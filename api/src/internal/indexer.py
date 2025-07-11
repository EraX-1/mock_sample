import base64
import json
import os
import re
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

from azure.search.documents.indexes.models import *
from langchain.text_splitter import MarkdownHeaderTextSplitter

from src.services.azure_ai_search import AzureAISearch
from src.services.azure_blob_storage import AzureBlobStorage
from src.services.azure_openai import AzureOpenAI
from src.utils.extract_markdown_text_from_file import (
    extract_markdown_text_from_docx,
    extract_markdown_text_from_excel,
    extract_markdown_text_from_html,
    extract_markdown_text_from_image,
    extract_markdown_text_from_pdf,
    extract_markdown_text_from_pptx,
)

japanese_separators = ["\n\n", "  \n", "。"]
embedding_deploy = os.environ["EMBEDDING_MODEL_NAME"]


# Semantic Chunking
def _semantic_chunk(contents: list):
    """テキストを指定したサイズで分割する"""
    print(f"🔍 _semantic_chunk: Processing {len(contents)} content items")

    chunks = []

    content_text = ""
    text_count_array = []
    for i, content in enumerate(contents):
        print(f"🔍 Content {i}: {content.keys()}")
        content_text += content["page_content"]
        text_count_array.append(len(content_text))

    print(f"🔍 Total content_text length: {len(content_text)}")
    print(f"🔍 Content preview: {content_text[:500]}...")

    # Split the document into chunks base on markdown headers.
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    text_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

    print(f"🔍 Using MarkdownHeaderTextSplitter with headers: {headers_to_split_on}")
    chunks = text_splitter.split_text(content_text)
    print(f"🔍 MarkdownHeaderTextSplitter result: {len(chunks)} chunks")

    chunks_with_page_number = []
    page_number = 1
    for chunk in chunks:
        keywords = ""
        if "Header 1" in chunk.metadata:
            keywords += chunk.metadata["Header 1"]
        if "Header 2" in chunk.metadata:
            keywords += " " + chunk.metadata["Header 2"]
        if "Header 3" in chunk.metadata:
            keywords += " " + chunk.metadata["Header 3"]

        current_page_number = page_number

        # 文字数が多すぎる場合は、分割する
        if len(chunk.page_content) > 512:
            splitted_chunks = []
            chunk_size = 512
            chunk_overlap = 100
            for i in range(0, len(chunk.page_content), chunk_size):
                start_index = i
                if i > 0:
                    start_index = i - chunk_overlap
                end_index = i + chunk_size
                if end_index > len(chunk.page_content):
                    end_index = len(chunk.page_content)
                splitted_chunks.append(chunk.page_content[start_index:end_index])

            for splitted_chunk in splitted_chunks:
                # テキストに埋め込まれたページ番号を取得する
                matches = re.findall(
                    r"<PAGE_NUMBER>(.*?)</PAGE_NUMBER>", splitted_chunk
                )
                if len(matches) > 0:
                    page_number = int(matches[-1]) + 1
                    splitted_chunk = re.sub(
                        r"<PAGE_NUMBER>(.*?)</PAGE_NUMBER>", "", splitted_chunk
                    )
                # デフォルトのページ番号もノイズとなるので削除する
                splitted_chunk = re.sub(
                    r"<!-- PageNumber=(.*?) -->", "", splitted_chunk
                )

                chunks_with_page_number.append(
                    {
                        "content": splitted_chunk,
                        "page_number": current_page_number,
                        "keywords": keywords,
                    }
                )
        else:
            # テキストに埋め込まれたページ番号を取得する
            matches = re.findall(
                r"<PAGE_NUMBER>(.*?)</PAGE_NUMBER>", chunk.page_content
            )
            if len(matches) > 0:
                page_number = int(matches[-1]) + 1
                chunk.page_content = re.sub(
                    r"<PAGE_NUMBER>(.*?)</PAGE_NUMBER>", "", chunk.page_content
                )
            # デフォルトのページ番号もノイズとなるので削除する
            chunk.page_content = re.sub(
                r"<!-- PageNumber=(.*?) -->", "", chunk.page_content
            )

            chunks_with_page_number.append(
                {
                    "content": chunk.page_content,
                    "page_number": current_page_number,
                    "keywords": keywords,
                }
            )

    print(f"🔍 Final result: {len(chunks_with_page_number)} chunks with page numbers")
    if chunks_with_page_number:
        print(f"🔍 Sample chunk: {chunks_with_page_number[0]}")

    return chunks_with_page_number


# Semantic Chunking From Excel
def _semantic_chunk_from_excel(contents: list):
    """テキストを指定したサイズで分割する"""
    # Split the document into chunks base on markdown headers.
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    text_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

    chunks_with_page_number = []

    for content in contents:
        chunks = []
        chunks = text_splitter.split_text(content["page_content"])

        for chunk in chunks:
            keywords = ""
            if "Header 1" in chunk.metadata:
                keywords += chunk.metadata["Header 1"]
            if "Header 2" in chunk.metadata:
                keywords += " " + chunk.metadata["Header 2"]
            if "Header 3" in chunk.metadata:
                keywords += " " + chunk.metadata["Header 3"]

        chunks_with_page_number.append(
            {
                "content": chunk.page_content,
                "page_number": content["metadata"]["page"],
                "keywords": keywords,
            }
        )

    return chunks_with_page_number


# インデックス処理をバッチ化
def _index_docs_to_azure_ai_search(
    chunks,
    source_file_name: str,
    index_type: str,
    actual_blob_name: str = None,
    batch_size=10,
):
    """ドキュメントをAzure AI Searchにインデックスし、データベースにも記録する"""
    index_name = AzureAISearch().get_index_name(index_type)
    search_client = AzureAISearch().init_search_client(index_name)
    open_ai_client = AzureOpenAI().init_client()

    def _embed_and_prepare_document(open_ai_client, chunk, source_file_name, i):
        try:
            response = open_ai_client.embeddings.create(
                input=chunk["content"], model=embedding_deploy
            )
            document = {
                "id": _encode_data(source_file_name + "_" + str(i)),
                "keywords": chunk["keywords"],
                "content": chunk["content"],
                "contentVector": response.data[0].embedding,
                "pageNumber": chunk["page_number"],
                "sourceFileName": source_file_name,
                "blobUrl": AzureBlobStorage().get_blob_url(source_file_name),
            }
            print(document)
            return document
        except Exception as e:
            raise Exception(f"Error embedding chunk {i}: {e}")

    batch = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i, chunk in enumerate(chunks):
            futures.append(
                executor.submit(
                    _embed_and_prepare_document,
                    open_ai_client,
                    chunk,
                    source_file_name,
                    i,
                )
            )
            if len(futures) >= batch_size:
                for future in as_completed(futures):
                    document = future.result()
                    batch.append(document)
                    del future
                search_client.upload_documents(documents=batch)
                batch.clear()
                futures.clear()
        # 残りのドキュメントをアップロード
        if futures:
            for future in as_completed(futures):
                document = future.result()
                batch.append(document)
                del future
            search_client.upload_documents(documents=batch)
            batch.clear()

    # インデックス処理が完了したらデータベースに記録
    # actual_blob_nameには実際にBlob Storageに保存されたファイル名（タイムスタンプ付き）が含まれる
    blob_name_to_save = actual_blob_name if actual_blob_name else source_file_name
    _save_indexed_file_to_database(blob_name_to_save, index_name, index_type)


def _save_indexed_file_to_database(
    original_blob_name: str, indexed_blob_name: str, index_type: str
):
    """インデックス済みファイル情報をデータベースに保存"""
    try:
        import os

        from src.schemas.index_schema import IndexedFileTable
        from src.services.db import get_session

        # ファイル拡張子から file_type を判定
        file_extension = os.path.splitext(original_blob_name)[1].lower()
        file_type_map = {
            ".pdf": "PDF",
            ".docx": "DOCX",
            ".doc": "DOC",
            ".pptx": "PPTX",
            ".xlsx": "EXCEL",
            ".xls": "EXCEL",
            ".xlsm": "EXCEL",
            ".html": "HTML",
            ".htm": "HTML",
            ".png": "IMAGE",
            ".jpg": "IMAGE",
            ".jpeg": "IMAGE",
        }
        file_type = file_type_map.get(file_extension, "UNKNOWN")

        with get_session() as session:
            # 既存レコードをチェック
            existing = (
                session.query(IndexedFileTable)
                .filter(IndexedFileTable.original_blob_name == original_blob_name)
                .first()
            )

            if existing:
                # 既存レコードを更新
                existing.indexed_blob_name = indexed_blob_name
                existing.index_type = index_type
                existing.file_type = file_type
                print(f"✅ Updated indexed file record: {original_blob_name}")
            else:
                # 新規レコードを作成
                indexed_file = IndexedFileTable(
                    original_blob_name=original_blob_name,
                    indexed_blob_name=indexed_blob_name,
                    file_type=file_type,
                    index_type=index_type,
                )
                session.add(indexed_file)
                print(f"✅ Created indexed file record: {original_blob_name}")

    except Exception as e:
        print(f"❌ Error saving indexed file to database: {str(e)}")
        # エラーが発生してもインデックス処理は成功とする


def _encode_data(data: str) -> str:
    return base64.urlsafe_b64encode(data.encode("utf-8")).decode("utf-8")


def _decode_data(encoded_data: str) -> str:
    return base64.urlsafe_b64decode(encoded_data).decode("utf-8")


async def index_pdf_docs(fileBytes: bytes, fileName: str, index_type: str):
    """PDF（.pdf）ドキュメントをインデックスする"""
    try:
        print(f"🔄 Starting PDF indexing for: {fileName}")

        # まずBlobにファイルをアップロード
        blob_storage = AzureBlobStorage()
        upload_result = await blob_storage.upload_document(
            fileBytes, fileName, "application/pdf"
        )
        print(f"✅ Blob uploaded: {upload_result}")

        # PDFからテキスト抽出
        print("🔄 Extracting text from PDF...")
        content = extract_markdown_text_from_pdf(fileBytes)
        print(f"📄 Extracted {len(content)} pages of content")
        if content:
            print(f"📝 Sample content: {content[0]['page_content'][:200]}...")

        # チャンク生成
        print("🔄 Creating semantic chunks...")
        chunks = _semantic_chunk(content)
        print(f"📦 Generated {len(chunks)} chunks")

        # AI Searchにインデックス
        if chunks:
            print("🔄 Indexing to AI Search...")
            _index_docs_to_azure_ai_search(
                chunks, fileName, index_type, upload_result["blob_name"]
            )
            print("✅ AI Search indexing completed")
        else:
            print("⚠️ No chunks generated, skipping AI Search indexing")

        return {
            "status": "success",
            "message": "PDFファイルのインデックス化が完了しました",
            "processed_chunks": len(chunks),
            "filename": fileName,
            "index_type": index_type,
            "blob_uploaded": True,
            "content_pages": len(content) if content else 0,
        }
    except Exception as e:
        print("❌ index_pdf_docs error:")
        print(traceback.format_exc())
        return {
            "status": "error",
            "message": f"PDFインデックス化中にエラーが発生しました: {str(e)}",
            "filename": fileName,
        }


async def index_docx_docs(fileBytes: bytes, fileName: str, index_type: str):
    """Word（.docx）ドキュメントをインデックスする"""
    try:
        print(f"🔄 Starting DOCX indexing for: {fileName}")

        # まずBlobにファイルをアップロード
        blob_storage = AzureBlobStorage()

        upload_result = await blob_storage.upload_document(
            fileBytes,
            fileName,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        print(f"✅ Blob uploaded: {upload_result}")

        # Wordからテキスト抽出
        print("🔄 Extracting text from DOCX...")
        content = extract_markdown_text_from_docx(fileBytes)
        print("📄 Extracted content from DOCX")

        # チャンク生成
        print("🔄 Creating semantic chunks...")
        chunks = _semantic_chunk(content)
        print(f"📦 Generated {len(chunks)} chunks")

        # AI Searchにインデックス
        if chunks:
            print("🔄 Indexing to AI Search...")
            _index_docs_to_azure_ai_search(
                chunks, fileName, index_type, upload_result["blob_name"]
            )
            print("✅ AI Search indexing completed")
        else:
            print("⚠️ No chunks generated, skipping AI Search indexing")

        return {
            "status": "success",
            "message": "Wordファイルのインデックス化が完了しました",
            "processed_chunks": len(chunks),
            "filename": fileName,
            "index_type": index_type,
            "blob_uploaded": True,
        }
    except Exception as e:
        print("❌ index_docx_docs error:")
        import traceback

        print(traceback.format_exc())
        return {
            "status": "error",
            "message": f"Wordインデックス化中にエラーが発生しました: {str(e)}",
            "filename": fileName,
        }


async def index_pptx_docs(fileBytes: bytes, fileName: str, index_type: str):
    """Power Point（.pptx）ドキュメントをインデックスする"""
    try:
        print(f"🔄 Starting PPTX indexing for: {fileName}")

        # まずBlobにファイルをアップロード
        blob_storage = AzureBlobStorage()

        upload_result = await blob_storage.upload_document(
            fileBytes,
            fileName,
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
        print(f"✅ Blob uploaded: {upload_result}")

        # PowerPointからテキスト抽出
        print("🔄 Extracting text from PPTX...")
        content = extract_markdown_text_from_pptx(fileBytes)
        print("📄 Extracted content from PPTX")

        # チャンク生成
        print("🔄 Creating semantic chunks...")
        chunks = _semantic_chunk(content)
        print(f"📦 Generated {len(chunks)} chunks")

        # AI Searchにインデックス
        if chunks:
            print("🔄 Indexing to AI Search...")
            _index_docs_to_azure_ai_search(
                chunks, fileName, index_type, upload_result["blob_name"]
            )
            print("✅ AI Search indexing completed")
        else:
            print("⚠️ No chunks generated, skipping AI Search indexing")

        return {
            "status": "success",
            "message": "PowerPointファイルのインデックス化が完了しました",
            "processed_chunks": len(chunks),
            "filename": fileName,
            "index_type": index_type,
            "blob_uploaded": True,
        }
    except Exception as e:
        print("❌ index_pptx_docs error:")
        import traceback

        print(traceback.format_exc())
        return {
            "status": "error",
            "message": f"PowerPointインデックス化中にエラーが発生しました: {str(e)}",
            "filename": fileName,
        }


async def index_html_docs(fileBytes: bytes, fileName: str, index_type: str):
    """HTML（.html）ドキュメントをインデックスする"""
    try:
        print(f"🔄 Starting HTML indexing for: {fileName}")

        # まずBlobにファイルをアップロード
        blob_storage = AzureBlobStorage()

        upload_result = await blob_storage.upload_document(
            fileBytes, fileName, "text/html"
        )
        print(f"✅ Blob uploaded: {upload_result}")

        # HTMLからテキスト抽出
        print("🔄 Extracting text from HTML...")
        content = extract_markdown_text_from_html(fileBytes)
        print("📄 Extracted content from HTML")

        # チャンク生成
        print("🔄 Creating semantic chunks...")
        chunks = _semantic_chunk(content)
        print(f"📦 Generated {len(chunks)} chunks")

        # AI Searchにインデックス
        if chunks:
            print("🔄 Indexing to AI Search...")
            _index_docs_to_azure_ai_search(
                chunks, fileName, index_type, upload_result["blob_name"]
            )
            print("✅ AI Search indexing completed")
        else:
            print("⚠️ No chunks generated, skipping AI Search indexing")

        return {
            "status": "success",
            "message": "HTMLファイルのインデックス化が完了しました",
            "processed_chunks": len(chunks),
            "filename": fileName,
            "index_type": index_type,
            "blob_uploaded": True,
        }
    except Exception as e:
        print("❌ index_html_docs error:")
        import traceback

        print(traceback.format_exc())
        return {
            "status": "error",
            "message": f"HTMLインデックス化中にエラーが発生しました: {str(e)}",
            "filename": fileName,
        }


async def index_image_docs(fileBytes: bytes, fileName: str, index_type: str):
    """画像（.png, .jpg, .jpeg）ドキュメントをインデックスする"""
    try:
        print(f"🔄 Starting image indexing for: {fileName}")

        # まずBlobにファイルをアップロード
        blob_storage = AzureBlobStorage()

        file_extension = os.path.splitext(fileName)[1].lower()
        content_type = "image/png" if file_extension == ".png" else "image/jpeg"

        upload_result = await blob_storage.upload_document(
            fileBytes, fileName, content_type
        )
        print(f"✅ Blob uploaded: {upload_result}")

        # 画像からテキスト抽出
        print("🔄 Extracting text from image...")
        content = extract_markdown_text_from_image(fileBytes)
        print("📄 Extracted content from image")

        # チャンク生成
        print("🔄 Creating semantic chunks...")
        chunks = _semantic_chunk(content)
        print(f"📦 Generated {len(chunks)} chunks")

        # AI Searchにインデックス
        if chunks:
            print("🔄 Indexing to AI Search...")
            _index_docs_to_azure_ai_search(
                chunks, fileName, index_type, upload_result["blob_name"]
            )
            print("✅ AI Search indexing completed")
        else:
            print("⚠️ No chunks generated, skipping AI Search indexing")

        return {
            "status": "success",
            "message": "画像ファイルのインデックス化が完了しました",
            "processed_chunks": len(chunks),
            "filename": fileName,
            "index_type": index_type,
            "blob_uploaded": True,
        }
    except Exception as e:
        print("❌ index_image_docs error:")
        import traceback

        print(traceback.format_exc())
        return {
            "status": "error",
            "message": f"画像インデックス化中にエラーが発生しました: {str(e)}",
            "filename": fileName,
        }


async def index_excel_docs(fileBytes: bytes, fileName: str, index_type: str):
    """Excel（.xlsx, .xls, .xlsm）ドキュメントをインデックスする"""
    try:
        print(f"🔄 Starting Excel indexing for: {fileName}")

        # まずBlobにファイルをアップロード
        blob_storage = AzureBlobStorage()

        upload_result = await blob_storage.upload_document(
            fileBytes,
            fileName,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        print(f"✅ Blob uploaded: {upload_result}")

        # Excelからテキスト抽出
        print("🔄 Extracting text from Excel...")
        content = extract_markdown_text_from_excel(fileBytes)
        print("📄 Extracted content from Excel")

        # チャンク生成
        print("🔄 Creating semantic chunks...")
        chunks = _semantic_chunk(content)
        print(f"📦 Generated {len(chunks)} chunks")

        # AI Searchにインデックス
        if chunks:
            print("🔄 Indexing to AI Search...")
            _index_docs_to_azure_ai_search(
                chunks, fileName, index_type, upload_result["blob_name"]
            )
            print("✅ AI Search indexing completed")
        else:
            print("⚠️ No chunks generated, skipping AI Search indexing")

        return {
            "status": "success",
            "message": "Excelファイルのインデックス化が完了しました",
            "processed_chunks": len(chunks),
            "filename": fileName,
            "index_type": index_type,
            "blob_uploaded": True,
        }
    except Exception as e:
        print("❌ index_excel_docs error:")
        import traceback

        print(traceback.format_exc())
        return {
            "status": "error",
            "message": f"Excelインデックス化中にエラーが発生しました: {str(e)}",
            "filename": fileName,
        }


def index_videostep_docs(fileBytes: bytes, fileName: str, index_type: str):
    """動画マニュアルデータ（.json）をインデックスする。1ファイルすべてをtxtとして扱う"""
    print(1)
    try:
        json_content = json.loads(fileBytes.decode("utf-8"))
    except Exception:
        print("json.load error:")
        print(traceback.format_exc())
        raise Exception("json.load error:")
    print(2)

    try:
        # JSONデータを_semantic_chunkが期待する形式に変換
        # JSONデータを文字列に変換し、それをpage_contentとして持つ辞書を作成
        content = [{"page_content": json.dumps(json_content, ensure_ascii=False)}]
        chunks = _semantic_chunk(content)
    except Exception:
        print("_semantic_chunk error:")
        print(traceback.format_exc())
        raise Exception("_semantic_chunk error:")

    print(chunks)
    print(fileName)
    print(index_type)
    _index_docs_to_azure_ai_search(chunks, fileName, index_type)

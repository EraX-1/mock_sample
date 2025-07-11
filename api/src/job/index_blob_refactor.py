import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
from pydantic import BaseModel
from InquirerPy import prompt

from src.services.azure_ai_search import AzureAISearch
from src.services.azure_blob_storage import AzureBlobStorage
from src.internal.indexer import (
    index_pdf_docs,
    index_docx_docs,
    index_pptx_docs,
    index_html_docs,
    index_excel_docs,
    index_image_docs
)
from src.models import File
from src.repositories import FileRepository
from src.utils.convert_doc_to_docx import convert_doc_bytes_to_docx_bytes


class Blob(BaseModel):
    name: str


def _index_file(index: int, file: Blob, total_files: int, index_type: str) -> dict:
    print(f"インデックス開始: {file.name} ({index + 1}/{total_files})")

    try:
        container_client = AzureBlobStorage().init_container_client()
        blob_client = container_client.get_blob_client(file.name)
        stream = blob_client.download_blob()
        file_bytes = stream.readall()

        if file.name.lower().endswith(('.xlsx', '.xls', '.xlsm')):
            index_excel_docs(file_bytes, file.name, index_type)
        elif file.name.lower().endswith('.pdf'):
            index_pdf_docs(file_bytes, file.name, index_type)
        elif file.name.lower().endswith(('.docx', '.doc')):
            if file.name.lower().endswith('.doc'):
                file_bytes = convert_doc_bytes_to_docx_bytes(file_bytes)
            index_docx_docs(file_bytes, file.name, index_type)
        elif file.name.lower().endswith(('.pptx', '.ppt')):
            index_pptx_docs(file_bytes, file.name, index_type)
        elif file.name.lower().endswith('.html'):
            index_html_docs(file_bytes, file.name, index_type)
        elif file.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            index_image_docs(file_bytes, file.name, index_type)
        else:
            raise ValueError("サポートしていないファイル形式です")

        print(f"インデックス完了: {file.name} ({index + 1}/{total_files})")

        return {
            "file_name": file.name,
            "success": True,
        }

    except Exception as e:
        print(f"インデックスエラー: {file.name} ({index + 1}/{total_files})")
        print(f"エラー詳細: {e}")

        return {
            "file_name": file.name,
            "success": False,
        }


def _index_file_wrapper(args):
    return _index_file(*args)


def get_blob_list(blob_folder_name: str) -> list[Blob]:
    container_client = AzureBlobStorage().init_container_client()
    blob_list = container_client.list_blobs(name_starts_with=blob_folder_name)
    return [Blob(name=blob.name) for blob in blob_list]


def get_blob_list_by_folder_names(blob_folder_names: list[str]) -> list[Blob]:
    container_client = AzureBlobStorage().init_container_client()
    blob_list = []
    for blob_folder_name in blob_folder_names:
        blob_list.extend(container_client.list_blobs(name_starts_with=blob_folder_name))
    return [Blob(name=blob.name) for blob in blob_list]


def insert_blob_into_db(blob_list: list[Blob]) -> list[File]:
    file_repository = FileRepository()
    return [file_repository.insert_one({"blob_name": blob.name, "blob_url": AzureBlobStorage().get_blob_url(blob.name)}) for blob in blob_list]


def index_files(files: list[Blob], index_type: str, retry: bool = False):
    print("既にインデックス済みのファイルを取り除く")
    index_name = AzureAISearch().get_index_name(index_type)
    search_client = AzureAISearch().init_search_client(index_name)
    results = search_client.search("*")

    indexed_file_names = []
    def _append_indexed_file_name(result):
        if result["sourceFileName"] not in indexed_file_names:
            indexed_file_names.append(result["sourceFileName"])

    with ThreadPoolExecutor(max_workers=20) as executor:
        [executor.submit(_append_indexed_file_name, result) for result in results]

    target_files = []
    for file in files:
        if file.name not in indexed_file_names:
            target_files.append(file)

    total_files = len(target_files)

    print(f"インデックス対象のファイル数: {total_files}")

    results = []
    if retry:
        for index, file in enumerate(target_files):
            results.append(_index_file(index, file, total_files, index_type))
    else:
        cpu_count = os.cpu_count()
        processes = cpu_count * 2 if cpu_count else 8
        args_list = [(index, file, total_files, index_type) for index, file in enumerate(target_files)]

        with Pool(processes=processes) as pool:
            results = pool.map(_index_file_wrapper, args_list)

    failed_files = []
    for result in results:
        if not result["success"]:
            file_name = result["file_name"]
            failed_files.append(file_name)

    if len(failed_files) == 0:
        return []

    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_name = f"{current_time}_{index_type}"
    if retry:
        log_file_name += "_retry"
    log_file = os.path.join("./job/logs/", f"{log_file_name}.txt")
    with open(log_file, "w") as f:
        for file_name in failed_files:
            f.write(f"{file_name}\n")

    return failed_files


def prompt_user_input():
    try:
        INDEX_FILE_PATH = os.getenv("INDEX_FILE_PATH")
        INDEX_TYPE = os.getenv("INDEX_TYPE")

        questions = [
            {
                "type": "input",
                "name": "blob_folder_name",
                "message": "Blobコンテナのフォルダ名を入力してください:",
                "default": INDEX_FILE_PATH if INDEX_FILE_PATH else "tmp",
            },
            {
                "type": "list",
                "name": "index_type",
                "message": "インデックスの種類を指定してください:",
                "choices": AzureAISearch().get_index_types(),
                "default": INDEX_TYPE if INDEX_TYPE else "NKJG",
            },
        ]

        answers = prompt(questions)
        return answers["blob_folder_name"], answers["index_type"]

    except Exception as e:
        print("対話形式のUIでエラーが発生しました。")
        print(f"エラー詳細: {e}")
        raise


def main(blob_folder_name: str = None, index_type: str = None):
    if not blob_folder_name or not index_type:
        blob_folder_name, index_type = prompt_user_input()

    blob_list = get_blob_list(blob_folder_name)
    failed_files = index_files(blob_list, index_type)
    if failed_files:
        blob_list = get_blob_list_by_folder_names(failed_files)
        index_files(blob_list, index_type, retry=True)


if __name__ == "__main__":
    main()
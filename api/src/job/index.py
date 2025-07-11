import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

from InquirerPy import prompt
from InquirerPy.validator import PathValidator

from src.internal.indexer import (
    index_docx_docs,
    index_excel_docs,
    index_html_docs,
    index_image_docs,
    index_pdf_docs,
    index_pptx_docs,
    index_videostep_docs,
)
from src.services.azure_ai_search import INDEX_TYPES


async def async_index_files(file_type: str, path: str, index_type: str):
    def index_file(i_filename):
        i, filename = i_filename
        print(f"{i + 1}個目: {filename}\n")
        file_path = os.path.join(path, filename)
        if os.path.isfile(file_path):  # ファイルかどうかをチェック
            with open(file_path, "rb") as file:  # バイナリモードでファイルを開く
                file_bytes = file.read()  # ファイル全体をバイトデータとして読み込む

                if file_type == "excel":
                    index_excel_docs(file_bytes, filename, index_type)
                elif file_type == "pdf":
                    index_pdf_docs(file_bytes, filename, index_type)
                elif file_type == "word":
                    index_docx_docs(file_bytes, filename, index_type)
                elif file_type == "html":
                    index_html_docs(file_bytes, filename, index_type)
                elif file_type == "powerpoint":
                    index_pptx_docs(file_bytes, filename, index_type)
                elif file_type == "image":
                    index_image_docs(file_bytes, filename, index_type)
                elif file_type == "videostep":
                    print("実行")
                    index_videostep_docs(file_bytes, filename, index_type)
                else:
                    raise ValueError("サポートしていないファイル形式です")

    def index_directory():
        with ThreadPoolExecutor(max_workers=5) as executor:
            [
                executor.submit(index_file, (i, filename))
                for i, filename in enumerate(os.listdir(path))
            ]

    def index_single_file():
        filename = os.path.basename(path)
        file_path = os.path.abspath(path)
        index_file((0, filename))

    # 入力がディレクトリかファイルかを判断
    if os.path.isdir(path):
        index_directory()
    elif os.path.isfile(path):
        index_single_file()
    else:
        print("無効なパスです。ファイルまたはディレクトリを指定してください。")

    return {"message": "start"}


def prompt_user_input():
    try:
        # 対話形式の UI を構築
        INDEX_FILE_TYPE = os.getenv("INDEX_FILE_TYPE")
        INDEX_FILE_PATH = os.getenv("INDEX_FILE_PATH")
        INDEX_TYPE = os.getenv("INDEX_TYPE")

        # 対話形式の質問を定義
        questions = [
            {
                "type": "list",
                "name": "file_type",
                "message": "インデックス作成するファイルタイプを選択してください:",
                "choices": [
                    "excel",
                    "pdf",
                    "word",
                    "html",
                    "powerpoint",
                    "image",
                    "videostep",
                ],
                "default": INDEX_FILE_TYPE if INDEX_FILE_TYPE else "excel",
            },
            {
                "type": "input",
                "name": "path",
                "message": "インデックス作成するファイルまたはディレクトリのパスを入力してください:",
                "validate": PathValidator(
                    is_file=False, is_dir=True, message="有効なパスを入力してください。"
                ),
                "default": INDEX_FILE_PATH if INDEX_FILE_PATH else "tmp",
            },
            {
                "type": "list",
                "name": "index_type",
                "message": "インデックスの種類を指定してください:",
                "choices": INDEX_TYPES,
                "default": INDEX_TYPE if INDEX_TYPE else "NKJG",
            },
        ]

        # プロンプトを表示
        answers = prompt(questions)
        return answers["file_type"], answers["path"], answers["index_type"]

    except ZeroDivisionError:
        print("ターミナルの幅が取得できないため、対話形式のUIを使用できません。")
        print("環境変数 COLUMNS と LINES を適切に設定するか、CLI 引数を使用してください。")
        raise
    except Exception as e:
        print("対話形式のUIでエラーが発生しました。")
        print(f"エラー詳細: {e}")
        raise


def main():
    try:
        file_type, path, index_type = prompt_user_input()

        asyncio.run(async_index_files(file_type, path, index_type))

    except Exception as e:
        print("エラーが発生しました。処理を終了します。")
        print(f"エラー詳細: {e}")


if __name__ == "__main__":
    main()

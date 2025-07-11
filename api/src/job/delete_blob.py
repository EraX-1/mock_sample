from InquirerPy import prompt
from pydantic import BaseModel

from src.services.azure_blob_storage import AzureBlobStorage


class Blob(BaseModel):
    name: str


def get_blob_list(blob_folder_name: str) -> list[Blob]:
    container_client = AzureBlobStorage().init_container_client()
    blob_list = container_client.list_blobs(name_starts_with=blob_folder_name)
    return [Blob(name=blob.name) for blob in blob_list]


def delete_blob(blobs: list[Blob]):
    container_client = AzureBlobStorage().init_container_client()
    for blob in blobs:
        container_client.delete_blob(blob.name)


def prompt_user_input():
    try:
        # 対話形式の質問を定義
        questions = [
            {
                "type": "input",
                "name": "blob_folder_name",
                "message": "Blobコンテナのフォルダ名を入力してください:",
            },
        ]

        # プロンプトを表示
        answers = prompt(questions)
        return answers["blob_folder_name"]

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
        blob_folder_name = prompt_user_input()

        blob_list = get_blob_list(blob_folder_name)
        delete_blob(blob_list)

    except Exception as e:
        print("エラーが発生しました。処理を終了します。")
        print(f"エラー詳細: {e}")


if __name__ == "__main__":
    main()

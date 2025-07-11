import os

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient


def rename_source_file_names(index_name, search_endpoint, api_key):
    """
    Azure AI Searchの特定インデックスのsourceFileNameカラムの値を変更する関数
    SampleForIndex20250122から始まる値をDataforIndexに置き換えます
    """
    # 認証情報の設定
    credential = AzureKeyCredential(api_key)

    # SearchClientの初期化
    client = SearchClient(
        endpoint=search_endpoint, index_name=index_name, credential=credential
    )

    # 全件取得
    results = client.search(
        search_text="*",
        select=["id", "sourceFileName"],
        top=1000,  # 必要に応じて調整してください
    )

    # 更新するドキュメントのリスト
    actions = []

    # 検索結果を処理
    for result in results:
        doc_id = result["id"]
        old_name = result["sourceFileName"]

        # SampleForIndex20250122で始まる場合のみ処理
        if old_name and old_name.startswith("SampleForIndex20250122"):
            # 新しい名前を作成（置換処理）
            new_name = old_name.replace("SampleForIndex20250122", "DataforIndex")

            # 更新用のドキュメントを作成
            actions.append(
                {
                    "@search.action": "mergeOrUpload",
                    "id": doc_id,
                    "sourceFileName": new_name,
                }
            )

    # バッチ更新を実行
    if actions:
        result = client.upload_documents(documents=actions)
        print(f"{len(actions)}件のドキュメントを更新しました")
        return result
    else:
        print("更新対象のドキュメントが見つかりませんでした")
        return None


if __name__ == "__main__":
    # 環境変数から設定を読み込む
    index_name = os.environ.get(
        "AZURE_SEARCH_INDEX_NAME", "e982c376-792c-4013-a788-bb049e34e9ad"
    )
    search_endpoint = os.environ.get(
        "AZURE_SEARCH_ENDPOINT",
        "https://srch-kdk-knoledgedb-dev-cus-001.search.windows.net",
    )
    api_key = os.environ.get("AZURE_SEARCH_API_KEY")

    # 関数を実行
    rename_source_file_names(index_name, search_endpoint, api_key)

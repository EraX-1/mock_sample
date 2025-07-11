from azure.search.documents.indexes.models import *
from InquirerPy import prompt

from src.services.azure_ai_search import AzureAISearch


def create_index(index_name: str):
    """Azure AI Searchのインデックスを作成する"""
    client = AzureAISearch().init_search_index_client()
    # すでにインデックスが作成済みである場合には何もしない
    if index_name in client.list_index_names():
        print("すでにインデックスが作成済みです")
        return

    # インデックスのフィールドを定義する
    # id: ドキュメントを一意に識別するためのフィールド
    # content: ドキュメントの内容を格納するためのフィールド
    # contentVector: ドキュメントの内容をベクトル化した結果を格納するためのフィールド
    # sourceFileName: ドキュメントのファイル名を格納するためのフィールド
    # pageNumber: ドキュメントのページ番号を格納するためのフィールド
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SimpleField(name="keywords", type="Edm.String", analyzer_name="ja.microsoft"),
        SearchableField(
            name="content", type="Edm.String", analyzer_name="ja.microsoft"
        ),
        SearchField(
            name="contentVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="myHnswProfile",
        ),
        SimpleField(name="sourceFileName", type=SearchFieldDataType.String),
        SimpleField(name="pageNumber", type=SearchFieldDataType.Int32),
        SimpleField(name="blobUrl", type=SearchFieldDataType.String),
    ]
    # セマンティック検索のための定義を行う
    semantic_settings = SemanticSearch(
        configurations=[
            SemanticConfiguration(
                name="default",
                prioritized_fields=SemanticPrioritizedFields(
                    title_field=None,
                    content_fields=[SemanticField(field_name="content")],
                ),
            )
        ]
    )
    # ベクトル検索のための定義を行う
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="myHnsw")],
        profiles=[
            VectorSearchProfile(
                name="myHnswProfile",
                algorithm_configuration_name="myHnsw",
            )
        ],
    )
    # インデックスを作成する
    index = SearchIndex(
        name=index_name,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_settings,
    )
    client.create_index(index)


def prompt_user_input():
    try:
        # 対話形式の質問を定義
        questions = [
            {
                "type": "input",
                "name": "index_name",
                "message": "インデックス名を入力してください:",
                "default": "tmp",
            },
        ]

        # プロンプトを表示
        answers = prompt(questions)
        return answers["index_name"]

    except ZeroDivisionError:
        print("ターミナルの幅が取得できないため、対話形式のUIを使用できません。")
        print("環境変数 COLUMNS と LINES を適切に設定するか、CLI 引数を使用してください。")
        raise
    except Exception as e:
        print("対話形式のUIでエラーが発生しました。")
        print(f"エラー詳細: {e}")
        raise


def main():
    index_name = prompt_user_input()
    create_index(index_name)


if __name__ == "__main__":
    main()

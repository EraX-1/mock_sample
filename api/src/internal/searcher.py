import json
import os
from typing import Any

import tiktoken
import toml
from azure.search.documents.indexes.models import *
from azure.search.documents.models import VectorizedQuery
from pydantic import BaseModel

from src.services.azure_ai_search import AzureAISearch
from src.services.azure_openai import AzureOpenAI

CONFIG_PATH = "/app/config.toml"
CONFIG = toml.load(CONFIG_PATH)
PROMPT_CONFIG = CONFIG.get("prompt", {})
SYSTEM_PROMPT = PROMPT_CONFIG.get("SYSTEM_PROMPT", "")
HYPOTHETICAL_ANSWER_PROMPT = PROMPT_CONFIG.get("HYPOTHETICAL_ANSWER_PROMPT", "")


class ChatHistoryItem(BaseModel):
    type: str
    content: str


embedding_deploy = os.environ["EMBEDDING_MODEL_NAME"]
gpt_deploy = os.environ["SEARCH_MODEL_NAME"]


# AIのキャラクターを決めるためのシステムメッセージを定義する。
system_message_chat_conversation = """
{system_prompt}

# 条件
・マークダウン形式で回答してください。積極的に箇条書きにするなど、わかりやすい回答を心掛けてください。
・回答については、「Sources:」以下に記載されているテキスト情報に基づいて回答してください。情報が複数ある場合は「Sources:」のあとに[Source1]、[Source2]、[Source3]のように記載されますので、それに基づいて回答してください。
・回答に際して、文ごとにその文の最後の終わりに、<source-doc:<<blobUrl>>(p.ページ番号)---<<sourceFileName>>>を追記してください。ファイル名、ページ番号は各[Source]の文末に存在している、[Reference]の中に入っているファイル名、ページ番号を使用してください。「「「「Referenceを使用してください。カッコなどの記号を含めて必ず原文のまま使用してください。ファイル名は省略しないでください。ファイル名に空白が含まれている場合はそれも出力しなさい。」」」」
・sourceFileNameとblobUrlはドキュメント検索結果の内容をそのまま使用してください。
・ユーザーの質問に対して、「Sources:」以下に記載されている内容に基づいて適切な回答ができない場合は、「すみません。わかりません。」と回答して、どのような追加情報があれば回答できるかをユーザーに伝えてください。
・以下に「# 追加の指示」がある場合は、「# 条件」や「# 制約」や「# 回答例」よりも優先的に従って回答してください。

# 制約
・「Sources:」以下に記載されている情報以外の回答はしないでください。
・回答の中に[Source]や[Reference]という文言は入れないでください。
・videostepの情報は後述のvideostepタグを使用して回答の中に挿入してください。

# 回答例
「構成には居住区域を考慮する必要があります。<source-doc:https://〇〇.pdf(p.1)---△△.pdf>さらに、生産を使用する目的は、安全性を確保しながら設計することが求められます。<source-doc:〇〇.pdf(p.2)---△△.pdf>」

{custom_prompt}

{videostep_custom_prompt}
"""

# ユーザからの質問を元に、Azure AI Searchに投げる検索クエリを生成するためのテンプレートを定義する。
query_prompt_template = """
これまでの会話履歴と、以下のユーザーからの質問に基づいて、検索クエリを生成してください。
回答には検索クエリ以外のものを含めないでください。
たとえば、「育児休暇はどういうものですか？」という質問に対して、「育児休暇とは」と検索クエリのみを生成してください。

# ユーザーからの質問
{query}
"""


def semantic_hybrid_search(
    query: str,
    index_type_list: list[str],
    custom_prompt: str = "",
    is_active_custom_prompt: bool = False,
    model: str = gpt_deploy,
    history: list[ChatHistoryItem] = [],
    from_job=False,
):
    """セマンティックサーチとハイブリッドサーチを組み合わせて回答を生成する。"""
    # Azure OpenAIのAPIに接続するためのクライアントを生成する
    production_client = AzureOpenAI()
    openai_client = production_client.init_client()

    # Hypothetical Answer
    user_message_for_hypothetical_answer = f"""
{HYPOTHETICAL_ANSWER_PROMPT}


回答する際は、参考にした情報源を該当する文言の後に載せてください。

# 制約
・簡潔に400文字以内で答えてください。
・改行などは含まずに、文章で回答してください。

# 質問
{query}
"""

    # 会話履歴の最後に、キーワード検索用クエリを生成するためのプロンプトを追加する。
    chat_histories = []
    for h in history:
        if h.type == "user":
            chat_histories.append({"role": "user", "content": h.content})
        elif h.type == "assistant":
            chat_histories.append({"role": "assistant", "content": h.content})
    # try:
    hypothetical_answer = (
        openai_client.chat.completions.create(
            model=gpt_deploy,
            messages=[
                *chat_histories,
                {"role": "system", "content": "あなたは、AIのアシスタントです。"},
                {
                    "role": "user",
                    "content": user_message_for_hypothetical_answer.format(),
                },
            ],
        )
        .choices[0]
        .message.content
    )
    # except:
    #     raise RuntimeError("検索クエリ生成においてエラーが発生しました")

    # Azure OpenAI Serviceの埋め込み用APIを用いて、ユーザーからの質問をベクトル化する。
    # セマンティックハイブリッド検索に必要な「ベクトル化されたクエリ」「キーワード検索用クエリ」のうち、ベクトル化されたクエリを生成する。
    try:
        response = openai_client.embeddings.create(
            input=hypothetical_answer, model=embedding_deploy
        )
        vector_query = VectorizedQuery(
            vector=response.data[0].embedding,
            k_nearest_neighbors=3,
            fields="contentVector",
        )
    except:
        raise RuntimeError("埋め込み取得においてエラーが発生しました")

    # ユーザーからの質問を元に、Azure AI Searchに投げる検索クエリを生成する。
    # セマンティックハイブリッド検索に必要な「ベクトル化されたクエリ」「キーワード検索用クエリ」のうち、検索クエリを生成する。
    messages_for_search_query = [*chat_histories]

    messages_for_search_query.append(
        {"role": "user", "content": query_prompt_template.format(query=query)}
    )
    messages_for_search_query = _trim_messages(messages_for_search_query)

    response = openai_client.chat.completions.create(
        model=gpt_deploy, messages=messages_for_search_query
    )
    search_query = response.choices[0].message.content

    # 「ベクトル化されたクエリ」「キーワード検索用クエリ」を用いて、Azure AI Searchに対してセマンティックハイブリッド検索を行う。
    results = []
    source_prompt = ""
    # index_typeからAzure AI Searchの実際のインデックス名へのマッピング
    # 現在はすべて同じインデックスを使用
    index_mapping = {
        "01INDEX01TYPE001001001001": "yuyama-documents-index",
        "01INDEX02TYPE001001001001": "yuyama-documents-index",
        "01INDEX03TYPE001001001001": "yuyama-documents-index",
        "documents": "yuyama-documents-index",  # フォールバック用
    }

    try:
        for index_type in index_type_list:
            # マッピングを使用してAzureの正しいインデックス名を取得
            index_name = index_mapping.get(index_type, "yuyama-documents-index")
            print(f"Using Azure index: {index_name} for index_type: {index_type}")
            search_client = AzureAISearch().init_search_client(index_name)
            _results = search_client.search(
                query_type="semantic",
                semantic_configuration_name="default",
                search_text=search_query,
                vector_queries=[vector_query],
                select=[
                    "id",
                    "keywords",
                    "content",
                    "sourceFileName",
                    "pageNumber",
                    "blobUrl",
                ],
                query_caption="extractive",
                query_answer="extractive",
                highlight_pre_tag="<em>",
                highlight_post_tag="</em>",
                top=20,
            )
            for result in _results:
                results.append(result)
            source_prompt += _get_source_prompt(results)
    except Exception as e:
        # エラーの詳細情報をログに記録
        print(f"ドキュメント検索エラー: {str(e)}")
        # インデックス名とクエリ情報を含めたエラーメッセージ
        error_message = "ドキュメント検索においてエラーが発生しました。"
        raise RuntimeError(error_message)

    messages_for_semantic_answer = [*chat_histories]
    videostep_custom_prompt = ""
    if "3d401888-1c0b-0ef4-3e46-941a799d635e" in index_type_list:
        videostep_custom_prompt = """
# videostepタグの指示
・videostepの情報はJSON形式で渡されます。
・JSONのフォーマットは以下の通りです。
{
    "title": "動画タイトル",
    "description": "動画の説明",
    "url": "動画のURL"
    "tags": [],
    "keyword": [],
    "created_at": "",
    "updated_at": ""
}
・検索結果にvideostepの情報が含まれる場合は、必ず以下のフォーマットに従って回答の中に挿入してください：
  <videostep title="動画タイトル" desc="動画の説明" url="動画のURL">
・フロントエンドでは上記タグが自動でコンテンツに置き換わるので、回答中に動画の情報を入れる必要はありません。
・動画情報は、関連する説明の直後に配置してください。
・動画情報が複数ある場合は、それぞれの動画を適切な位置に配置してください。

# videostepタグを含んだ回答例
「構成には居住区域を考慮する必要があります。<source-doc:https://〇〇.pdf(p.1)---△△.pdf>さらに、生産を使用する目的は、安全性を確保しながら設計することが求められます。<source-doc:〇〇.pdf(p.2)---△△.pdf><videostep title="〇〇" desc="〇〇" url="https://example.com/video1">」

この手順については、以下の動画で詳しく説明されています：
<videostep title="安全な設計の基本" desc="居住区域と生産性を考慮した設計方法の解説" url="https://example.com/video1">」

#　必ずvideostepタグを含んだ回答を生成してください。
videostep_test_index_xxxx.jsonというファイル名のファイルが存在する場合、必ずvideostepタグを使用してください。
"""

    if len(custom_prompt) > 0 and is_active_custom_prompt:
        custom_prompt = "# 追加の指示\n" + custom_prompt
    messages_for_semantic_answer.append(
        {
            "role": "system",
            "content": system_message_chat_conversation.format(
                system_prompt=SYSTEM_PROMPT,
                custom_prompt=custom_prompt,
                videostep_custom_prompt=videostep_custom_prompt,
            ),
        }
    )

    source_file_names_text_list = []
    reference_docs = []
    for result in results:
        reference_docs.append(
            {
                "id": result["id"],
                "content": result["content"],
                "sourceFileName": result["sourceFileName"],
                "pageNumber": result["pageNumber"],
            }
        )
        source_file_names_text_list.append(
            (
                result["sourceFileName"] + "(p." + str(result["pageNumber"]) + ")",
                result["blobUrl"],
            )
        )
    # source_file_names_text_list内の重複排除
    source_file_names_text_list = list(set(source_file_names_text_list))
    user_message = f"""
# ユーザーの質問
{query}

# 回答生成のための情報源
Sources:
{source_prompt}
"""

    messages_for_semantic_answer.append({"role": "user", "content": user_message})

    messages_for_semantic_answer = _trim_messages(messages_for_semantic_answer)
    if "3d401888-1c0b-0ef4-3e46-941a799d635e" in index_type_list:
        messages_for_semantic_answer.append(
            {"role": "user", "content": "videostepを使用してください"}
        )

    if from_job:
        response = openai_client.chat.completions.create(
            model=model,
            messages=messages_for_semantic_answer,
            temperature=0,
        )
        return {
            "query": search_query,
            "reference_docs": reference_docs,
            "generated": response.choices[0].message.content,
        }
    # jobからの実行の場合これ以降は実行されない

    # Azure OpenAI Serviceに回答生成を依頼する（本番環境対応版）
    try:
        response = production_client.create_chat_completion(
            messages=messages_for_semantic_answer,
            model=model,
            temperature=0,
            stream=True,
            max_tokens=2000,
        )
    except Exception as e:
        production_client.logger.error(
            f"回答生成においてエラーが発生しました: {str(e)}"
        )
        raise RuntimeError(f"回答生成においてエラーが発生しました: {str(e)}")

    accumulated_text = []
    end_flag = False
    token_usage = None  # トークン使用量を保存する変数を追加

    def stream_generator():
        nonlocal end_flag, token_usage
        for chunk in response:
            if end_flag:
                if not token_usage:
                    token_usage = {
                        "completion_tokens": chunk.usage.completion_tokens,
                        "prompt_tokens": chunk.usage.prompt_tokens,
                        "total_tokens": chunk.usage.total_tokens,
                    }
                    token_info_json = json.dumps(token_usage)
                    yield f"\n<<TOKEN_INFO>>{token_info_json}<<TOKEN_INFO_END>>\n"
            else:
                if chunk.choices and len(chunk.choices) > 0:
                    delta_content = getattr(chunk.choices[0].delta, "content", "")
                    if delta_content:
                        accumulated_text.append(delta_content)
                        yield delta_content
                    elif chunk.choices[0].finish_reason == "stop":
                        end_flag = True

        references_json = json.dumps(source_file_names_text_list)
        yield f"\n<<REFERENCES_START>>\n{references_json}\n"

    def get_full_content():
        return "".join(accumulated_text)

    def get_token_usage():
        return token_usage

    return (
        stream_generator,
        get_full_content,
        source_file_names_text_list,
        get_token_usage,
    )


def _trim_messages(messages):
    """会話履歴の合計のトークン数が最大トークン数を超えないように、古いメッセージから削除する。"""
    # 利用するモデルからエンコーディングを取得する。
    encoding = tiktoken.encoding_for_model("gpt-4-1106-preview")

    # 各メッセージのトークン数を計算
    token_counts = [
        (message, len(encoding.encode(message["content"]))) for message in messages
    ]
    total_tokens = sum(count for _, count in token_counts)

    # トークン数が最大トークン数を超えないように、古いメッセージから削除する
    # もし最大トークン数を超える場合は、systemメッセージ以外のメッセージを古い順から削除する。
    # この処理をトークン数が最大トークン数を下回るまで行う。
    max_tokens = 128000 * 0.8
    while total_tokens > max_tokens:
        messages.pop(1)
        total_tokens -= token_counts.pop(1)[1]
        if total_tokens <= max_tokens:
            break

    return messages


def _get_source_prompt(results: Any) -> str:
    sources = []
    for i, result in enumerate(results):
        sources.append(
            "[Source"
            + str(i + 1)
            + "]: "
            + result["content"]
            + "\n"
            + "[SourceFileName"
            + str(i + 1)
            + "]: "
            + result["sourceFileName"]
            + "[Reference"
            + str(i + 1)
            + "]: "
            + result["blobUrl"]
            + "(p."
            + str(result["pageNumber"])
            + ")"
            + "\n"
        )
    return "\n".join(sources)

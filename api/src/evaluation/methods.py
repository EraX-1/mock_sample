def precision_at_k(
    retrieved_docs: list[str],
    relevant_docs: list[str],
    k: int,
) -> float:
    """情報検索システムの評価指標の一つである k における適合率を計算します。

    Args:
    retrieved_docs (list): 検索システムによって取得されたドキュメントのリスト。
    relevant_docs (list): 関連するドキュメントのリスト。
    k (int): 適合率を計算するために考慮する上位 k 件のドキュメント数。

    Returns:
    float: 上位 k 件における適合率。計算は (上位 k 件の取得されたドキュメントのうち関連するドキュメントの数) / k で行われます。

    """
    retrieved_at_k = retrieved_docs[:k]
    relevant_and_retrieved = set(retrieved_at_k) & set(relevant_docs)
    return len(relevant_and_retrieved) / k


def recall_at_k(retrieved_docs: list[str], relevant_docs: list[str], k: int) -> float:
    """指定された k におけるリコールを計算します。

    リコールは、関連文書のうち、検索された文書がどれだけ含まれているかを示す指標です。

    Args:
        retrieved_docs (list[str]): 検索された文書のリスト。
        relevant_docs (list[str]): 関連文書のリスト。
        k (int): 検索結果の上位k件を考慮します。

    Returns:
        float: リコール値。関連文書が存在しない場合は0を返します。

    """
    retrieved_at_k = retrieved_docs[:k]
    relevant_and_retrieved = set(retrieved_at_k) & set(relevant_docs)
    return len(relevant_and_retrieved) / len(relevant_docs) if relevant_docs else 0


def evaluate_precision_recall(
    queries: list[str],
    retriever_results: dict[str, list[str]],
    ground_truth_relevant_docs: dict[str, list[str]],
    k: int,
) -> tuple[float, float]:
    """クエリに対する精度と再現率を評価します。

    Args:
        queries (list[str]): クエリのリスト。
        retriever_results (dict[str, list[str]]): 各クエリに対する検索結果の辞書。
        ground_truth_relevant_docs (dict[str, list[str]]): 各クエリに対する正解の関連文書の辞書。
        k (int): 上位k件の結果を評価するためのパラメータ。

    Returns:
        tuple[float, float]: 平均精度と平均再現率のタプル。

    """
    precisions = []
    recalls = []

    for query in queries:
        retrieved_docs = retriever_results[query]
        relevant_docs = ground_truth_relevant_docs[query]

        precisions.append(precision_at_k(retrieved_docs, relevant_docs, k))
        recalls.append(recall_at_k(retrieved_docs, relevant_docs, k))

    avg_precision = sum(precisions) / len(precisions)
    avg_recall = sum(recalls) / len(recalls)

    return avg_precision, avg_recall


def compute_mrr(
    retrieved_documents: list[list[str]],
    relevant_documents: list[list[str]],
) -> float:
    """Mean Reciprocal Rank (MRR) を計算します。

    MRR は情報検索や質問応答システムの評価指標の一つで、検索結果のリストにおける最初の関連文書の順位の逆数の平均を表します。

    Args:
        retrieved_documents (list[list[str]]): 検索システムが返した文書のリストのリスト。
        relevant_documents (list[list[str]]): 各クエリに対する関連文書のリストのリスト。

    Returns:
        float: MRR の値。全てのクエリに対する平均逆順位。

    """
    reciprocal_ranks = []

    for retrieved, relevant in zip(
        retrieved_documents, relevant_documents, strict=False
    ):
        rank = 0
        for i, doc in enumerate(retrieved):
            if doc in relevant:
                rank = i + 1
                print(rank)
                break

        if rank > 0:
            reciprocal_ranks.append(1 / rank)
        else:
            reciprocal_ranks.append(0)

    return sum(reciprocal_ranks) / len(reciprocal_ranks)


def run_evaluation(
    queries: list[str],
    retriever_results: dict[str, list[str]],
    ground_truth_relevant_docs: dict[str, list[str]],
):
    print(
        "(Precision@K, Recall@K) =",
        evaluate_precision_recall(
            queries=queries,
            retriever_results=retriever_results,
            ground_truth_relevant_docs=ground_truth_relevant_docs,
            k=5,
        ),
    )

    print(
        "MRR =",
        compute_mrr(
            relevant_documents=list(retriever_results.values()),
            retrieved_documents=list(ground_truth_relevant_docs.values()),
        ),
    )

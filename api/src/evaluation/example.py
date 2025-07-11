import json

from src.evaluation.methods import run_evaluation


def extract_content(json_data: dict) -> list[str]:
    return [item["content"] for item in json_data["queryResult"]["value"]]


def extract_docs_from_file(file_path: str) -> tuple[list[str], list[str], str]:
    with open(file_path, encoding="utf-8") as f:
        result = json.load(f)
    return result["relevantDocuments"], extract_content(result), result["query"]


def load_evaluation_data(
    file_paths: list[str],
) -> tuple[list[str], dict[str, list[str]], dict[str, list[str]]]:
    queries = []
    retriever_results = {}
    ground_truth_relevant_docs = {}

    for file_path in file_paths:
        relevant_docs, retrieved_docs, query = extract_docs_from_file(file_path)
        queries.append(query)
        retriever_results[query] = retrieved_docs
        ground_truth_relevant_docs[query] = relevant_docs

    return queries, retriever_results, ground_truth_relevant_docs


if __name__ == "__main__":
    file_paths = [
        "src/evaluation/sample_1.json",
        "src/evaluation/sample_2.json",
        "src/evaluation/sample_3.json",
    ]

    queries, retriever_results, ground_truth_relevant_docs = load_evaluation_data(
        file_paths,
    )

    run_evaluation(queries, retriever_results, ground_truth_relevant_docs)

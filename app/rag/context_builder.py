from typing import Any


def build_context(results: list[dict[str, Any]]) -> str:
    """
    Build deterministic LLM context from retrieved RAG results.

    Includes only safe retrieval metadata and content.
    """

    if not results:
        return ""

    context_blocks = []

    for index, result in enumerate(results, start=1):
        title = result.get("title") or "Untitled"
        category = result.get("category") or "unknown"
        content = result.get("content") or ""

        block = (
            f"[Context {index}]\n"
            f"Title: {title}\n"
            f"Category: {category}\n"
            f"Record ID: {result.get('record_id')}\n"
            f"Content: {content}"
        )

        context_blocks.append(block)

    return "\n\n".join(context_blocks)


if __name__ == "__main__":
    print("Context builder test")

    sample_results = [
        {
            "record_id": "company_001",
            "title": "Company Overview",
            "category": "company",
            "content": "MoinSystems AI is a full-service software development company.",
        },
        {
            "record_id": "company_003",
            "title": "Core Approach",
            "category": "company",
            "content": "The team first understands the business problem before recommending a solution.",
        },
    ]

    context = build_context(sample_results)

    print()
    print(context)
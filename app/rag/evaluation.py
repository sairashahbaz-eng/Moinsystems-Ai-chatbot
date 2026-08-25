import json
from pathlib import Path

from app.rag.retriever import RAGRetriever


DATASET = Path("data/MoinSystems_AI_Public_Chatbot_RAG_Dataset_v2.jsonl")

TEST_QUERIES = [
    ("What services does MoinSystems AI provide?", "service"),
    ("Do you provide SaaS development?", "saas"),
    ("What is the price of your services?", "pricing"),
    ("Do you provide backend development?", "backend"),
    ("Do you build websites?", "web"),
    ("Do you develop mobile applications?", "mobile"),
    ("Do you provide AI chatbot development?", "ai"),
    ("Tell me about quantum computing research.", "unknown"),
]


def main():
    print("Starting Day 3 retrieval evaluation...")
    print()

    retriever = RAGRetriever(
        top_k=5,
        threshold=0.30,
    )

    report = []

    for query, expected in TEST_QUERIES:
        print("=" * 70)
        print(f"Query: {query}")
        print(f"Expected: {expected}")

        results = retriever.retrieve(query)

        top5 = [
            {
                "record_id": r["record_id"],
                "score": round(r["score"], 4),
            }
            for r in results[:5]
        ]

        top3 = top5[:3]

        if expected == "unknown":
            passed = len(results) == 0
        else:
            passed = len(results) > 0

        print(f"Top-3: {top3}")
        print(f"Top-5: {top5}")
        print(f"PASS: {passed}")

        report.append({
            "query": query,
            "expected": expected,
            "top_3": top3,
            "top_5": top5,
            "passed": passed,
        })

    output = Path("data/day3_retrieval_evaluation.json")
    output.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    passed_count = sum(x["passed"] for x in report)

    print()
    print("=" * 70)
    print("DAY 3 EVALUATION SUMMARY")
    print(f"Passed: {passed_count}/{len(report)}")
    print(f"Report saved: {output}")


if __name__ == "__main__":
    main()
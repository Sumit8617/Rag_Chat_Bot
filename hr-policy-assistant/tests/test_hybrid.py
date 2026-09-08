import sys
from app.retrieval.hybrid import HybridRetriever


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    retriever = HybridRetriever()

    questions = [
        "How many casual leave days can I carry forward?",
        "Can sick leave be carried to the next year?",
        "When does carried-forward casual leave expire?",
        "How many privilege leave days can I carry forward?",
        "What does section 4.1 say about CL?",
        "Does the Standard health tier cover dental implants?",
        "Can I send confidential company files to my personal Gmail?"
    ]

    for question in questions:

        print("\n" + "=" * 80)

        print(
            f"QUESTION: {question}"
        )

        print("=" * 80)

        results = retriever.retrieve(
            question,
            top_k=5
        )

        if not results:

            print("No results found.")

            continue

        for i, result in enumerate(
            results,
            start=1
        ):

            print(
                f"\n--- Result {i} ---"
            )

            print(
                f"Document       : "
                f"{result['document']}"
            )

            print(
                f"Section        : "
                f"{result['metadata']['section']}"
            )

            print(
                f"Vector Rank    : "
                f"{result.get('vector_rank')}"
            )

            print(
                f"Keyword Rank   : "
                f"{result.get('keyword_rank')}"
            )

            print(
                f"Keyword Score  : "
                f"{result.get('keyword_score', 0.0):.4f}"
            )

            print(
                f"Distance       : "
                f"{result.get('distance')}"
            )

            print(
                f"RRF Score      : "
                f"{result.get('rrf_score', 0.0):.6f}"
            )

            print(
                f"Exact Section  : "
                f"{result.get('exact_section_match', False)}"
            )

            print(
                f"Text           : "
                f"{result['text'][:500]}"
            )


if __name__ == "__main__":
    main()
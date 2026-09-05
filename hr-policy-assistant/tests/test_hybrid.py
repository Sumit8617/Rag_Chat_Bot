from app.retrieval.hybrid import HybridRetriever


retriever = HybridRetriever()

questions = [
    "How many casual leave days can I carry forward?",
    "Can sick leave be carried to the next year?",
    "When does carried-forward casual leave expire?",
    "How many privilege leave days can I carry forward?",
    "What does section 4.1 say about CL?"
]


for question in questions:

    print("\n" + "=" * 80)
    print(f"QUESTION: {question}")
    print("=" * 80)

    results = retriever.retrieve(question, top_k=5)

    for i, result in enumerate(results, start=1):

        print(f"\n--- Result {i} ---")

        print(
            f"Section       : "
            f"{result['metadata']['section']}"
        )

        print(
            f"Vector Rank   : "
            f"{result['vector_rank']}"
        )

        print(
            f"Keyword Rank  : "
            f"{result['keyword_rank']}"
        )

        print(
            f"Keyword Score : "
            f"{result['keyword_score']:.4f}"
        )

        print(
            f"RRF Score     : "
            f"{result['rrf_score']:.6f}"
        )

        print(
            f"Exact Section : "
            f"{result['exact_section_match']}"
        )

        print(
            f"Text          : "
            f"{result['document']}"
        )
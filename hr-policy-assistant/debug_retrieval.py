from app.retrieval.hybrid import HybridRetriever
from app.retrieval.grounding import GroundingChecker

retriever = HybridRetriever()
checker = GroundingChecker()

questions = [
    "How many remote days per week does the Hybrid tier get?",
    "What is the equipment allowance for the Fully Remote tier?",
    "Can I expense a personal home gym?",
    "Does the company provide free gym membership?",
    "What is the company's maternity leave policy?",
]

for q in questions:
    print("\n" + "=" * 80)
    print(f"QUESTION: {q}")
    print("=" * 80)

    results = retriever.retrieve(q, top_k=5)

    for i, r in enumerate(results, start=1):
        print(f"\n--- Result {i} ---")
        print(f"Document      : {r['metadata']['document']}")
        print(f"Section       : {r['metadata']['section']}")
        print(f"Distance      : {r.get('distance')}")
        print(f"Vector Rank   : {r.get('vector_rank')}")
        print(f"Keyword Rank  : {r.get('keyword_rank')}")
        print(f"Keyword Score : {r.get('keyword_score')}")
        print(f"RRF Score     : {r.get('rrf_score')}")
        print(f"Exact Section : {r.get('exact_section_match')}")

    grounded = checker.is_grounded(results)
    print(f"\nGROUNDED: {grounded}")
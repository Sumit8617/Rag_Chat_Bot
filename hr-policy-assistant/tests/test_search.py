from app.retrieval.embeddings import EmbeddingService
from app.retrieval.vector_store import VectorStore
from app.config import settings


embedding_service = EmbeddingService()
vector_store = VectorStore()


questions = [
    "How many casual leave days can I carry forward?",
    "Can sick leave be carried to the next year?",
    "When does carried-forward casual leave expire?",
    "How many privilege leave days can I carry forward?"
]


for question in questions:

    print("\n" + "=" * 80)
    print(f"QUESTION: {question}")
    print("=" * 80)

    query_embedding = embedding_service.embed_query(question)

    results = vector_store.search(
        query_embedding,
        top_k=settings.top_k
    )

    for i, result in enumerate(results, start=1):

        print(f"\n--- Result {i} ---")

        print(
            f"Document : {result['metadata']['document']}"
        )

        print(
            f"Section  : {result['metadata']['section']}"
        )

        print(
            f"Distance : {result['distance']:.4f}"
        )

        print(
            f"Text     : {result['document']}"
        )
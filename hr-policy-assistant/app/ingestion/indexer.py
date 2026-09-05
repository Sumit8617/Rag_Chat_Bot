from app.retrieval.embeddings import EmbeddingService
from app.retrieval.vector_store import VectorStore


class PolicyIndexer:

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()

    def index_chunks(self, chunks: list[dict]):
        """
        Generate embeddings and store chunks in ChromaDB.
        """

        if not chunks:
            return 0

        texts = [
            f"Section: {chunk['section']}\n\n{chunk['text']}"
            for chunk in chunks
        ]

        embeddings = self.embedding_service.embed_documents(
            texts
        )

        self.vector_store.add_chunks(
            chunks,
            embeddings
        )

        return len(chunks)
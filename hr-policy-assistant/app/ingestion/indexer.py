from app.retrieval.embeddings import EmbeddingService
from app.retrieval.vector_store import VectorStore


class PolicyIndexer:

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()

    def index_chunks(self, chunks: list[dict]):
        """
        Generate embeddings and store chunks in ChromaDB.

        Any previously indexed chunks belonging to the same
        document are deleted first, so re-indexing a document
        (e.g. an updated policy) replaces the old chunks instead
        of leaving stale ones behind alongside the new ones.
        """

        if not chunks:
            return 0

        document_name = chunks[0]["document"]

        self.vector_store.delete_by_document(document_name)

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
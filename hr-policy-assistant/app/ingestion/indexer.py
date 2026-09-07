from app.retrieval.embeddings import EmbeddingService
from app.retrieval.vector_store import VectorStore


class PolicyIndexer:

    def __init__(self, embedding_service: EmbeddingService | None = None):
        
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = VectorStore()

    def index_chunks(self, chunks: list[dict]):
        

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
from sentence_transformers import SentenceTransformer

from app.config import settings


class EmbeddingService:

    def __init__(self):
        print(
            f"Loading embedding model: "
            f"{settings.embedding_model}"
        )

        self.model = SentenceTransformer(
            settings.embedding_model,
            local_files_only=settings.embedding_local_files_only
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple document chunks.
        """

        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True
        )

        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """
        Generate an embedding for a user query.
        """

        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        embedding = self.model.encode(
            query,
            normalize_embeddings=True
        )

        return embedding.tolist()
from sentence_transformers import SentenceTransformer

from app.config import settings


class EmbeddingService:
    """
    Generates local embeddings using SentenceTransformers.

    The embedding model runs locally and does not send policy text
    to an external embedding API.
    """

    def __init__(self):
        print(
            f"Loading embedding model: "
            f"{settings.embedding_model}"
        )

        try:
            self.model = SentenceTransformer(
                settings.embedding_model,
                local_files_only=settings.embedding_local_files_only
            )

        except Exception as exc:
            raise RuntimeError(
                f"Could not load embedding model "
                f"'{settings.embedding_model}'. "
                f"Make sure the model has been downloaded and cached "
                f"locally."
            ) from exc

    def embed_documents(
        self,
        texts: list[str]
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple document chunks.
        """

        if not texts:
            return []

        cleaned_texts = [
            text.strip()
            for text in texts
            if text and text.strip()
        ]

        if not cleaned_texts:
            return []

        embeddings = self.model.encode(
            cleaned_texts,
            normalize_embeddings=True,
            convert_to_numpy=True
        )

        return embeddings.tolist()

    def embed_query(
        self,
        query: str
    ) -> list[float]:
        """
        Generate an embedding for a user query.
        """

        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        embedding = self.model.encode(
            query.strip(),
            normalize_embeddings=True,
            convert_to_numpy=True
        )

        return embedding.tolist()
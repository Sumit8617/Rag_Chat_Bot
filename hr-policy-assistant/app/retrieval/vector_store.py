import chromadb

from app.config import settings


class VectorStore:
    """
    ChromaDB-backed vector store for HR policy chunks.
    """

    COLLECTION_NAME = "hr_policies"

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_path
        )

        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={
                "hnsw:space": "cosine"
            }
        )

    # Add / update chunks
    def add_chunks(
        self,
        chunks: list[dict],
        embeddings: list[list[float]]
    ):
        """
        Store policy chunks and their embeddings.
        """

        if not chunks:
            return

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks and embeddings must match."
            )

        ids = [
            chunk["chunk_id"]
            for chunk in chunks
        ]

        documents = [
            chunk["text"]
            for chunk in chunks
        ]

        metadatas = [
            {
                "document": chunk["document"],
                "section": chunk["section"],
            }
            for chunk in chunks
        ]

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

    # Semantic search
    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5
    ) -> list[dict]:
        """
        Perform semantic similarity search.
        """

        if not query_embedding:
            return []

        collection_count = self.collection.count()

        if collection_count == 0:
            return []

        top_k = max(
            1,
            min(top_k, collection_count)
        )

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=[
                "documents",
                "metadatas",
                "distances"
            ]
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0]

        matches = []

        for i in range(len(documents)):
            metadata = metadatas[i] or {}

            matches.append(
                {
                    "chunk_id": ids[i],
                    "text": documents[i],
                    "document": metadata.get(
                        "document",
                        "unknown"
                    ),
                    "metadata": metadata,
                    "distance": distances[i]
                }
            )

        return matches

    # Get every indexed chunk
    def get_all_chunks(self) -> list[dict]:
        """
        Return all indexed policy chunks.

        Used by the keyword retrieval stage.
        """

        results = self.collection.get(
            include=[
                "documents",
                "metadatas"
            ]
        )

        documents = results.get(
            "documents",
            []
        )

        metadatas = results.get(
            "metadatas",
            []
        )

        ids = results.get(
            "ids",
            []
        )

        chunks = []

        for i in range(len(documents)):
            metadata = metadatas[i] or {}

            chunks.append(
                {
                    "chunk_id": ids[i],
                    "text": documents[i],
                    "document": metadata.get(
                        "document",
                        "unknown"
                    ),
                    "metadata": metadata
                }
            )

        return chunks

    # Delete a document
    def delete_by_document(
        self,
        document_name: str
    ):
        """
        Delete all chunks belonging to a document.
        """

        if not document_name:
            return

        self.collection.delete(
            where={
                "document": document_name
            }
        )

    # Utility
    def count(self) -> int:
        """
        Return number of indexed chunks.
        """

        return self.collection.count()
import chromadb

from app.config import settings


class VectorStore:

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_path
        )

        # EmbeddingService normalizes vectors specifically for cosine
        # similarity. Chroma's default HNSW space is squared L2, which
        # for unit vectors is on a 0-4 scale (2 - 2*cos_sim) instead of
        # cosine distance's 0-2 scale (1 - cos_sim). GroundingChecker's
        # max_distance threshold assumes the cosine scale, so the space
        # must be set explicitly or correct top matches get refused.
        self.collection = self.client.get_or_create_collection(
            name="hr_policies",
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(
        self,
        chunks: list[dict],
        embeddings: list[list[float]]
    ):
        """
        Store chunks and their embeddings in ChromaDB.
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

    def search(self, query_embedding: list[float], top_k: int = 5):
    
        if not query_embedding:
            return []

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]
        ids = results["ids"][0]

        matches = []

        for i in range(len(documents)):
            matches.append(
                {
                    "chunk_id": ids[i],
                    "document": documents[i],
                    "metadata": metadatas[i],
                    "distance": distances[i]
                }
            )

        return matches


    def get_all_chunks(self):
        """
        Return all indexed policy chunks.

        Used by keyword retrieval because keyword search
        should not depend on the vector search results.
        """

        results = self.collection.get(
            include=["documents", "metadatas"]
        )

        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        ids = results.get("ids", [])

        chunks = []

        for i in range(len(documents)):
            chunks.append(
                {
                    "chunk_id": ids[i],
                    "document": documents[i],
                    "metadata": metadatas[i]
                }
            )

        return chunks


    def delete_by_document(self, document_name: str):
        """
        Delete all previously indexed chunks belonging to a
        given document name.

        Called before re-indexing so a re-uploaded or updated
        policy replaces its old chunks instead of leaving stale
        ones (with outdated section boundaries) alongside the
        new ones.
        """

        if not document_name:
            return

        self.collection.delete(
            where={"document": document_name}
        )
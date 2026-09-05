import chromadb

from app.config import settings


class VectorStore:

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_path
        )

        self.collection = self.client.get_or_create_collection(
            name="hr_policies"
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
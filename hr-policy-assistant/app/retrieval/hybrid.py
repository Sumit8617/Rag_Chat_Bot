import re

from app.config import settings
from app.retrieval.embeddings import EmbeddingService
from app.retrieval.vector_store import VectorStore
from app.retrieval.keyword_search import keyword_score


class HybridRetriever:
    def __init__(self, embedding_service: EmbeddingService | None = None):

        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = VectorStore()

    def retrieve(self, query: str, top_k: int | None = None) -> list[dict]:
        if not query or not query.strip():
            return []

        top_k = top_k or settings.top_k

        # 1. Semantic retrieval
        query_embedding = self.embedding_service.embed_query(query)

        vector_results = self.vector_store.search(
            query_embedding,
            top_k=max(top_k * 2, 10)
        )

        vector_rank = {
            result["chunk_id"]: rank
            for rank, result in enumerate(vector_results, start=1)
        }

        # 2. Keyword retrieval over all chunks
        all_chunks = self.vector_store.get_all_chunks()

        keyword_results = []

        for chunk in all_chunks:
            searchable_text = (
                f"Section: {chunk['metadata']['section']}\n"
                f"{chunk['document']}"
            )

            score = keyword_score(query, searchable_text)

            keyword_results.append({
                **chunk,
                "keyword_score": score
            })

        keyword_results.sort(
            key=lambda x: x["keyword_score"],
            reverse=True
        )

        keyword_rank = {
            result["chunk_id"]: rank
            for rank, result in enumerate(keyword_results, start=1)
        }

        # 3. Combine candidates
        candidates = {}

        for result in vector_results:
            candidates[result["chunk_id"]] = {
                **result,
                "vector_rank": vector_rank[result["chunk_id"]],
                "keyword_rank": keyword_rank.get(
                    result["chunk_id"]
                ),
                "keyword_score": 0.0,
            }

        for result in keyword_results:
            if result["chunk_id"] not in candidates:
                candidates[result["chunk_id"]] = {
                    **result,
                    "vector_rank": None,
                    "keyword_rank": keyword_rank[result["chunk_id"]],
                }
            else:
                candidates[result["chunk_id"]]["keyword_score"] = (
                    result["keyword_score"]
                )

        rrf_k = settings.rrf_k
        vector_weight = settings.rrf_vector_weight
        keyword_weight = settings.rrf_keyword_weight

        for result in candidates.values():

            vector_component = 0.0
            keyword_component = 0.0

            if result["vector_rank"] is not None:
                vector_component = (
                    vector_weight / (rrf_k + result["vector_rank"])
                )

            if result["keyword_rank"] is not None:
                keyword_component = (
                    keyword_weight / (rrf_k + result["keyword_rank"])
                )

            rrf_score = vector_component + keyword_component

            # 5. Exact section-number boost
            section_match = re.search(
                r"\bsection\s+(\d+(?:\.\d+)+)\b",
                query.lower()
            )

            exact_section_match = False

            if section_match:
                requested_section = section_match.group(1)

                actual_section = result["metadata"]["section"]

                if actual_section.startswith(requested_section):
                    exact_section_match = True
                    rrf_score += 0.02

            result["rrf_score"] = rrf_score
            result["exact_section_match"] = exact_section_match

        # 6. Final ranking
        ranked_results = sorted(
            candidates.values(),
            key=lambda x: x["rrf_score"],
            reverse=True
        )

        return ranked_results[:top_k]
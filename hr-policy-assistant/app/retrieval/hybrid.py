import re

from app.config import settings
from app.retrieval.embeddings import EmbeddingService
from app.retrieval.vector_store import VectorStore
from app.retrieval.keyword_search import keyword_score


SECTION_PATTERN = re.compile(
    r"\bsection\s+(\d+(?:\.\d+)*)\b",
    re.IGNORECASE
)

ABBREVIATION_EXPANSIONS = [
    (re.compile(r"\bCL\b", re.IGNORECASE), "casual leave"),
    (re.compile(r"\bSL\b", re.IGNORECASE), "sick leave"),
    (re.compile(r"\bPL\b", re.IGNORECASE), "privilege leave"),
    (re.compile(r"\bPTO\b", re.IGNORECASE), "privilege leave"),
    (re.compile(r"\bLTA\b", re.IGNORECASE), "leave travel allowance"),
    (re.compile(r"\bhealth\s+insurance\b", re.IGNORECASE), "health coverage"),
    (re.compile(r"\bmedical\s+insurance\b", re.IGNORECASE), "health coverage"),
    (re.compile(r"\bnon-sso\b", re.IGNORECASE), "without SSO"),
    (re.compile(r"\bnon\s+sso\b", re.IGNORECASE), "without SSO"),
    (re.compile(r"\bWFH\b", re.IGNORECASE), "work from home"),
]


def expand_query(query: str) -> str:
    """
    Expand standard HR policy abbreviations into full phrases
    so both semantic vector search and keyword lexical search
    reliably match policy documentation.
    """
    expanded = query
    for pattern, replacement in ABBREVIATION_EXPANSIONS:
        expanded = pattern.sub(replacement, expanded)
    return expanded


class HybridRetriever:
    """
    Hybrid retrieval using:

    1. Semantic vector similarity
    2. Keyword matching
    3. Reciprocal Rank Fusion
    4. Exact section-number boosting
    """

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None
    ):
        self.embedding_service = (
            embedding_service
            or EmbeddingService()
        )

        self.vector_store = VectorStore()

    # Main retrieval
    def search(
        self,
        query: str,
        top_k: int | None = None
    ) -> list[dict]:
        """
        Alias for retrieve to support callers expecting a .search() interface.
        """
        return self.retrieve(query=query, top_k=top_k)

    def retrieve(
        self,
        query: str,
        top_k: int | None = None
    ) -> list[dict]:

        if not query or not query.strip():
            return []

        query = expand_query(query.strip())

        top_k = top_k or settings.top_k

        # 1. Semantic retrieval
        query_embedding = (
            self.embedding_service.embed_query(
                query
            )
        )

        vector_results = self.vector_store.search(
            query_embedding,
            top_k=max(
                top_k * 2,
                10
            )
        )

        vector_rank = {
            result["chunk_id"]: rank
            for rank, result in enumerate(
                vector_results,
                start=1
            )
        }

        # 2. Keyword retrieval
        all_chunks = (
            self.vector_store.get_all_chunks()
        )

        keyword_results = []

        for chunk in all_chunks:

            metadata = chunk.get(
                "metadata",
                {}
            )

            section = metadata.get(
                "section",
                ""
            )

            document_name = chunk.get(
                "document",
                ""
            )

            chunk_text = chunk.get(
                "text",
                ""
            )

            # IMPORTANT: Search the actual policy text, not just the filename.
            searchable_text = (
                f"Section: {section}\n"
                f"Document: {document_name}\n"
                f"{chunk_text}"
            )

            score = keyword_score(
                query,
                searchable_text
            )

            if score > 0.0:

                keyword_results.append(
                    {
                        **chunk,
                        "keyword_score": score
                    }
                )

        keyword_results.sort(
            key=lambda result: result["keyword_score"],
            reverse=True
        )

        keyword_rank = {
            result["chunk_id"]: rank
            for rank, result in enumerate(
                keyword_results,
                start=1
            )
        }

        # 3. Combine candidates
        candidates = {}

        for result in vector_results:

            chunk_id = result["chunk_id"]

            candidates[chunk_id] = {
                **result,
                "vector_rank": vector_rank[chunk_id],
                "keyword_rank": keyword_rank.get(
                    chunk_id
                ),
                "keyword_score": 0.0
            }

        for result in keyword_results:

            chunk_id = result["chunk_id"]

            if chunk_id not in candidates:

                candidates[chunk_id] = {
                    **result,
                    "vector_rank": None,
                    "keyword_rank": keyword_rank[chunk_id],
                    "keyword_score": result[
                        "keyword_score"
                    ]
                }

            else:

                candidates[chunk_id][
                    "keyword_score"
                ] = result["keyword_score"]

        # 4. Reciprocal Rank Fusion
        rrf_k = settings.rrf_k

        vector_weight = (
            settings.rrf_vector_weight
        )

        keyword_weight = (
            settings.rrf_keyword_weight
        )

        # 5. Exact section detection
        section_match = SECTION_PATTERN.search(
            query
        )

        requested_section = None

        if section_match:
            requested_section = (
                section_match.group(1)
            )

        # 6. Calculate final scores
        for result in candidates.values():

            vector_component = 0.0

            keyword_component = 0.0

            # Vector contribution
            if result["vector_rank"] is not None:

                vector_component = (
                    vector_weight
                    / (
                        rrf_k
                        + result["vector_rank"]
                    )
                )

            # Keyword contribution
            if result["keyword_rank"] is not None:

                keyword_component = (
                    keyword_weight
                    / (
                        rrf_k
                        + result["keyword_rank"]
                    )
                )

            rrf_score = (
                vector_component
                + keyword_component
            )

            # Exact section boost
            exact_section_match = False

            if requested_section:

                actual_section = result[
                    "metadata"
                ].get(
                    "section",
                    ""
                ).strip()

                if (
                    actual_section == requested_section
                    or actual_section.startswith(
                        requested_section + " "
                    )
                    or actual_section.startswith(
                        requested_section + ":"
                    )
                ):
                    exact_section_match = True

                    rrf_score += 0.02

            result["rrf_score"] = rrf_score

            result["exact_section_match"] = (
                exact_section_match
            )

        # 7. Final ranking
        ranked_results = sorted(
            candidates.values(),
            key=lambda result: (
                result["rrf_score"],
                result["exact_section_match"],
                result.get("keyword_score", 0.0)
            ),
            reverse=True
        )

        return ranked_results[:top_k]
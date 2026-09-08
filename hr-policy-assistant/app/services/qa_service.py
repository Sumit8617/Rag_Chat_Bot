from typing import Any

from app.config import settings
from app.retrieval.embeddings import EmbeddingService
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.grounding import GroundingChecker
from app.generation.generator import PolicyGenerator
from app.generation.citation_validator import CitationValidator


class QAService:

    REFUSAL_MESSAGE = (
        "I don't have enough information in the uploaded policies "
        "to answer this question. Please contact HR."
    )

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        retriever=None,
        generator=None,
        grounding_checker=None,
        citation_validator=None,
    ):
        self.embedding_service = embedding_service
        self.retriever = (
            retriever
            if retriever is not None
            else HybridRetriever(embedding_service=embedding_service)
        )
        self.grounding_checker = (
            grounding_checker
            if grounding_checker is not None
            else GroundingChecker()
        )
        self.citation_validator = (
            citation_validator
            if citation_validator is not None
            else CitationValidator()
        )
        self._generator = generator

    @property
    def generator(self):
        if self._generator is not None:
            return self._generator
        try:
            self._generator = PolicyGenerator()
            return self._generator
        except Exception:
            return None

    @generator.setter
    def generator(self, value):
        self._generator = value

    # RETRIEVAL + GROUNDING
    def retrieve_and_ground(
        self,
        question: str,
        top_k: int | None = None,
    ) -> dict[str, Any]:

        if self.retriever is None:
            raise RuntimeError(
                "Retriever is not configured."
            )

        k = top_k if top_k is not None else settings.top_k

        # Retrieve documents (support both retrieve and search API)
        if hasattr(self.retriever, "retrieve"):
            results = self.retriever.retrieve(
                question,
                top_k=k
            )
        elif hasattr(self.retriever, "search"):
            results = self.retriever.search(
                question,
                top_k=k
            )
        else:
            raise RuntimeError(
                "Retriever must implement 'retrieve' or 'search'."
            )

        if results is None:
            results = []

        # Grounding check
        decision = self.grounding_checker.check(results)

        return {
            "question": question,
            "results": results,
            "grounded": decision.grounded,
            "grounding_reason": decision.reason,
        }

    # ANSWER GENERATION & CITATION VALIDATION
    def generate_answer(
        self,
        question: str,
        retrieval_data: dict[str, Any],
    ) -> dict[str, Any]:

        grounded = retrieval_data.get(
            "grounded",
            False
        )

        results = retrieval_data.get(
            "results",
            []
        )

        # Refuse when retrieval is not grounded or results empty

        if not grounded or not results:
            return {
                "answer": self.REFUSAL_MESSAGE,
                "citations": [],
            }

        # Generator unavailable

        generator = self.generator
        if generator is None:
            return {
                "answer": self.REFUSAL_MESSAGE,
                "citations": [],
            }

        # Generate answer
        try:
            try:
                generated = generator.generate(
                    query=question,
                    chunks=results,
                )
            except TypeError:
                generated = generator.generate(
                    question,
                    results,
                )
        except Exception:
            return {
                "answer": self.REFUSAL_MESSAGE,
                "citations": [],
            }
        
        # Extract answer and raw citations
        if hasattr(generated, "citations") and hasattr(generated, "answer"):
            raw_citations = [
                c.model_dump() if hasattr(c, "model_dump") else (
                    c if isinstance(c, dict) else {
                        "document": getattr(c, "document", ""),
                        "section": getattr(c, "section", ""),
                    }
                )
                for c in generated.citations
            ]
            raw_answer = str(generated.answer).strip()
        elif isinstance(generated, dict):
            raw_citations = generated.get("citations", [])
            raw_answer = str(generated.get("answer", "")).strip()
        else:
            raw_citations = []
            raw_answer = str(generated).strip()

        # Validate citations
        citations = self.citation_validator.validate(
            raw_citations,
            results,
        )

        if not citations:
            return {
                "answer": self.REFUSAL_MESSAGE,
                "citations": [],
            }

        return {
            "answer": raw_answer or self.REFUSAL_MESSAGE,
            "citations": citations,
        }

    # MAIN ASK METHOD
    def ask(
        self,
        question: str,
        top_k: int | None = None,
    ) -> dict[str, Any]:

        if not question or not question.strip():
            return {
                "question": question,
                "answer": "Please provide a question.",
                "citations": [],
                "grounded": False,
                "grounding_reason": "Empty question.",
                "results": [],
            }

        question = question.strip()

        retrieval_data = self.retrieve_and_ground(
            question=question,
            top_k=top_k,
        )

        generation_result = self.generate_answer(
            question=question,
            retrieval_data=retrieval_data,
        )

        return {
            "question": question,
            "answer": generation_result["answer"],
            "citations": generation_result["citations"],
            "grounded": retrieval_data["grounded"],
            "grounding_reason": retrieval_data[
                "grounding_reason"
            ],
            "results": retrieval_data["results"],
        }
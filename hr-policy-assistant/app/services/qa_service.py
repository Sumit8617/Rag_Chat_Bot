from app.config import settings
from app.retrieval.embeddings import EmbeddingService
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.grounding import GroundingChecker
from app.generation.generator import PolicyGenerator
from app.generation.citation_validator import CitationValidator


class QAService:

    def __init__(self, embedding_service: EmbeddingService | None = None):
        
        self.retriever = HybridRetriever(embedding_service=embedding_service)
        self.grounding_checker = GroundingChecker()
        self.generator = PolicyGenerator()
        self.citation_validator = CitationValidator()

    def ask(self, question: str) -> dict:


        if not question or not question.strip():
            return {
                "answer": "Please provide a question.",
                "citations": []
            }

        question = question.strip()


        results = self.retriever.retrieve(
            question,
            top_k=settings.top_k
        )


        grounded = self.grounding_checker.is_grounded(
            results
        )

        if not grounded:
            return {
                "answer": (
                    "I don't have enough information in the "
                    "uploaded policies to answer this question. "
                    "Please contact HR."
                ),
                "citations": []
            }


        generated = self.generator.generate(
            question,
            results
        )


        citations = self.citation_validator.validate(
            [citation.model_dump() for citation in generated.citations],
            results
        )


        if not citations:
            return {
                "answer": (
                    "I don't have enough information in the "
                    "uploaded policies to answer this question. "
                    "Please contact HR."
                ),
                "citations": []
            }


        return {
            "answer": generated.answer.strip(),
            "citations": citations
        }
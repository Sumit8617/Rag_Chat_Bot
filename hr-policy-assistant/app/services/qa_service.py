from app.config import settings
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.grounding import GroundingChecker
from app.generation.generator import PolicyGenerator
from app.generation.citation_validator import CitationValidator


class QAService:

    def __init__(self):
        self.retriever = HybridRetriever()
        self.grounding_checker = GroundingChecker()
        self.generator = PolicyGenerator()
        self.citation_validator = CitationValidator()

    def ask(self, question: str) -> dict:

        # -----------------------------------------
        # 1. Validate question
        # -----------------------------------------

        if not question or not question.strip():
            return {
                "answer": "Please provide a question.",
                "citations": []
            }

        question = question.strip()

        # -----------------------------------------
        # 2. Retrieve relevant policy chunks
        # -----------------------------------------

        results = self.retriever.retrieve(
            question,
            top_k=settings.top_k
        )

        # -----------------------------------------
        # 3. Grounding / relevance check
        # -----------------------------------------

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

        # -----------------------------------------
        # 4. Generate answer
        # -----------------------------------------

        generated = self.generator.generate(
            question,
            results
        )

        # -----------------------------------------
        # 5. Validate citations
        # -----------------------------------------

        citations = self.citation_validator.validate(
            [citation.model_dump() for citation in generated.citations],
            results
        )

        # -----------------------------------------
        # 6. Refuse if no valid citations
        # -----------------------------------------

        if not citations:
            return {
                "answer": (
                    "I don't have enough information in the "
                    "uploaded policies to answer this question. "
                    "Please contact HR."
                ),
                "citations": []
            }

        # -----------------------------------------
        # 7. Final structured response
        # -----------------------------------------

        return {
            "answer": generated.answer.strip(),
            "citations": citations
        }
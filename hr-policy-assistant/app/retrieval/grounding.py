from dataclasses import dataclass
from typing import Any


@dataclass
class GroundingDecision:
    grounded: bool
    reason: str = ""


class GroundingChecker:
    """
    Determines whether retrieved results provide enough evidence
    to answer a user question safely.

    Grounding rules:
    1. Exact section match -> always grounded.
    2. Strong semantic similarity -> grounded.
    3. Good semantic + keyword evidence -> grounded.
    4. Otherwise -> not grounded.
    """

    # Lower Chroma distance = better semantic similarity.
    STRONG_DISTANCE_THRESHOLD = 0.25

    # Hybrid retrieval score.
    MIN_RRF_SCORE = 0.015

    # Keyword overlap score.
    MIN_KEYWORD_SCORE = 0.50

    def check(self, results: list[Any]) -> GroundingDecision:
        """
        Check whether retrieved results contain sufficient evidence.
        """

        if not results:
            return GroundingDecision(
                grounded=False,
                reason="No retrieval results were found."
            )

        # Rule 1: Exact section match
        for result in results:
            exact_section = self._get_value(
                result,
                "exact_section",
                None
            )
            if exact_section is None:
                exact_section = self._get_value(
                    result,
                    "exact_section_match",
                    False
                )

            if exact_section is True:
                return GroundingDecision(
                    grounded=True,
                    reason="Exact policy section match found."
                )

        # Rule 2: Strong semantic evidence
        for result in results:
            distance = self._get_value(
                result,
                "distance",
                None
            )

            rrf_score = self._get_value(
                result,
                "rrf_score",
                None
            )

            if (
                distance is not None
                and distance <= self.STRONG_DISTANCE_THRESHOLD
                and (
                    rrf_score is None
                    or rrf_score >= self.MIN_RRF_SCORE
                )
            ):
                return GroundingDecision(
                    grounded=True,
                    reason="Strong semantic retrieval evidence found."
                )

        # Rule 3: Semantic + keyword evidence
        for result in results:
            distance = self._get_value(
                result,
                "distance",
                None
            )

            rrf_score = self._get_value(
                result,
                "rrf_score",
                None
            )

            keyword_score = self._get_value(
                result,
                "keyword_score",
                None
            )

            if (
                distance is not None
                and distance <= 0.70
                and rrf_score is not None
                and rrf_score >= self.MIN_RRF_SCORE
                and keyword_score is not None
                and keyword_score >= self.MIN_KEYWORD_SCORE
            ):
                return GroundingDecision(
                    grounded=True,
                    reason="Semantic and keyword evidence agree."
                )

        # No sufficiently strong evidence
        return GroundingDecision(
            grounded=False,
            reason="Retrieved evidence is too weak to answer reliably."
        )

    def is_grounded(self, results: list[Any]) -> bool:
        """
        Simple helper used by QAService and tests.
        """

        return self.check(results).grounded

    @staticmethod
    def _get_value(
        result: Any,
        key: str,
        default: Any = None
    ) -> Any:
        """
        Supports both dictionaries and dataclass/object results.

        This is important because:
        - production retrieval may return dictionaries
        - unit tests use FakeResult dataclasses
        """

        if isinstance(result, dict):
            return result.get(key, default)

        return getattr(result, key, default)
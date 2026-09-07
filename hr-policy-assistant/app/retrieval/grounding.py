from app.config import settings


class GroundingChecker:

    def __init__(self):
        self.max_distance = settings.grounding_max_distance
        self.top_n_check = settings.grounding_top_n_check

        vector_only_ceiling = (
            settings.rrf_vector_weight / (settings.rrf_k + 1)
        )

        self.min_rrf_score = (
            settings.grounding_rrf_threshold_fraction
            * vector_only_ceiling
        )

    def is_grounded(self, results: list[dict]) -> bool:

        if not results:
            return False

        # ground the answer.
        for result in results[: self.top_n_check]:
            if self._is_result_grounded(result):
                return True

        return False

    def _is_result_grounded(self, result: dict) -> bool:

        # Explicit section reference
        if result.get("exact_section_match", False):
            return True

        # Semantic relevance check
        distance = result.get("distance")

        if distance is None:
            return False

        if distance > self.max_distance:
            return False

        # RRF ranking check
        rrf_score = result.get("rrf_score", 0.0)

        if rrf_score < self.min_rrf_score:
            return False

        return True
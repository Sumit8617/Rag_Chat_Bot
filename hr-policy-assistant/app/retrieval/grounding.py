class GroundingChecker:

    def __init__(self):
        self.max_distance = 0.75

        # RRF is only used as a secondary ranking signal.
        self.min_rrf_score = 0.015

    def is_grounded(self, results: list[dict]) -> bool:

        if not results:
            return False

        top_result = results[0]

        # Explicit section reference

        if top_result.get("exact_section_match", False):
            return True

        # Semantic relevance check

        distance = top_result.get("distance")

        if distance is None:
            return False

        if distance > self.max_distance:
            return False

        # RRF ranking check

        rrf_score = top_result.get("rrf_score", 0.0)

        if rrf_score < self.min_rrf_score:
            return False

        return True
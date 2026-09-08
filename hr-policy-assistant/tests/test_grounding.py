from dataclasses import dataclass

from app.retrieval.grounding import GroundingChecker


@dataclass
class FakeResult:
    distance: float | None = None
    rrf_score: float | None = None
    keyword_score: float | None = None
    exact_section: bool = False


def test_exact_section_is_grounded():
    checker = GroundingChecker()

    results = [
        FakeResult(
            exact_section=True
        )
    ]

    decision = checker.check(results)

    assert decision.grounded is True

    print("PASS: exact section match is grounded")


def test_strong_semantic_result_is_grounded():
    checker = GroundingChecker()

    results = [
        FakeResult(
            distance=0.20,
            rrf_score=0.016,
            keyword_score=0.10,
            exact_section=False
        )
    ]

    decision = checker.check(results)

    assert decision.grounded is True

    print("PASS: strong semantic evidence is grounded")


def test_strong_keyword_and_semantic_result_is_grounded():
    checker = GroundingChecker()

    results = [
        FakeResult(
            distance=0.50,
            rrf_score=0.016,
            keyword_score=0.60,
            exact_section=False
        )
    ]

    decision = checker.check(results)

    assert decision.grounded is True

    print("PASS: semantic + keyword evidence is grounded")


def test_weak_result_is_not_grounded():
    checker = GroundingChecker()

    results = [
        FakeResult(
            distance=0.90,
            rrf_score=0.010,
            keyword_score=0.05,
            exact_section=False
        )
    ]

    decision = checker.check(results)

    assert decision.grounded is False

    print("PASS: weak evidence is rejected")


def test_empty_results_are_not_grounded():
    checker = GroundingChecker()

    decision = checker.check([])

    assert decision.grounded is False

    print("PASS: empty retrieval is rejected")


def test_exact_section_beats_weak_scores():
    checker = GroundingChecker()

    results = [
        FakeResult(
            distance=0.99,
            rrf_score=0.001,
            keyword_score=0.0,
            exact_section=True
        )
    ]

    decision = checker.check(results)

    assert decision.grounded is True

    print("PASS: exact section match overrides weak scores")


def test_is_grounded_helper():
    checker = GroundingChecker()

    strong_results = [
        FakeResult(
            distance=0.30,
            rrf_score=0.016,
            keyword_score=0.50,
            exact_section=False
        )
    ]

    weak_results = [
        FakeResult(
            distance=0.95,
            rrf_score=0.005,
            keyword_score=0.01,
            exact_section=False
        )
    ]

    assert checker.is_grounded(strong_results) is True
    assert checker.is_grounded(weak_results) is False

    print("PASS: is_grounded helper")


if __name__ == "__main__":
    test_exact_section_is_grounded()
    test_strong_semantic_result_is_grounded()
    test_strong_keyword_and_semantic_result_is_grounded()
    test_weak_result_is_not_grounded()
    test_empty_results_are_not_grounded()
    test_exact_section_beats_weak_scores()
    test_is_grounded_helper()

    print()
    print("=" * 70)
    print("ALL GROUNDING TESTS PASSED")
    print("=" * 70)
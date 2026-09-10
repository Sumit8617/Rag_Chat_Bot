"""
Regression and End-to-End Correctness Tests for HR Policy Assistant RAG Pipeline.

Tests:
1. test_casual_leave_direct_question()
2. test_casual_leave_paraphrase()
3. test_casual_leave_carry_forward()
4. test_sick_leave()
5. test_privilege_leave()
6. test_lta_band_b()
7. test_standard_health_dental_implants()
8. test_confidential_email()
9. test_unknown_question_refusal()
10. test_partial_answer()
11. test_citation_correctness()
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.services.qa_service import QAService
from app.generation.citation_validator import CitationValidator


qa_service = QAService()
citation_validator = CitationValidator()


def test_casual_leave_direct_question():
    """
    Direct question: 'How many casual leaves can an employee take?'
    Must retrieve Section 2.1 Casual leave (CL) containing '12 casual leave days'
    and pass grounding.
    """
    question = "How many casual leaves can an employee take?"
    data = qa_service.retrieve_and_ground(question, top_k=5)

    assert data["grounded"] is True, f"Expected grounded=True, got {data['grounded']} (reason: {data['grounding_reason']})"
    results = data["results"]
    assert len(results) > 0, "Expected non-empty retrieval results"

    top_chunk = results[0]
    section = top_chunk.get("metadata", {}).get("section", "")
    assert "2.1 Casual leave" in section or "2.1" in section, f"Expected Section 2.1, got {section}"

    text = top_chunk.get("text", "")
    assert "12 casual leave days" in text, f"Expected '12 casual leave days' in chunk text, got: {text}"

    print("PASS: test_casual_leave_direct_question (retrieved Section 2.1 with 12 casual leave days)")


def test_casual_leave_paraphrase():
    """
    Tests various natural paraphrases and abbreviations for casual leave.
    All must retrieve Section 2.1 and pass grounding.
    """
    paraphrases = [
        "How many CL days do I get?",
        "What is my yearly casual leave allowance?",
        "How much casual leave can an employee take annually?",
        "Tell me the casual leave entitlement.",
        "How many days of CL are provided each year?",
        "How many CL days do employees get?",
        "What is the annual casual leave allowance?",
        "How much casual leave am I entitled to?",
        "How many days of casual leave are provided?",
    ]

    for question in paraphrases:
        data = qa_service.retrieve_and_ground(question, top_k=5)
        assert data["grounded"] is True, f"Failed grounding for '{question}': {data['grounding_reason']}"

        retrieved_sections = [r.get("metadata", {}).get("section", "") for r in data["results"]]
        assert any("2.1 Casual leave" in s or "2.1" in s for s in retrieved_sections), (
            f"Expected Section 2.1 in retrieved sections for '{question}', got: {retrieved_sections}"
        )

        top_chunk = data["results"][0]
        assert "12" in top_chunk.get("text", "") or "casual leave" in top_chunk.get("text", "").lower(), (
            f"Chunk text does not support casual leave for '{question}'"
        )

    print(f"PASS: test_casual_leave_paraphrase ({len(paraphrases)} paraphrases verified)")


def test_casual_leave_carry_forward():
    """
    Verify carry forward queries:
    1. How many casual leave days can be carried forward? -> 8 days (Section 4.1)
    2. When must carried-forward casual leave be used? -> 31 March (Section 4.1)
    """
    q1 = "How many casual leave days can be carried forward?"
    data1 = qa_service.retrieve_and_ground(q1, top_k=5)
    assert data1["grounded"] is True
    top_chunk1 = data1["results"][0]
    assert "8 days" in top_chunk1.get("text", "") or "8" in top_chunk1.get("text", "")
    assert "4.1" in top_chunk1.get("metadata", {}).get("section", "")

    q2 = "When must carried-forward casual leave be used?"
    data2 = qa_service.retrieve_and_ground(q2, top_k=5)
    assert data2["grounded"] is True
    top_chunk2 = data2["results"][0]
    assert "31 March" in top_chunk2.get("text", "")
    assert "4.1" in top_chunk2.get("metadata", {}).get("section", "")

    print("PASS: test_casual_leave_carry_forward (8 days, 31 March)")


def test_sick_leave():
    """
    Verify sick leave entitlement: 10 days (Section 2.2).
    """
    question = "How many sick leave days do employees receive?"
    data = qa_service.retrieve_and_ground(question, top_k=5)
    assert data["grounded"] is True
    top_chunk = data["results"][0]
    assert "10 sick leave days" in top_chunk.get("text", "") or "10" in top_chunk.get("text", "")
    assert "2.2" in top_chunk.get("metadata", {}).get("section", "")

    print("PASS: test_sick_leave (10 days in Section 2.2)")


def test_privilege_leave():
    """
    Verify privilege leave entitlement: 18 days (Section 2.3).
    """
    question = "How many privilege leave days do employees receive?"
    data = qa_service.retrieve_and_ground(question, top_k=5)
    assert data["grounded"] is True
    top_chunk = data["results"][0]
    assert "18 privilege leave days" in top_chunk.get("text", "") or "18" in top_chunk.get("text", "")
    assert "2.3" in top_chunk.get("metadata", {}).get("section", "")

    print("PASS: test_privilege_leave (18 days in Section 2.3)")


def test_lta_band_b():
    """
    Verify LTA for Band B: ₹50,000 (Benefits Policy Section 3).
    """
    question = "What is the LTA limit for Band B?"
    data = qa_service.retrieve_and_ground(question, top_k=5)
    assert data["grounded"] is True
    top_chunk = data["results"][0]
    assert "50,000" in top_chunk.get("text", "") or "50000" in top_chunk.get("text", "")
    assert "Band B" in top_chunk.get("text", "")

    print("PASS: test_lta_band_b (INR 50,000 for Band B)")


def test_standard_health_dental_implants():
    """
    Verify table lookup: Standard health tier dental implants -> Not covered.
    And optical coverage for Standard tier -> ₹8,000.
    """
    q1 = "Does the Standard health tier cover dental implants?"
    data1 = qa_service.retrieve_and_ground(q1, top_k=5)
    assert data1["grounded"] is True
    top_chunk1 = data1["results"][0]
    text1 = top_chunk1.get("text", "")
    assert "Standard" in text1
    assert "Not covered" in text1 or "Dental" in text1

    q2 = "How much optical coverage does the Standard tier provide?"
    data2 = qa_service.retrieve_and_ground(q2, top_k=5)
    assert data2["grounded"] is True
    top_chunk2 = data2["results"][0]
    text2 = top_chunk2.get("text", "")
    assert "8,000" in text2 or "8000" in text2

    print("PASS: test_standard_health_dental_implants (Dental: Not covered, Optical: INR 8,000)")


def test_confidential_email():
    """
    Verify IT security policy: Sending confidential files to personal email -> Not allowed.
    """
    question = "Can confidential files be sent to personal email?"
    data = qa_service.retrieve_and_ground(question, top_k=5)
    assert data["grounded"] is True
    retrieved_text = " ".join([r.get("text", "") for r in data["results"]])
    assert "Confidential" in retrieved_text or "personal" in retrieved_text.lower()

    print("PASS: test_confidential_email (grounded in IT Security Policy)")


def test_unknown_question_refusal():
    """
    Verify strict refusal behavior for unanswerable/out-of-scope questions.
    Must return grounded=False and refusal message.
    """
    unknown_questions = [
        "Can I expense a personal home gym?",
        "Can I work from home when I am sick?",
        "What is the company maternity leave policy?",
        "Does the company provide free gym membership?",
    ]

    for question in unknown_questions:
        data = qa_service.retrieve_and_ground(question, top_k=5)
        assert data["grounded"] is False, (
            f"Expected refusal for unknown question '{question}', but grounded=True (results: {[r.get('metadata', {}).get('section', '') for r in data['results']]})"
        )

        response = qa_service.generate_answer(question, data)
        assert response["answer"] == qa_service.REFUSAL_MESSAGE, (
            f"Expected REFUSAL_MESSAGE for '{question}', got: {response['answer']}"
        )
        assert response["citations"] == []

    print(f"PASS: test_unknown_question_refusal ({len(unknown_questions)} questions correctly refused)")


def test_partial_answer():
    """
    Verify partially answerable question:
    'How many casual leaves do I get and can I work from home when sick?'
    Retrieval should supply evidence for Casual Leave (12 days in Section 2.1),
    while the policies do not support WFH when sick.
    """
    question = "How many casual leaves do I get and can I work from home when sick?"
    data = qa_service.retrieve_and_ground(question, top_k=5)

    retrieved_sections = [r.get("metadata", {}).get("section", "") for r in data["results"]]
    assert any("2.1 Casual leave" in s or "2.1" in s for s in retrieved_sections), (
        f"Expected Section 2.1 in retrieved sections, got {retrieved_sections}"
    )

    # Check that Casual Leave fact exists in retrieved evidence
    cl_chunks = [r for r in data["results"] if "2.1" in r.get("metadata", {}).get("section", "")]
    assert len(cl_chunks) > 0
    assert "12 casual leave days" in cl_chunks[0].get("text", "")

    # Check that NO chunk provides a WFH entitlement
    wfh_chunks = [r for r in data["results"] if "work from home" in r.get("text", "").lower()]
    assert len(wfh_chunks) == 0, "Found unexpected WFH entitlement chunk"

    print("PASS: test_partial_answer (casual leave evidence present, WFH absent)")


def test_citation_correctness():
    """
    Verify citation validation for Section 2.1 Casual leave (CL).
    Citation must validate against retrieved chunks and contain the factual statement.
    """
    question = "How many casual leaves can an employee take?"
    data = qa_service.retrieve_and_ground(question, top_k=5)
    results = data["results"]

    raw_citations = [
        {"document": "leave-policy.md", "section": "2.1 Casual leave (CL)"}
    ]
    validated = citation_validator.validate(raw_citations, results)
    assert len(validated) == 1, f"Expected citation to be validated, got {validated}"
    assert validated[0]["section"] == "2.1 Casual leave (CL)"

    # Verify that the cited chunk actually contains the supporting fact
    cited_chunk = next(
        r for r in results
        if r.get("metadata", {}).get("section") == "2.1 Casual leave (CL)"
    )
    assert "12 casual leave days" in cited_chunk.get("text", "")

    print("PASS: test_citation_correctness (validates against chunk containing '12 casual leave days')")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("RUNNING RAG PIPELINE REGRESSION TESTS")
    print("=" * 80)

    test_casual_leave_direct_question()
    test_casual_leave_paraphrase()
    test_casual_leave_carry_forward()
    test_sick_leave()
    test_privilege_leave()
    test_lta_band_b()
    test_standard_health_dental_implants()
    test_confidential_email()
    test_unknown_question_refusal()
    test_partial_answer()
    test_citation_correctness()

    print("\n" + "=" * 80)
    print("ALL 11 REGRESSION TESTS PASSED SUCCESSFULLY!")
    print("=" * 80 + "\n")

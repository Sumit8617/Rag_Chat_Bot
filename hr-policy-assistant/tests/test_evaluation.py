import sys
import json
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.retrieval.hybrid import HybridRetriever
from app.retrieval.grounding import GroundingChecker


# Load evaluation questions
eval_path = Path(__file__).parent / "evaluation_questions.json"
with open(eval_path, "r", encoding="utf-8") as f:
    questions = json.load(f)


retriever = HybridRetriever()
grounding_checker = GroundingChecker()


# Evaluation counters

total = len(questions)

answerable_count = sum(
    1 for question in questions
    if question["answerable"]
)

unanswerable_count = total - answerable_count

correct_retrieval = 0
correct_refusals = 0


# ---------------------------------------------------------
# Start evaluation
# ---------------------------------------------------------

print("\n" + "=" * 80)
print("RAG EVALUATION")
print("=" * 80)


for item in questions:

    question = item["question"]
    expected_answerable = item["answerable"]

    expected_sections = item.get("expected_sections", [])

    # Retrieve relevant chunks

    results = retriever.retrieve(
        question,
        top_k=5
    )

    # Grounding check

    grounded = grounding_checker.is_grounded(results)

  
    # Get retrieved sections

    retrieved_sections = [
        result["metadata"]["section"]
        for result in results
    ]

    # Determine whether test passed

    correct = False

    if expected_answerable:

        if any(
            section in retrieved_sections
            for section in expected_sections
        ):
            correct_retrieval += 1
            correct = True

    else:


        if not grounded:
            correct_refusals += 1
            correct = True

    # Print result

    status = "PASS" if correct else "FAIL"

    print(f"\n[{status}] {question}")

    print(
        f"Expected answerable: "
        f"{expected_answerable}"
    )

    print(
        f"Grounded: "
        f"{grounded}"
    )

    print(
        f"Expected sections: "
        f"{expected_sections}"
    )

    if retrieved_sections:

        print(
            f"Top result: "
            f"{retrieved_sections[0]}"
        )

        if "rrf_score" in results[0]:
            print(
                f"RRF score: "
                f"{results[0]['rrf_score']:.6f}"
            )

    else:

        print("Top result: None")


# Calculate scores

retrieval_percentage = (
    correct_retrieval / answerable_count * 100
    if answerable_count > 0
    else 0
)

refusal_percentage = (
    correct_refusals / unanswerable_count * 100
    if unanswerable_count > 0
    else 0
)

overall_correct = (
    correct_retrieval + correct_refusals
)

overall_percentage = (
    overall_correct / total * 100
    if total > 0
    else 0
)


print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

print(f"Total questions: {total}")

print(
    f"Answerable questions: "
    f"{answerable_count}"
)

print(
    f"Correct retrieval: "
    f"{correct_retrieval}/{answerable_count} "
    f"({retrieval_percentage:.1f}%)"
)

print(
    f"Unanswerable questions: "
    f"{unanswerable_count}"
)

print(
    f"Correct refusals: "
    f"{correct_refusals}/{unanswerable_count} "
    f"({refusal_percentage:.1f}%)"
)

print(
    f"Overall score: "
    f"{overall_correct}/{total} "
    f"({overall_percentage:.1f}%)"
)

print("=" * 80)
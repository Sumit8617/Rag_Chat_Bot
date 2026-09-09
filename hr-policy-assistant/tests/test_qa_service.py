import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.services.qa_service import QAService


def main():

    service = QAService()

    questions = [
        "How many casual leave days can I carry forward?",
        "Does the Standard health tier cover dental implants?",
        "Can I send confidential company files to my personal Gmail?",
        "Can sick leave be carried to the next year?",
        "How many privilege leave days can I carry forward?",
        "Can I expense a personal home gym?",
        "What is the company's maternity leave policy?",
        "",
    ]

    for question in questions:

        print("\n" + "=" * 80)
        print(f"QUESTION: {question}")
        print("=" * 80)

        result = service.ask(question)

        print("\nANSWER:")
        print(result["answer"])

        print("\nCITATIONS:")

        if result["citations"]:
            for citation in result["citations"]:
                print(
                    f"{citation['document']} -> "
                    f"{citation['section']}"
                )
        else:
            print("No citations")


if __name__ == "__main__":
    main()
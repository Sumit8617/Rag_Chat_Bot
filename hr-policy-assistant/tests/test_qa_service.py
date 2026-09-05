from app.services.qa_service import QAService


def main():

    service = QAService()

    questions = [
        "How many casual leave days can I carry forward?",
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
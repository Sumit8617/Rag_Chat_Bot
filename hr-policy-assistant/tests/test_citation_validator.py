import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.generation.citation_validator import CitationValidator


def main():

    validator = CitationValidator()

    retrieved_results = [
        {
            "metadata": {
                "document": "leave-policy.md",
                "section": "4.1 Casual leave carry-forward"
            }
        },
        {
            "metadata": {
                "document": "leave-policy.md",
                "section": "2.1 Casual leave (CL)"
            }
        }
    ]


    citations = [
        {
            "document": "leave-policy.md",
            "section": "4.1 Casual leave carry-forward"
        }
    ]

    result = validator.validate(
        citations,
        retrieved_results
    )

    print("\nTest 1 - Valid citation")
    print(result)

    assert len(result) == 1


    citations = [
        {
            "document": "leave-policy.md",
            "section": "9. Fake section"
        }
    ]

    result = validator.validate(
        citations,
        retrieved_results
    )

    print("\nTest 2 - Invalid section")
    print(result)

    assert len(result) == 0


    citations = [
        {
            "document": "fake-policy.md",
            "section": "4.1 Casual leave carry-forward"
        }
    ]

    result = validator.validate(
        citations,
        retrieved_results
    )

    print("\nTest 3 - Invalid document")
    print(result)

    assert len(result) == 0

   
    citations = [
        {
            "document": "leave-policy.md",
            "section": "4.1 Casual leave carry-forward"
        },
        {
            "document": "fake-policy.md",
            "section": "Fake section"
        }
    ]

    result = validator.validate(
        citations,
        retrieved_results
    )

    print("\nTest 4 - Mixed citations")
    print(result)

    assert len(result) == 1

    print("\n===================================")
    print("All citation validator tests passed")
    print("===================================")


if __name__ == "__main__":
    main()
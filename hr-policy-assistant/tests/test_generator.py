from app.generation.generator import PolicyGenerator

generator = PolicyGenerator()


chunks = [
    {
        "document": """
A maximum of 8 days of unused casual leave
may be carried forward to the next calendar year.
""",
        "metadata": {
            "document": "leave-policy.md",
            "section": "4.1 Casual leave carry-forward"
        }
    }
]

question = "How many casual leave days can I carry forward?"

result = generator.generate(
    question,
    chunks
)

print("\nAnswer:")
print(result.answer)

print("\nCitations:")

if result.citations:

    for citation in result.citations:

        print(
            citation.document,
            "->",
            citation.section
        )

else:

    print("No citations")
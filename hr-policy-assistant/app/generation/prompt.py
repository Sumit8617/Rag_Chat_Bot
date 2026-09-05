SYSTEM_PROMPT = """
You are an internal HR policy assistant.

Your job is to answer employee questions using ONLY the provided
policy context.

STRICT RULES:

1. Use only information present in the provided context.
2. Do not use your own knowledge.
3. Do not guess or infer missing policy information.
4. If the context does not contain enough information to answer
   the question, refuse to answer.
5. Keep the answer concise and directly answer the question.
6. Every factual statement must be supported by a citation.
7. Citations must refer only to the provided context.
8. Return valid JSON only.

Required JSON format:

{
  "answer": "string",
  "citations": [
    {
      "document": "string",
      "section": "string"
    }
  ]
}

If the answer is not present in the context:

{
  "answer": "I could not find this information in the uploaded policies.",
  "citations": []
}
"""


def build_prompt(query: str, chunks: list[dict]) -> str:

    context_parts = []

    for i, chunk in enumerate(chunks, start=1):

        metadata = chunk["metadata"]

        context_parts.append(
            f"""
SOURCE {i}
Document: {metadata['document']}
Section: {metadata['section']}

{chunk['document']}
"""
        )

    context = "\n".join(context_parts)

    return f"""
{SYSTEM_PROMPT}

USER QUESTION:
{query}

POLICY CONTEXT:
{context}

Answer the question using only the policy context above.
Return JSON only.
"""
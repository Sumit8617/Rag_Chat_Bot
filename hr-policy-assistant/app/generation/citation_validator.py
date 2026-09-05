class CitationValidator:

    def validate(
        self,
        citations: list[dict],
        retrieved_results: list[dict]
    ) -> list[dict]:
        """
        Validate that every citation returned by the LLM
        points to a document and section that actually
        exist in the retrieved context.
        """

        if not citations:
            return []

        # Build a set of valid document + section combinations
        valid_sources = set()

        for result in retrieved_results:
            metadata = result.get("metadata", {})

            document = metadata.get("document")
            section = metadata.get("section")

            if document and section:
                valid_sources.add(
                    (document.strip(), section.strip())
                )

        validated = []

        for citation in citations:
            document = citation.get("document", "").strip()
            section = citation.get("section", "").strip()

            if not document or not section:
                continue

            if (document, section) in valid_sources:
                validated.append({
                    "document": document,
                    "section": section
                })

        return validated
import re


class CitationValidator:
    @staticmethod
    def _normalize_doc(doc: str) -> str:
        s = doc.strip().lower()
        if s.endswith(".md"):
            s = s[:-3]
        elif s.endswith(".txt"):
            s = s[:-4]
        return re.sub(r"[\s\-_]+", " ", s).strip()

    @staticmethod
    def _normalize_sec(sec: str) -> str:
        s = sec.strip().lower()
        s = re.sub(r"^section\s+", "", s)
        return re.sub(r"\s+", " ", s).strip()

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
        if not citations or not retrieved_results:
            return []

        # Map normalized keys to canonical (document, section) metadata
        valid_lookup = {}
        for result in retrieved_results:
            metadata = result.get("metadata", {})
            doc = metadata.get("document")
            sec = metadata.get("section")
            if doc and sec:
                canonical_doc = doc.strip()
                canonical_sec = sec.strip()
                norm_doc = self._normalize_doc(canonical_doc)
                norm_sec = self._normalize_sec(canonical_sec)

                valid_lookup[(norm_doc, norm_sec)] = {
                    "document": canonical_doc,
                    "section": canonical_sec
                }
                # Also index by section alone for resilient lookup
                valid_lookup[norm_sec] = {
                    "document": canonical_doc,
                    "section": canonical_sec
                }

        validated = []
        seen = set()

        for citation in citations:
            raw_doc = citation.get("document", "").strip()
            raw_sec = citation.get("section", "").strip()

            if not raw_sec:
                continue

            norm_doc = self._normalize_doc(raw_doc)
            norm_sec = self._normalize_sec(raw_sec)

            matched_source = None
            if (norm_doc, norm_sec) in valid_lookup:
                matched_source = valid_lookup[(norm_doc, norm_sec)]
            elif not raw_doc and norm_sec in valid_lookup:
                matched_source = valid_lookup[norm_sec]

            if matched_source:
                key = (matched_source["document"], matched_source["section"])
                if key not in seen:
                    seen.add(key)
                    validated.append(matched_source)

        return validated

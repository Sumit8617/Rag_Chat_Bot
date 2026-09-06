# DESIGN.md — HR Policy Assistant

## 1. Architecture

The system has two independent pipelines that share a vector store:
**ingestion** (admin uploads a policy → it becomes searchable) and
**query** (an employee asks a question → they get a grounded, cited
answer or a safe refusal).

```
INGESTION
  Admin upload (.md/.txt)
        │
        ▼
  loader.py           — read file, validate extension + UTF-8
        │
        ▼
  chunker.py           — split into section-aware, table-aware chunks
        │
        ▼
  indexer.py            — delete old chunks for this filename (if any),
        │                  embed new chunks, upsert into Chroma
        ▼
  ChromaDB (persistent, ./chroma_db)


QUERY
  Employee question
        │
        ▼
  HybridRetriever        — embed query; vector search (Chroma) +
        │                   keyword search (all chunks); fuse via RRF;
        │                   boost exact "section X.Y" matches
        ▼
  GroundingChecker        — refuse here if evidence is weak
        │ (grounded)
        ▼
  PolicyGenerator          — Gemini call, strict JSON-only prompt
        │
        ▼
  CitationValidator         — strip any citation not actually retrieved
        │
        ▼
  Refuse again if citations ended up empty, else return
        │
        ▼
  { "answer": "...", "citations": [{"document","section"}, ...] }
```

**Components and responsibilities:**

| Component | Responsibility |
|---|---|
| `IngestionService` | Orchestrates upload → load → chunk → index; the only entry point that touches disk for policy files |
| `QAService` | Orchestrates ask → retrieve → ground → generate → validate; the only entry point for answering |
| `HybridRetriever` | Combines two independent signals (semantic + keyword) into one ranking |
| `GroundingChecker` | The first anti-hallucination gate — decides whether retrieval evidence is strong enough to even attempt an answer |
| `PolicyGenerator` | Talks to Gemini; enforces JSON-only output; handles retries/backoff for transient API errors |
| `CitationValidator` | The second anti-hallucination gate — a hard backstop that doesn't trust the LLM's citations, only what was actually retrieved |

**Why two independently-owned services (`QAService`/`IngestionService`)
rather than one monolithic service:** upload and query have different
failure modes, different request shapes, and are used by different
actors (admin vs. employee). Keeping them separate means a failure in
one doesn't need special-casing in the other, and each is small enough
to read end-to-end in under a minute.

---

## 2. Chunking & retrieval

### Chunking strategy

Documents are split on **Markdown headings** (`#` through `######`),
not on a fixed character window. This was a deliberate choice over
"default tutorial" fixed-size chunking: HR policies are already
organized into numbered sections (e.g. `4.1 Casual leave
carry-forward`), and those section boundaries are exactly the unit an
employee references ("what does section 4.1 say?") and exactly the
unit a citation should point to. Splitting on headings means chunk
boundaries and citation boundaries are the same thing.

If a section is small enough (≤1200 chars), it becomes one chunk. If
it's larger, it's split into paragraph-level blocks with 150 characters
of overlap carried forward for continuity — **except** that a Markdown
table is treated as one atomic, unsplittable block, even if that makes
the resulting chunk larger than the 1200-char target. This was verified
directly: a synthetic table forced past the size limit stayed fully
intact in a single chunk, while the paragraph before it was correctly
split off. Without this rule, a row like "Standard tier | ... | Not
covered" could be separated from its header row, silently breaking any
question about that specific cell.

### Metadata stored per chunk

- `document` — source filename (used for citations and for
  delete-then-reindex on re-upload)
- `section` — the heading text the chunk came from (used for citations
  and for exact-section-number matching)

Deliberately minimal. No page numbers (source is Markdown, not
paginated), no per-chunk timestamps (not needed for this assignment's
scope — see Trade-offs).

### Retrieval: hybrid, not vector-only

Two retrieval signals run independently, then get fused:

1. **Vector search** (Chroma kNN over embeddings) — good at "what's
   this question *about*" even with different wording than the policy
   text.
2. **Keyword search** (custom token-overlap scorer) — good at exact
   matches vector search is unreliable for: clause numbers like `4.1`,
   abbreviations like `CL`/`SL`/`PL`. The tokenizer specifically
   preserves dotted section numbers as single tokens so `4.1` isn't
   silently mangled into `4` and `1`.

They're combined with **Reciprocal Rank Fusion** (weights: 0.7 vector /
0.3 keyword, k=60) rather than a raw score blend, because vector
distances and keyword-overlap fractions live on incomparable scales —
RRF sidesteps that by only using each method's *rank*, not its raw
score. On top of the fused score, a chunk gets a further +0.02 boost if
the query explicitly names a section number that the chunk's section
heading starts with — this was verified to correctly promote the exact
section a user asks about, even if it wouldn't otherwise be the top
semantic match.

### Top-k

`TOP_K=5` chunks are sent to the LLM by default. The vector stage
over-fetches `max(top_k*2, 10)` candidates before fusion, so the fused
ranking has more to work with than the final k — this matters because
a chunk that's, say, semantically 6th-best but keyword-exact could
still legitimately end up in the top 5 after fusion.

---

## 3. Grounding

Hallucination is prevented by **three independent layers**, not by the
prompt alone:

1. **Prompt contract.** The system prompt explicitly forbids using
   outside knowledge, requires every statement to have a citation, and
   forces strict JSON output.
2. **Pre-generation grounding gate** (`GroundingChecker`). Before the
   LLM is even called, retrieval evidence is checked: grounded if the
   top result exactly matched a named section, OR if its vector
   distance is ≤ 0.75 AND its RRF score is ≥ 0.015. If neither holds,
   the system refuses immediately — the LLM is never invoked, so it
   can't be tempted to fill the gap with general knowledge.
3. **Post-generation citation validation** (`CitationValidator`). Even
   if the LLM does answer, every citation it returns is checked against
   the actual `(document, section)` pairs that were retrieved for this
   query. Any citation not in that set is dropped. If dropping leaves
   zero valid citations, the system refuses — an answer with no real
   citation left behind is treated the same as no answer.

**What happens when retrieval is weak:** the standard refusal is
returned without ever reaching the LLM:

```json
{
  "answer": "I don't have enough information in the uploaded policies to answer this question. Please contact HR.",
  "citations": []
}
```

This two-gate design (before *and* after generation) means a single
point of failure — a bad threshold, or the LLM hallucinating a
plausible-looking source — isn't enough to leak an ungrounded answer.

---

## 4. Schema & APIs

```
POST /documents  (multipart file)   →  { document: str, chunks_indexed: int }
POST /ask        { question: str }  →  { answer: str, citations: [{document, section}] }
GET  /health                        →  { status: "ok" }
```

`Citation` is a single shared Pydantic model (`{document: str, section:
str}`) used both as the LLM's structured-output contract
(`AnswerResponse`) and the API's response contract (`AskResponse`) —
one schema, not two independently-drifting ones. `AskRequest.question`
has `min_length=1`, so a literally empty string is rejected by FastAPI
at the request boundary (422) before it reaches any business logic;
whitespace-only strings pass that check but are caught by an explicit
`.strip()` check inside `QAService.ask()`.

**Why this shape:** `citations` is a list of `{document, section}`
pairs rather than free-text source strings, because it needs to be
independently *checked* (see Section 3) — a checkable schema has to be
structured, not prose.

---

## 5. Trade-offs

**1. Local embeddings vs. a hosted embedding API.**
Chosen: local `sentence-transformers`. Rejected: a hosted embedding
API (e.g. Gemini's embedding endpoint). Local wins here because it's
free at any volume, keeps HR policy text off a third-party embedding
endpoint entirely, and removes a second point of external-API failure.
Cost: a one-time model download and a few hundred MB of disk, and
slightly slower cold-start than an API call.

**2. `local_files_only=True` vs. auto-download-on-first-use.**
Chosen: `local_files_only=True`, with an explicit one-time download
step documented in the README. Rejected: letting `sentence-transformers`
silently reach out to Hugging Face on first run. Auto-download is
friendlier for a from-scratch clone, but for a system handling
internal HR data, an unexpected outbound network call on first request
is the wrong default — better to fail loudly and predictably if the
model isn't there, and require an explicit, visible setup step.

**3. Synchronous vs. asynchronous ingestion.**
Chosen: synchronous — `POST /documents` blocks until chunking and
embedding finish. Rejected: a background job queue. For a handful of
Markdown policy files (the assignment's actual scope), synchronous
ingestion completes in well under a second and adds no operational
complexity (no queue, no worker process, no job-status endpoint to
build). This would need to change if uploads were large PDFs at scale
— noted below.

**4. ChromaDB vs. pgvector/a managed vector DB.**
Chosen: Chroma, file-backed, zero external services. Rejected:
pgvector (would need a running Postgres instance) or a managed vector
DB (network dependency, and out of scope per the assignment's own
"don't build production infra" guidance). Chroma is the right size for
a demo-scale corpus and needs no setup beyond `pip install`.

---

## 6. If I had two more weeks

1. **Harden the app-startup coupling further.** The `/health`,
   `/documents`, and `/ask` construction issue was already fixed (lazy
   service construction — see commit history), but I'd add a
   `/health/deep` endpoint that actually checks Gemini key validity and
   embedding-model availability, so operators can distinguish "app is
   up" from "app is fully functional" without hitting `/ask`.
2. **Expand the evaluation harness.** The current `evaluation_questions.json`
   has 8 questions. I'd grow this to 30–50, covering more paraphrases of
   the same underlying question, to get a statistically meaningful
   retrieval-hit-rate and refusal-rate rather than an anecdotal one, and
   use it to actually tune the grounding thresholds rather than setting
   them by inspection.
3. **PDF and richer table extraction.** Currently only `.md`/`.txt` are
   supported. Real HR policies often live in Word/PDF with more complex
   tables (merged cells, multi-page tables) than Markdown pipe-tables.
4. **Async ingestion** for large uploads, with a job-status endpoint,
   once documents are large enough that synchronous blocking becomes a
   real UX problem.
5. **Minimal auth.** Even a hardcoded `X-Role: admin` header check on
   `/documents` — the assignment explicitly says a hardcoded flag is
   acceptable, and right now there isn't even that.
6. **Citation entailment checking**, not just citation *existence*
   checking — verify the specific claim in the answer is actually
   supported by the cited chunk's text, not just that the cited
   `(document, section)` pair was among the retrieved chunks.
7. **Convert the print-based debug scripts** (`test_hybrid.py`,
   `test_chunker.py`, etc.) into real `pytest` tests with assertions, so
   regressions are caught automatically rather than requiring a human
   to eyeball console output.
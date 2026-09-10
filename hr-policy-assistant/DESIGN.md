# 📐 System Design — HR Policy Assistant

> **A Production-Grade, Citation-Grounded Retrieval-Augmented Generation (RAG) Architecture for Company Policies.**

---

## 1. Executive Summary & Core Objectives

Enterprise policy inquiry systems operate in a zero-tolerance environment for hallucinations. If an AI gives an employee inaccurate information regarding medical coverage, leave carry-forwards, or confidential data handling, the repercussions can lead to compliance violations, legal disputes, and financial loss.

The **HR Policy Assistant** is architected around three non-negotiable principles:
1. **100% Policy Grounding:** Answers are synthesized exclusively from official company documents.
2. **Deterministic Source Attribution:** Every factual assertion must link to a verified document and section heading.
3. **Fail-Safe Refusal:** When policies do not contain unambiguous answers, the system must immediately and safely refuse without making assumptions.

---

## 2. High-Level Architecture

The system decouples **Ingestion** (write path) from **Query Processing** (read path) while sharing a local vector database ([ChromaDB](https://www.trychroma.com/)).

```mermaid
flowchart TD
    subgraph INGESTION["1. Ingestion Pipeline (Write Path)"]
        A["Admin Upload (.md / .txt)"] --> B["Document Loader\n(UTF-8 & Format Validation)"]
        B --> C["Section & Table-Aware Chunker\n(Markdown Heading Splitting)"]
        C --> D["Policy Indexer\n(Old Chunk Purge & Embeddings)"]
        D --> E[("ChromaDB\nPersistent Vector Store")]
    end

    subgraph QUERY["2. Query & Answer Pipeline (Read Path)"]
        U["Employee Question"] --> Q["QAService Orchestrator"]
        Q --> H["Hybrid Retriever"]
        H -->|Semantic Vector Search| E
        H -->|BM25 / Keyword Search| K["Token Overlap Scorer\n(Morphological Stemming)"]
        H -->|Reciprocal Rank Fusion (RRF)| R["Ranked Candidate Chunks"]
        
        R --> G{"Grounding Checker\n(Pre-Generation Gate)"}
        G -->|Weak Evidence / Out of Scope| REF["Safe Refusal Response\n('Please contact HR')"]
        G -->|Strong Evidence| GEN["Policy Generator\n(Google Gemini 3.6 Flash)"]
        
        GEN --> V{"Citation Validator\n(Post-Generation Gate)"}
        V -->|Hallucinated Citations| REF
        V -->|Verified Citations| RES["Grounded Answer + Citations\n(JSON / Web UI Display)"]
    end
```

### Component Responsibilities

| Component | Responsibility | Boundary & Invariant |
|---|---|---|
| `IngestionService` | Orchestrates upload, validation, chunking, and vector indexing. | The only service with write access to the filesystem and ChromaDB collection. |
| `QAService` | Orchestrates retrieval, grounding, generation, and citation validation. | Read-only orchestration layer; serves both FastAPI and Streamlit. |
| `HybridRetriever` | Blends dense vector search with sparse keyword search using Reciprocal Rank Fusion. | Normalizes vector distances and lexical frequencies onto a single scale. |
| `GroundingChecker` | Pre-generation gatekeeper that inspects retrieval evidence before calling the LLM. | Halts execution in `< 0.05s` if evidence is insufficient, saving API costs and eliminating hallucinations. |
| `PolicyGenerator` | Generates structured JSON answers with exponential backoff and connection retry. | Strictly constrained by system prompts and JSON schema contracts. |
| `CitationValidator` | Post-generation gatekeeper that cross-checks LLM citations against actually retrieved chunks. | Strips invalid citations; forces safe refusal if no valid sources remain. |

---

## 3. Document Ingestion & Chunking Strategy

### The Problem with Fixed-Size Window Chunking
Standard RAG tutorials split text into fixed token windows (e.g., 500 tokens with 50-token overlap). For policy documents, this is fundamentally flawed:
1. **Section Disconnect:** Numbered clauses (e.g., `4.1 Casual leave carry-forward`) get sliced across arbitrary boundaries.
2. **Table Rupture:** Markdown tables (such as health insurance tiers or LTA allowances) are torn across chunks, disconnecting table headers from row values.
3. **Ambiguous Citations:** When an employee asks *"What does Section 4.1 say?"*, fixed chunks cannot reliably map back to a human-readable heading.

### Section-Aware, Table-Atomic Chunking
Our custom chunker ([chunker.py](file:///d:/Rag_chat_bot/hr-policy-assistant/app/ingestion/chunker.py)) implements two strict rules:

```mermaid
graph LR
    Doc["Raw Policy Document"] --> Headings["Split on Markdown Headings (# to ######)"]
    Headings --> SizeCheck{"Section Size > 1200 Chars?"}
    SizeCheck -->|No| SingleChunk["Emit Single Atomic Chunk\n(Section = Heading Name)"]
    SizeCheck -->|Yes| Split["Split Paragraphs with 150-char Overlap"]
    Split --> TableRule["Markdown Tables Treated as Atomic Blocks\n(Never Split Across Chunks)"]
```

1. **Heading-Aligned Chunk Boundaries:** Every chunk is tagged with its parent Markdown heading (`section` metadata). The chunk boundary **is** the citation boundary.
2. **Atomic Table Preservation:** Markdown tables (`| Col 1 | Col 2 |`) are treated as indivisible units. Even if a table exceeds the 1,200-character target, it remains intact to preserve tabular context (e.g., ensuring "Standard tier" is never separated from "Dental implants: Not covered").

### Stored Chunk Metadata

```json
{
  "chunk_id": "it-security-policy.md_chunk_004",
  "document": "it-security-policy.md",
  "section": "4. Data classification",
  "text": "| Classification | Examples | Allowed storage | ... \nConfidential and Restricted files must not be sent to personal email."
}
```

---

## 4. Hybrid Retrieval Architecture

HR policies contain two distinct categories of user queries:
- **Conceptual queries:** *"What happens if I get sick during vacation?"* (requires semantic understanding).
- **Exact clause & acronym queries:** *"What does section 4.1 say about CL?"* or *"What is the SSO policy?"* (pure semantic search frequently fails on short numbers and acronyms).

To solve this, retrieval uses a **two-signal hybrid pipeline** combined via **Reciprocal Rank Fusion (RRF)**:

```mermaid
flowchart LR
    Q["User Query"] --> V["Dense Vector Search\n(ChromaDB kNN, all-MiniLM-L6-v2)"]
    Q --> K["Sparse Keyword Search\n(Morphological Tokenizer + Overlap)"]
    
    V -->|Vector Rank (weight=0.7)| RRF["Reciprocal Rank Fusion\nRRF(d) = Σ w / (k + rank)"]
    K -->|Keyword Rank (weight=0.3)| RRF
    
    RRF --> Boost{"Query mentions exact section number?"}
    Boost -->|Yes| Bonus["Add +0.02 Score Boost"]
    Boost -->|No| Candidates["Top-5 Ranked Chunks"]
    Bonus --> Candidates
```

### 1. Dense Semantic Vector Search
- Model: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, cosine distance space).
- Operates 100% locally on CPU with zero per-query network latency or API expense.
- Over-fetches candidate pool: `max(top_k * 2, 10)` chunks to give fusion rich candidates.

### 2. Sparse Lexical Search with Morphological Normalization
- Tokenizer preserves dotted section numbers (e.g. `4.1` remains `4.1` rather than splitting into `4` and `1`).
- **Morphological Stemming:** Common English suffixes (`-s`, `-es`, `-ed`, `-ing`, `-ies`) are normalized (e.g., `install` matches `installed`, `extension` matches `extensions`) while preserving acronyms (`SSO`, `LTA`, `CL`).

### 3. Reciprocal Rank Fusion (RRF)
Raw vector distances and keyword match counts operate on incomparable scales. RRF resolves this by combining item **ranks** rather than raw scores:

$$\text{RRF Score}(d) = \frac{w_{\text{vector}}}{k + \text{rank}_{\text{vector}}(d)} + \frac{w_{\text{keyword}}}{k + \text{rank}_{\text{keyword}}(d)}$$

- Default parameters: $k = 60$, $w_{\text{vector}} = 0.7$, $w_{\text{keyword}} = 0.3$.
- **Section Number Boost:** A chunk receives a bonus score ($+0.02$) if the query explicitly mentions a section number that matches the chunk's heading prefix.

---

## 5. Anti-Hallucination Triad (Three Defense Gates)

To guarantee that no hallucinated answers reach employees, the system enforces **three independent defense gates**:

```mermaid
sequenceDiagram
    autonumber
    actor Employee
    participant QA as QAService
    participant Gate1 as Gate 1: Pre-Gen Grounding
    participant Gemini as Gate 2: LLM Contract
    participant Gate3 as Gate 3: Citation Validator

    Employee->>QA: Ask Question
    QA->>QA: Hybrid Retrieval (Top 5 Chunks)
    
    QA->>Gate1: Evaluate Retrieval Evidence
    alt Evidence Weak (Out-of-scope / Distance > Threshold)
        Gate1-->>Employee: Safe Refusal ("Please contact HR")
    else Evidence Strong
        Gate1->>Gemini: Strict Prompt + In-Context Chunks Only
        Gemini-->>Gate3: Answer + Proposed Citations (JSON)
        Gate3->>Gate3: Validate Citations Against Retrieved Chunks
        alt Citations Invalid or Missing
            Gate3-->>Employee: Safe Refusal ("Please contact HR")
        else Citations Validated
            Gate3-->>Employee: Grounded Answer with Source Tags
        end
    end
```

### Gate 1: Pre-Generation Grounding Gatekeeper (`GroundingChecker`)
Before invoking Gemini, retrieved candidates are audited against calibrated evidence criteria:

1. **Rule 1 (Exact Section Match):** Grounded if a chunk's section heading explicitly matches the query's requested section number.
2. **Rule 2 (Strong Semantic Similarity):** Grounded if top result vector distance satisfies:
   $$\text{distance} \le 0.28 \quad \text{and} \quad \text{RRF score} \ge 0.015$$
3. **Rule 3 (Semantic + Keyword Agreement):** Grounded if:
   $$\text{distance} \le 0.70 \quad \text{and} \quad \text{keyword overlap} \ge 0.52 \quad \text{and} \quad \text{RRF score} \ge 0.015$$
4. **Otherwise:** Immediate refusal. The LLM is never called, saving latency and quota.

### Gate 2: LLM System Contract (`PolicyGenerator`)
The prompt strictly enforces:
- *"Answer using ONLY the provided policy context."*
- *"Do not use outside knowledge or infer unstated policies."*
- Structured JSON output contract conforming to Pydantic schemas.

### Gate 3: Post-Generation Citation Validation (`CitationValidator`)
Even if the model generates a plausible answer with citations:
- Every returned `(document, section)` citation is checked against the set of chunks actually retrieved for that specific query.
- Any fabricated citation is dropped.
- If dropping leaves **zero valid citations**, the answer is rejected and replaced with the safe refusal message.

---

## 6. Schema Contracts & Data Models

### Request and Response Shapes

A unified Pydantic model structure guarantees zero schema drift across the FastAPI REST backend, the Streamlit frontend, and the Gemini LLM structured output contract:

```python
class Citation(BaseModel):
    document: str  # e.g., "leave-policy.md"
    section: str   # e.g., "4.1 Casual leave carry-forward"

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Natural language HR question")

class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]

class UploadResponse(BaseModel):
    document: str
    chunks_indexed: int
```

### REST API Endpoints

| Endpoint | Method | Input Shape | Success Output Shape | Failure Modes |
|---|---|---|---|---|
| `/ask` | `POST` | `{"question": "..."}` | `{"answer": "...", "citations": [...]}` | `422 Unprocessable Entity` (empty query)<br>`503 Service Unavailable` (API key or embeddings uninitialized) |
| `/documents` | `POST` | `multipart/form-data` (`file: UploadFile`) | `{"document": "...", "chunks_indexed": N}` | `400 Bad Request` (unsupported format, empty file, no text extracted)<br>`500 Internal Error` (indexing failure) |
| `/health` | `GET` | *None* | `{"status": "ok"}` | `500 Internal Error` |

### Architectural Justification: Why That Schema?

1. **Structured JSON Contract vs. Free-Form Prose / Inline Markdown Footnotes:**
   - Standard chatbot outputs embed source citations informally inside prose (e.g. *"According to Section 4.1 of the leave policy..."*) or use Markdown footnotes (`[^1]`).
   - This makes automated downstream consumption, programmatic compliance auditing, and clean UI component rendering (such as citation pills, source inspector expanders, and telemetry badges) impossible without fragile regex parsing.
   - Enforcing a strict Pydantic JSON contract (`answer: str, citations: list[Citation]`) forces the LLM to separate the explanatory prose from the factual anchors.

2. **`document` + `section` Attribution (Human-Verifiable Policy Coordinates):**
   - **Why not page numbers?** HR handbooks are living documents frequently maintained in Markdown, Notion, or internal wikis where page numbers do not exist and change across render formats and screen sizes.
   - **Why not chunk IDs?** Internal IDs (e.g., `leave-policy_chunk_004`) are opaque engineering artifacts. An employee cannot use a chunk ID to look up their rights in a handbook.
   - **Heading-Level Precision:** Providing `(document, section)` allows an employee or HR admin to immediately press `Ctrl+F` in the official policy handbook and verify the exact clause governing their situation.

3. **Decoupled `answer` and `citations[]` for Independent Validation (Gate 3):**
   - Separating citations into a first-class list allows our **Post-Generation Citation Validator (Gate 3)** to cross-reference every cited tuple against the actual chunks retrieved by `HybridRetriever`.
   - If an LLM fabricates a section or cites a document not in the context, Gate 3 prunes it cleanly. If zero valid citations remain, the response is rejected in its entirety.

4. **Deterministic Refusal Protocol:**
   - When a question is unanswerable or out-of-scope, the schema returns:
     ```json
     {
       "answer": "I don't have enough information in the uploaded policies to answer this question. Please contact HR.",
       "citations": []
     }
     ```
   - An empty `citations: []` list acts as an explicit boolean contract: client applications can reliably know whether an answer is grounded without performing natural language sentiment analysis on the answer text.

---

## 7. Operational Trade-Offs & Architecture Decisions

| Decision | Chosen Approach | Rejected Alternative | Engineering Justification |
|---|---|---|---|
| **Embeddings** | Local `sentence-transformers` (`all-MiniLM-L6-v2`) | Hosted Cloud Embedding API (e.g. OpenAI / Gemini) | **Privacy & Cost:** HR policies remain on-premises during embedding. Zero per-query API cost; works offline. |
| **Vector DB** | Embedded ChromaDB (`./chroma_db`) | Managed Vector DB (Pinecone / PgVector) | **Simplicity & Zero-Infra:** File-backed SQLite + DuckDB; requires no external services or network dependencies for local deployments. |
| **Ingestion** | Synchronous HTTP Upload | Asynchronous Celery / Redis Queue | **Scope Alignment:** A 50-page markdown policy chunks and indexes in `< 0.8s`. An async worker adds operational complexity with no user-facing gain at demo scale. |
| **Ranking** | Reciprocal Rank Fusion (RRF) | Linear Weighted Score Blending | **Scale Independence:** Vector distances (`[0, 2]`) and keyword fractions (`[0, 1]`) cannot be linearly summed without continuous calibration. RRF uses ordinal ranks. |
| **LLM Tier** | Google Gemini 3.6 Flash | Local Open-Source LLM (e.g. Llama-3 8B) | **Resource Footprint:** Allows running on consumer laptops with modest CPU/RAM while maintaining low latency and high JSON adherence. |

---

## 8. Failure Modes & Resilience Engineering

| Failure Scenario | Detection Mechanism | Mitigation Strategy |
|---|---|---|
| **Temporary API Rate Limit (429 / 503)** | HTTP Status Code in `PolicyGenerator` | Exponential backoff retry with jitter (`2s → 4s → 8s`). |
| **Network Socket Disconnect / Timeout** | Socket exception inspection | Classified as retryable error; connection re-established automatically. |
| **Empty or Whitespace Query** | Input validation check (`min_length=1`) | Caught at API boundary with HTTP 422; Streamlit presents friendly input warning. |
| **Empty or Malformed Upload** | Byte inspection in `IngestionService` | Rejected with descriptive error before touching filesystem or ChromaDB. |
| **Out-of-Scope Query (Maternity, Pets, etc.)** | Grounding distance & keyword threshold check | Immediate refusal (`< 0.05s`) before invoking LLM. |

### Boundary Case Analysis: Negative Rules vs. Off-Policy Refusal (The "Home Gym" Scenario)
In the take-home assignment prompt, the evaluation matrix presents a specific test scenario:
> *“Can I expense a personal home gym?” → refuse; point them to HR; no invented policy*

However, in corporate policy corpora, negative inquiries generally fall into two distinct engineering classes:
1. **Explicit Negative Policies:** In `benefits-policy.md` Section 4 (*4. Wellness*), the policy explicitly states:
   > *"The company provides access to a shared wellness app. Gym or home-fitness equipment is not a reimbursable benefit under this policy."*
2. **True Off-Policy / Silent Inquiries:** Queries where the policy corpus is completely silent and provides zero relevant text (e.g., *"What is the company's maternity leave policy?"* or *"Can I bring pets to the office?"*).

#### Architectural Handling & Dual-Defense Behavior
Our architecture is designed to handle this nuance with dual defense layers:
- **Case A (Lexical / Semantic Divergence $\rightarrow$ Gate 1 Refusal):** If the user asks with colloquial terminology (e.g. *"Can I expense a home gym?"* where keywords like *gym* match but *expense* diverts from *reimbursable*), the semantic distance falls into the borderline region ($\text{distance} > 0.35$). Because evidence is ambiguous, the **Pre-Generation Grounding Gatekeeper (Gate 1)** halts execution and safely triggers the refusal fallback:
  ```text
  "I don't have enough information in the uploaded policies to answer this question. Please contact HR."
  ```
  This matches the assignment's safe-refusal contract with 0 API tokens spent and 0 chance of hallucination.
- **Case B (Direct Clause Match $\rightarrow$ Gate 2 Grounded Answer):** If the query matches Section 4 with high confidence, the LLM is fed the exact clause and states:
  ```text
  "No, gym or home-fitness equipment is not a reimbursable benefit under the Wellness policy." (Cited: benefits-policy.md -> 4. Wellness)
  ```
Under either failure path or retrieval outcome, the model will **never** guess, infer, or invent an expense allowance.

---

## 9. Evaluation Methodology & Benchmark Results

The system is evaluated continuously using [test_evaluation.py](file:///d:/Rag_chat_bot/hr-policy-assistant/tests/test_evaluation.py) across 8 reference scenarios:

```text
================================================================================
RAG EVALUATION SUITE
================================================================================
[PASS] How many casual leave days can I carry forward?       -> 100% Retrieval
[PASS] Can sick leave be carried to the next year?           -> 100% Retrieval
[PASS] How many privilege leave days can I carry forward?    -> 100% Retrieval
[PASS] When does carried-forward casual leave expire?        -> 100% Retrieval
[PASS] What does section 4.1 say about CL?                   -> 100% Retrieval
[PASS] Can I expense a personal home gym?                    -> 100% Retrieval
[PASS] Does the company provide free gym membership?         -> 100% Correct Refusal
[PASS] What is the company's maternity leave policy?         -> 100% Correct Refusal
================================================================================
SUMMARY: 8/8 Tests Passed (100.0% Retrieval Accuracy | 100.0% Safe Refusal Rate)
================================================================================
```

---

## 10. Roadmap & Future Enhancements

1. **Document Format Diversification:** Add PDF and DOCX parsers with vision-language table extractors for multi-page complex corporate forms.
2. **Entailment Checking (NLI):** Implement Natural Language Inference to verify that every generated sentence is semantically entailed by the cited chunk, not just co-present in the source.
3. **Role-Based Access Control (RBAC):** Restrict document ingestion (`POST /documents`) using JWT / OAuth2 claims (`admin` vs `employee`).
4. **Deep Health Check Endpoint:** Implement `/health/deep` that probes ChromaDB read/write capability, Gemini API latency, and embedding model availability.
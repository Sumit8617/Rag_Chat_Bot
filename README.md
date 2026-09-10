# 🏢 HR Policy Assistant

> **An AI-powered HR Assistant that answers employee questions strictly from approved company policies — with exact source citations and zero hallucinated answers.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.63+-FF4B4B.svg)](https://streamlit.io)
[![ChromaDB](https://img.shields.io/badge/Vector_DB-ChromaDB-orange.svg)](https://www.trychroma.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🌟 Table of Contents
- [📖 What is this Project?](#-what-is-this-project)
- [🧠 How It Works (In Plain English)](#-how-it-works-in-plain-english)
- [⚡ Quick Start Guide (Step-by-Step)](#-quick-start-guide-step-by-step)
  - [1. Prerequisites](#1-prerequisites)
  - [2. Clone and Setup Environment](#2-clone-and-setup-environment)
  - [3. Get a Free Gemini API Key](#3-get-a-free-gemini-api-key)
  - [4. Download the Embedding Model (One-Time)](#4-download-the-embedding-model-one-time)
  - [5. Run the Application](#5-run-the-application)
- [💬 Questions You Can Try](#-questions-you-can-try)
- [📤 Admin: Uploading New Policies](#-admin-uploading-new-policies)
- [🛠️ REST API Usage (FastAPI)](#️-rest-api-usage-fastapi)
- [📂 Project Structure](#-project-structure)
- [🧪 Running Tests](#-running-tests)
- [❓ Frequently Asked Questions (FAQ) & Troubleshooting](#-frequently-asked-questions-faq--troubleshooting)

---

## 📖 What is this Project?

When employees have questions about **leave balances, health benefits, travel allowances, or IT security rules**, searching through lengthy HR PDF or Markdown handbooks is time-consuming. 

Normal AI chatbots (like ChatGPT) often **hallucinate** (make up plausible-sounding answers that aren't true). For company policies, an invented answer can cause serious compliance and financial issues.

**HR Policy Assistant solves this problem:**
- ✅ **100% Policy-Grounded:** Answers only using the exact documents uploaded by your company.
- 📄 **Verifiable Citations:** Every answer references the document name and specific clause (e.g., `leave-policy.md → Section 4.1 Casual leave carry-forward`).
- 🛡️ **Safe Refusal:** If a policy doesn't mention something (e.g., *"Does the company have a pet policy?"*), the assistant honestly replies: *"I don't have enough information in the uploaded policies to answer this question. Please contact HR."*
- 💰 **100% Free to Run:** Uses local embeddings (`all-MiniLM-L6-v2`) and the free tier of Google Gemini API.

---

## 🧠 How It Works (In Plain English)

This project uses an industry-standard architecture called **RAG (Retrieval-Augmented Generation)**:

```text
               ┌───────────────────────────────┐
               │    HR Policy Documents        │
               │ (.md / .txt files in storage) │
               └──────────────┬────────────────┘
                              │
                              ▼
                       [1. Ingestion]
        Chunks documents into sections & converts them 
        into mathematical vectors (Embeddings) locally.
                              │
                              ▼
                      [2. ChromaDB]
                 (Local Vector Database)
                              │
                              │
User asks question ───────────┼────────────────────────┐
                              ▼                        ▼
                       [Vector Search]         [Keyword Search]
                       (Understands meaning)   (Matches exact terms/clauses)
                              │                        │
                              └───────────┬────────────┘
                                          ▼
                                [3. Hybrid RRF Fusion]
                           Ranks the best matching chunks
                                          │
                                          ▼
                             [4. Grounding Gatekeeper]
                           Is there enough solid evidence?
                           ├── NO  ──► Safe Refusal (No LLM called)
                           └── YES ──► Send context to Gemini
                                          │
                                          ▼
                                [5. Gemini LLM Answer]
                         Writes concise answer with citations
                                          │
                                          ▼
                              [6. Citation Validator]
                        Validates citations against retrieved text
                                          │
                                          ▼
                             Final Answer with Citations
```

---

## ⚡ Quick Start Guide (Step-by-Step)

Follow these steps to get the assistant running on your computer in under **5 minutes**.

### 1. Prerequisites
- **Python 3.10 or higher** installed on your system.
  - Check with: `python --version`
- **Git** (optional, to clone the code).

---

### 2. Clone and Setup Environment

Open your terminal (**Command Prompt** or **PowerShell** on Windows, or **Terminal** on macOS/Linux):

#### On Windows (PowerShell):
```powershell
# 1. Navigate to the project directory
cd D:\Rag_chat_bot\hr-policy-assistant

# 2. Allow running local scripts in PowerShell (if needed)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 3. Create a virtual environment named 'venv'
python -m venv venv

# 4. Activate the virtual environment
.\venv\Scripts\Activate.ps1

# 5. Install the required packages
pip install -r requirements.txt
```

#### On macOS / Linux:
```bash
# 1. Navigate to the project directory
cd hr-policy-assistant

# 2. Create a virtual environment named 'venv'
python3 -m venv venv

# 3. Activate the virtual environment
source venv/bin/activate

# 4. Install the required packages
pip install -r requirements.txt
```

---

### 3. Get a Free Gemini API Key

The assistant uses Google's **Gemini 3.6 Flash** to turn policy excerpts into friendly answers. Getting a key is free and takes 30 seconds:

1. Go to [Google AI Studio](https://aistudio.google.com/apikey).
2. Sign in with your Google account.
3. Click **Create API Key**.
4. Copy the generated key.

Now, configure your environment file:
1. In the project folder, copy the example file:
   - **Windows:** `copy .env.example .env`
   - **macOS / Linux:** `cp .env.example .env`
2. Open `.env` in any text editor (VS Code, Notepad, etc.).
3. Paste your key:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   GEMINI_MODEL=gemini-3.6-flash
   ```

---

### 4. Download the Embedding Model (One-Time)

The assistant uses a lightweight AI model (`all-MiniLM-L6-v2`) to turn text into vectors. It runs completely offline on your own machine. Download it once:

```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```
*(This downloads ~90 MB to your local cache. You will never need to download it again.)*

---

### 5. Run the Application

You have two ways to run the project:

### Option A: Web Chat Interface (Streamlit) — **Recommended!** 🌟

Run the following command in your terminal:
```bash
streamlit run streamlit_app.py
```

Your browser will open automatically at:
👉 **`http://localhost:8501`**

Here you can:
- Chat with the AI directly in a beautiful modern interface.
- View verified citations and inspect exact retrieved text snippets.
- Upload new HR policies in real-time from the sidebar!
- Export your conversation transcript to Markdown.

---

### Option B: FastAPI Backend Server (For Developers)

If you want to integrate this with another application or mobile app:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- **Health check:** Visit `http://127.0.0.1:8000/health`
- **Interactive API Documentation:** Visit `http://127.0.0.1:8000/docs` to test endpoints directly from your browser!

---

## 💬 Questions You Can Try

The assistant comes pre-loaded with three sample policies (`leave-policy.md`, `benefits-policy.md`, `it-security-policy.md`).

Try asking these questions in the chat:

| Type | Question to Try | Expected Behavior |
|---|---|---|
| 🏖️ **Leave Rules** | *"How many casual leaves can I carry forward to next year?"* | Answers **8 days**, citing `leave-policy.md → Section 4.1`. |
| 🏥 **Health Benefits** | *"Does the Standard health tier cover dental implants?"* | Answers **No, dental implants are not covered under Standard**, citing `benefits-policy.md → Section 2`. |
| 🔒 **IT Security** | *"Can I send confidential company files to my personal Gmail?"* | Answers **No, Confidential and Restricted files must not be sent to personal email**, citing `it-security-policy.md → Section 4`. |
| 💻 **Software Policy** | *"Can I install any browser extension I want?"* | Answers that **only approved software is allowed and extensions reading page content require InfoSec review**, citing `it-security-policy.md → Section 5`. |
| ❌ **Off-Policy (Refusal)** | *"What is the company's maternity leave policy?"* | Safely refuses: *"I don't have enough information in the uploaded policies to answer this question. Please contact HR."* |
| ❌ **Random / Out-of-Scope** | *"Can I bring my pet iguana to the office?"* | Safely refuses immediately without making up a policy. |

---

## 📤 Admin: Uploading New Policies

You can add new company policies at any time without restarting the application!

### Via the Web Interface (Streamlit):
1. Open the app (`http://localhost:8501`).
2. Look at the left sidebar under **Admin: Upload Policy**.
3. Drag and drop any Markdown (`.md`) or text (`.txt`) file (for example: `remote-work-office-policy.md`).
4. Click **📥 Ingest & Index Document**.
5. The policy is chunked, embedded, and immediately searchable!

### Via REST API:
```bash
curl -X POST "http://127.0.0.1:8000/documents" \
  -F "file=@data/policies/remote-work-office-policy.md"
```

---

## 🛠️ REST API Usage (FastAPI)

You can send standard JSON requests to the API:

### Ask a Question (`POST /ask`):

#### PowerShell:
```powershell
$body = @{ question = "How many casual leave days can I carry forward?" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/ask" -Method Post -ContentType "application/json" -Body $body
```

#### cURL (Bash):
```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many casual leave days can I carry forward?"}'
```

#### Sample Response:
```json
{
  "answer": "A maximum of 8 days of unused casual leave may be carried forward to the next calendar year.",
  "citations": [
    {
      "document": "leave-policy.md",
      "section": "4.1 Casual leave carry-forward"
    }
  ]
}
```

---

## 📂 Project Structure

```text
hr-policy-assistant/
│
├── app/
│   ├── config.py                 # Application settings & environment variables
│   ├── main.py                   # FastAPI REST server & API routes (/ask, /documents)
│   │
│   ├── generation/               # LLM Generation & Guardrails
│   │   ├── generator.py          # Communicates with Gemini API with retry logic
│   │   ├── prompt.py             # System prompt construction with strict context rules
│   │   └── citation_validator.py # Verifies LLM citations match actual retrieved chunks
│   │
│   ├── ingestion/                # Document Processing Pipeline
│   │   ├── chunker.py            # Splits policies by Markdown headings and tables
│   │   ├── indexer.py            # Generates embeddings and saves to ChromaDB
│   │   └── loader.py             # Reads and validates .md and .txt files
│   │
│   ├── models/                   # Pydantic data validation schemas
│   │   └── schemas.py            # Request and response models
│   │
│   ├── retrieval/                # Search & Grounding Engine
│   │   ├── embeddings.py         # Local sentence-transformers wrapper
│   │   ├── grounding.py          # Anti-hallucination gatekeeper
│   │   ├── hybrid.py             # Hybrid search (Vector + Keyword via RRF)
│   │   ├── keyword_search.py     # Tokenizer with morphological stemming
│   │   └── vector_store.py       # ChromaDB vector store interface
│   │
│   └── services/                 # Service Layer
│       ├── ingestion_service.py  # Coordinates document upload and indexing
│       ├── qa_service.py         # Coordinates retrieve -> ground -> generate -> validate
│       └── startup.py            # Auto-seeds sample policies on initial launch
│
├── chroma_db/                    # Local Chroma vector database storage
├── data/policies/                # Storage directory for sample HR policies (.md)
├── tests/                        # Automated unit and integration test suite
│   ├── test_citation_validator.py
│   ├── test_evaluation.py        # 8-question evaluation suite (retrieval & refusal)
│   ├── test_grounding.py         # Grounding gatekeeper unit tests
│   └── test_hybrid.py            # Hybrid search test script
│
├── .env.example                  # Template configuration file
├── requirements.txt              # Pinned Python package dependencies
├── streamlit_app.py              # Interactive Streamlit Web UI
└── README.md                     # Documentation (You are here!)
```

---

## 🧪 Running Tests

To verify that all retrieval, grounding, and citation validation tests pass on your machine:

#### 1. Test Citation Validator:
```bash
python tests/test_citation_validator.py
```
*(Validates that invented or fake citations are cleanly rejected.)*

#### 2. Test Grounding Gatekeeper:
```bash
python tests/test_grounding.py
```
*(Validates that strong matches pass and weak/fake questions are refused.)*

#### 3. Test Full Evaluation Suite:
```bash
python tests/test_evaluation.py
```
*(Tests 8 standard questions and confirms 100% retrieval and refusal accuracy.)*

#### 4. Test Comprehensive RAG Pipeline Regression Suite:
```bash
python tests/test_rag_pipeline.py
```
*(Tests direct facts, paraphrases, markdown tables, citations, and strict refusals across 11 scenarios.)*

---

## ❓ Frequently Asked Questions (FAQ) & Troubleshooting

### Q1: I get `Execution of scripts is disabled on this system` in Windows PowerShell.
**Solution:** PowerShell restricts running scripts by default. Run this command once in your terminal:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
Then run `.\venv\Scripts\Activate.ps1` again.

---

### Q2: I get `ModuleNotFoundError: No module named 'app'`.
**Solution:** Python needs to know the project root directory. Always run commands from the `hr-policy-assistant` directory and ensure your virtual environment is active. You can also set:
- **Windows (PowerShell):** `$env:PYTHONPATH="."`
- **macOS / Linux:** `export PYTHONPATH="."`

---

### Q3: How do I know if my Gemini API key is working?
**Solution:** When you launch `streamlit run streamlit_app.py`, check the terminal log. If your key is invalid or missing, you will see a warning in the sidebar. You can test your key anytime for free at [Google AI Studio](https://aistudio.google.com/apikey).

---

### Q4: Are my company policies sent to third parties?
**Solution:** 
- **Embeddings:** 100% private. Converted into vectors locally on your CPU using `all-MiniLM-L6-v2`.
- **Generation:** Only the top 5 small excerpts relevant to the specific question are sent over SSL to the Google Gemini API to format the answer.

---

## 📄 License
This project is licensed under the MIT License — feel free to use and adapt it for your team or organization!

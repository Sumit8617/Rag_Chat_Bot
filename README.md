# 🏢 HR Policy Assistant

> **An AI-powered HR assistant that answers employee questions using approved company policies, with source citations and safe refusal when the required information is not available.**

Instead of searching through lengthy HR documents, employees can simply ask questions in natural language and receive a concise answer along with the relevant policy document and section.

---

## 🎥 Demo

### ▶️ Project Demo

**[Watch the Demo Video](https://drive.google.com/drive/folders/1u9lrw5fB3j6226FqUH0ZZutn9E6TGgvC?usp=sharing)**

The demo shows:

* 💬 Asking HR questions using natural language
* 📄 Getting answers from company policy documents
* 📌 Viewing the source and section used for an answer
* 🛡️ Safe refusal for unsupported questions
* 📤 Uploading new policy documents
* 📥 Exporting conversations

---

## 📑 Table of Contents

* [Overview](#-overview)
* [Key Features](#-key-features)
* [System Workflow](#-system-workflow)
* [Architecture](#-architecture)
* [Tech Stack](#️-tech-stack)
* [Project Structure](#-project-structure)
* [Quick Start](#-quick-start)

  * [Prerequisites](#prerequisites)
  * [1. Clone and Setup Environment](#1-clone-and-setup-environment)
  * [2. Install Dependencies](#2-install-dependencies)
  * [3. Configure Gemini API](#3-configure-gemini-api)
  * [4. Download Embedding Model](#4-download-embedding-model)
  * [5. Run the Application](#5-run-the-application)
* [Questions You Can Try](#-questions-you-can-try)
* [Admin: Uploading New Policies](#-admin-uploading-new-policies)
* [REST API](#-rest-api)
* [Running Tests](#-running-tests)
* [FAQ & Troubleshooting](#-faq--troubleshooting)
* [License](#-license)

---

# 📖 Overview

Employees often need quick answers about:

* 🏖️ Leave policies
* 🏥 Health benefits
* 🔒 IT security rules
* 💻 Software and browser-extension policies
* 📋 Other company policies

Searching through long policy documents manually can be time-consuming.

The **HR Policy Assistant** provides a simple chat interface where employees can ask questions and receive answers based on the company's uploaded policy documents.

### Example

**Employee asks:**

> How many casual leaves can I carry forward to next year?

**Assistant answers:**

> You can carry forward a maximum of **8 days** of unused casual leave to the next calendar year.

**Source:**

```text
leave-policy.md → Section 4.1 Casual leave carry-forward
```

This makes the answer easier to verify against the original policy.

---

## 🎯 Problem Being Solved

A normal AI chatbot may generate an answer based on its general knowledge, even when the information does not exist in a company's policies.

For HR and compliance-related questions, this can lead to incorrect information.

This project addresses the problem using a **Retrieval-Augmented Generation (RAG)** approach.

The system:

1. Searches the company's policy documents.
2. Finds relevant information.
3. Checks whether enough evidence exists.
4. Generates an answer using the retrieved information.
5. Validates the citations before showing the response.

If the required information cannot be found, the assistant **refuses instead of guessing**.

---

# ✨ Key Features

### 💬 Natural Language Questions

Employees can ask questions in normal language without needing to know the exact wording used in the policy.

---

### 📚 Policy-Grounded Answers

The assistant uses the uploaded company policies as its primary knowledge source.

It does not intentionally rely on general AI knowledge when answering policy questions.

---

### 🔎 Hybrid Search

The application combines two search methods:

**Vector Search**

Finds information based on meaning.

For example:

> "Can I carry unused leave to next year?"

can match a policy section containing:

> "Casual leave carry-forward."

**Keyword Search**

Looks for important or exact terms from the question.

The results from both methods are combined using **Reciprocal Rank Fusion (RRF)** to improve retrieval quality.

---

### 🛡️ Grounding / Safe Refusal

Before generating an answer, the system checks whether the retrieved policy information is strong enough.

If sufficient evidence is not found, the system refuses to answer.

Example:

> **Question:** What is the company's maternity leave policy?

If maternity leave is not present in the uploaded policies, the assistant responds:

> I don't have enough information in the uploaded policies to answer this question. Please contact HR.

This prevents the system from simply making up an answer.

---

### 📌 Source Citations

Policy-based answers include the document and section used to generate the response.

Example:

```text
Document: leave-policy.md
Section: 4.1 Casual leave carry-forward
```

This allows users to verify the information.

---

### 📤 Upload New Policies

Administrators can upload new Markdown or text-based policy documents directly from the Streamlit interface.

The application processes the document and makes it searchable.

---

### 📥 Export Conversations

Users can export their conversation transcript as a Markdown file.

---

# 🔄 System Workflow

The system follows a multi-stage RAG pipeline.

```text
                    📄 HR Policy Documents
                             │
                             ▼
                    ┌─────────────────┐
                    │ Document Loader │
                    └────────┬────────┘
                             │
                             ▼
                    ✂️ Document Chunking
                             │
                             ▼
                    🔢 Embedding Generation
                             │
                             ▼
                    🗄️ ChromaDB
                    Vector Database
                             │
                             │
                      👤 User Question
                             │
                             ▼
                    🔍 Hybrid Retrieval
                             │
                 ┌───────────┴───────────┐
                 ▼                       ▼
          Vector Search            Keyword Search
          Meaning-based            Exact-term
             Search                  Search
                 │                       │
                 └───────────┬───────────┘
                             ▼
                       🔀 RRF Fusion
                             │
                             ▼
                  ⭐ Top Relevant Chunks
                             │
                             ▼
                    🛡️ Grounding Check
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
                  ❌ NO              ✅ YES
                    │                 │
                    ▼                 ▼
               Safe Refusal      🤖 Gemini
                                  Answer Generation
                                       │
                                       ▼
                              📌 Citation Validation
                                       │
                                       ▼
                                💬 Final Answer
                                  + Citations
```

### Workflow Stages

| Stage                   | Description                                              |
| ----------------------- | -------------------------------------------------------- |
| **Document Loading**    | Reads supported HR policy files                          |
| **Chunking**            | Divides large documents into smaller searchable sections |
| **Embedding**           | Converts text into numerical representations             |
| **Indexing**            | Stores searchable information in ChromaDB                |
| **Vector Search**       | Finds relevant information based on meaning              |
| **Keyword Search**      | Finds relevant exact terms and clauses                   |
| **RRF Fusion**          | Combines and ranks results from both searches            |
| **Grounding Check**     | Determines whether enough evidence exists                |
| **Generation**          | Gemini creates the final response                        |
| **Citation Validation** | Verifies generated citations against retrieved content   |
| **Final Response**      | Returns the answer and source information                |

---

# 🏗️ Architecture

The application is organized into separate layers for the user interface, API, retrieval, document processing, generation, and validation.

```text
                         👤 Employee
                             │
                             ▼
                  ┌─────────────────────┐
                  │   Streamlit Web UI  │
                  │                     │
                  │ • Chat              │
                  │ • Policy Upload     │
                  │ • Citations         │
                  │ • Export            │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │   FastAPI Backend   │
                  │                     │
                  │ • /ask              │
                  │ • /documents        │
                  │ • /health           │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │     QA Service      │
                  │                     │
                  │ Retrieve → Ground   │
                  │ → Generate → Verify │
                  └──────────┬──────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │      Hybrid Retrieval        │
              │                              │
              │   ┌──────────┐ ┌──────────┐ │
              │   │  Vector  │ │ Keyword  │ │
              │   │  Search  │ │  Search  │ │
              │   └────┬─────┘ └────┬─────┘ │
              │        └──────┬─────┘        │
              │               ▼              │
              │           RRF Fusion          │
              └───────────────┬──────────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │    ChromaDB     │
                     │  Vector Store   │
                     └─────────────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │    Grounding    │
                     │      Check      │
                     └────────┬────────┘
                              │
                         Evidence?
                       ┌──────┴──────┐
                       ▼             ▼
                     ❌ No          ✅ Yes
                       │             │
                       ▼             ▼
                    Refusal       🤖 Gemini
                                     │
                                     ▼
                              Answer Generator
                                     │
                                     ▼
                              Citation Validator
                                     │
                                     ▼
                              💬 Final Response
```

### Architecture Components

| Component              | Responsibility                                               |
| ---------------------- | ------------------------------------------------------------ |
| **Streamlit**          | Provides the interactive user interface                      |
| **FastAPI**            | Provides backend REST API endpoints                          |
| **QA Service**         | Coordinates the complete question-answering pipeline         |
| **Ingestion Service**  | Processes and indexes uploaded policy documents              |
| **Hybrid Retrieval**   | Searches policy information using vector and keyword methods |
| **ChromaDB**           | Stores document embeddings and metadata                      |
| **Grounding**          | Checks whether retrieved information is sufficient           |
| **Gemini**             | Generates the final natural-language response                |
| **Citation Validator** | Verifies citations against retrieved policy content          |

---

# 🛠️ Tech Stack

| Category            | Technology            | Purpose                                              |
| ------------------- | --------------------- | ---------------------------------------------------- |
| **Language**        | Python 3.10+          | Core application development                         |
| **Backend**         | FastAPI               | REST API and backend services                        |
| **Frontend**        | Streamlit             | Interactive web chat interface                       |
| **LLM**             | Google Gemini         | Generates answers from retrieved policy information  |
| **Embeddings**      | Sentence Transformers | Converts policy text into searchable representations |
| **Vector Database** | ChromaDB              | Stores and retrieves document embeddings             |
| **Retrieval**       | Hybrid Search         | Combines vector and keyword search                   |
| **Ranking**         | RRF                   | Combines and ranks retrieval results                 |
| **Validation**      | Pydantic              | Request and response validation                      |
| **Testing**         | Python Test Suite     | Tests retrieval and safety behavior                  |
| **Configuration**   | `.env`                | Stores API keys and configuration                    |

---

# 📂 Project Structure

```text
hr-policy-assistant/
│
├── app/
│   ├── config.py
│   ├── main.py
│   │
│   ├── generation/
│   │   ├── generator.py
│   │   ├── prompt.py
│   │   └── citation_validator.py
│   │
│   ├── ingestion/
│   │   ├── chunker.py
│   │   ├── indexer.py
│   │   └── loader.py
│   │
│   ├── models/
│   │   └── schemas.py
│   │
│   ├── retrieval/
│   │   ├── embeddings.py
│   │   ├── grounding.py
│   │   ├── hybrid.py
│   │   ├── keyword_search.py
│   │   └── vector_store.py
│   │
│   └── services/
│       ├── ingestion_service.py
│       ├── qa_service.py
│       └── startup.py
│
├── chroma_db/
│
├── data/
│   └── policies/
│
├── tests/
│   ├── test_citation_validator.py
│   ├── test_evaluation.py
│   ├── test_grounding.py
│   ├── test_hybrid.py
│   └── test_rag_pipeline.py
│
├── .env.example
├── requirements.txt
├── streamlit_app.py
└── README.md
```

---

# 🚀 Quick Start

## Prerequisites

Before running the project, install:

* **Python 3.10 or higher**
* **Git** *(optional)*

You will also need a **Google Gemini API key**.

---

## 1. Clone and Setup Environment

Clone the repository:

```bash
git clone https://github.com/Sumit8617/Rag_Chat_Bot.git
cd hr-policy-assistant
```

### Windows

Create a virtual environment:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks the command:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again.

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 2. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

---

## 3. Configure Gemini API

The application uses Google Gemini to generate the final response.

Get an API key from:

**Google AI Studio**

https://aistudio.google.com/apikey

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_actual_api_key_here
GEMINI_MODEL=gemini-3.6-flash
```

> ⚠️ **Never commit your real `.env` file or API key to GitHub.**

---

## 4. Download Embedding Model

The application uses the lightweight `all-MiniLM-L6-v2` model to create searchable representations of the policy documents.

Run this command once:

```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

The model runs locally on your machine.

---

## 5. Run the Application

### 🌟 Option A — Streamlit Web Interface

This is the recommended way to run the project.

```bash
streamlit run streamlit_app.py
```

Open:

```text
http://localhost:8501
```

The web interface allows you to:

* Ask HR questions
* View answers
* Check citations
* Inspect retrieved policy snippets
* Upload new policies
* Export conversations

---

### ⚙️ Option B — FastAPI Backend

The FastAPI server can be started using:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

> **For the normal project demo, Streamlit is enough.**
> FastAPI is mainly useful when another application needs to communicate with the backend.

---

# 💬 Questions You Can Try

The application comes with three sample policies:

```text
leave-policy.md
benefits-policy.md
it-security-policy.md
```

### 🏖️ Leave Policy

**Question:**

> How many casual leaves can I carry forward to next year?

**Expected:**

> Maximum **8 days**, with a citation to the relevant section.

---

### 🏥 Health Benefits

**Question:**

> Does the Standard health tier cover dental implants?

**Expected:**

> No, dental implants are not covered under the Standard tier.

---

### 🔒 IT Security

**Question:**

> Can I send confidential company files to my personal Gmail?

**Expected:**

> No. Confidential and Restricted files must not be sent to personal email.

---

### 💻 Software Policy

**Question:**

> Can I install any browser extension I want?

**Expected:**

The assistant explains the company's software and browser-extension requirements and provides the relevant citation.

---

### ❌ Unsupported Question

**Question:**

> What is the company's maternity leave policy?

**Expected:**

If the uploaded policies do not contain maternity leave information, the assistant safely refuses instead of guessing.

---

### ❌ Random / Out-of-Scope Question

**Question:**

> Can I bring my pet iguana to the office?

**Expected:**

The assistant safely refuses because the available policies do not provide enough information.

---

# 📤 Admin: Uploading New Policies

Administrators can add new policy documents directly from the web interface.

### Steps

1. Open the Streamlit application.
2. Open the left sidebar.
3. Find **Admin: Upload Policy**.
4. Upload a `.md` or `.txt` file.
5. Click **📥 Ingest & Index Document**.
6. The document is processed and indexed.
7. The new policy becomes searchable.

Example:

```text
remote-work-office-policy.md
```

After uploading the document, employees can ask questions about the new policy.

---

## REST API Upload

A policy can also be uploaded through the API:

```bash
curl -X POST "http://127.0.0.1:8000/documents" \
  -F "file=@data/policies/remote-work-office-policy.md"
```

---

# 🛠️ REST API

The FastAPI backend provides endpoints for interacting with the application.

## Ask a Question

### Endpoint

```http
POST /ask
```

### Request

```json
{
  "question": "How many casual leave days can I carry forward?"
}
```

### Example Response

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

## Health Check

```http
GET /health
```

Used to check whether the backend is running correctly.

---

## API Documentation

FastAPI automatically provides interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

---

# 🧪 Running Tests

The project contains tests for the major components of the RAG pipeline.

## 1. Citation Validator

```bash
python tests/test_citation_validator.py
```

Checks whether generated citations are supported by the retrieved content.

---

## 2. Grounding Test

```bash
python tests/test_grounding.py
```

Checks whether the system correctly identifies strong and weak evidence.

---

## 3. Evaluation Test

```bash
python tests/test_evaluation.py
```

Tests standard questions and refusal scenarios.

---

## 4. Full RAG Pipeline Test

```bash
python tests/test_rag_pipeline.py
```

Tests:

* Direct factual questions
* Rephrased questions
* Markdown tables
* Citation behavior
* Unsupported questions
* Safe refusals

---

# ❓ FAQ & Troubleshooting

## Q1. Do I need to run both Streamlit and FastAPI?

**No.**

For the normal web application, simply run:

```bash
streamlit run streamlit_app.py
```

FastAPI is useful when you want to access the backend through REST APIs.

---

## Q2. PowerShell says "Execution of scripts is disabled"

Run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again:

```powershell
.\venv\Scripts\Activate.ps1
```

---

## Q3. I get `ModuleNotFoundError: No module named 'app'`

Make sure you are running commands from the project root:

```text
hr-policy-assistant/
```

Also make sure the virtual environment is active.

---

## Q4. How do I know if my Gemini API key is working?

Start the Streamlit application:

```bash
streamlit run streamlit_app.py
```

If the key is missing or invalid, the application will show a warning.

You can manage your API key through Google AI Studio:

https://aistudio.google.com/apikey

---

## Q5. Can I upload new policies?

Yes.

Upload `.md` or `.txt` files from the **Admin: Upload Policy** section in the Streamlit sidebar.

---

## Q6. What happens when the answer is not in the policies?

The system performs a grounding check.

If sufficient evidence cannot be found, it refuses to answer rather than generating an unsupported response.

---

# 🎯 Project Highlights

This project demonstrates practical experience with:

* **Retrieval-Augmented Generation (RAG)**
* **Hybrid Search**
* **Vector Databases**
* **Semantic Search**
* **Keyword Search**
* **Reciprocal Rank Fusion (RRF)**
* **LLM Integration**
* **Prompt Engineering**
* **Grounding / Hallucination Prevention**
* **Citation Validation**
* **Document Ingestion**
* **FastAPI**
* **Streamlit**
* **Python**
* **REST APIs**
* **Automated Testing**
* **Environment Configuration**

---

# 📌 Key Design Decisions

### Why Hybrid Search?

Vector search is good at understanding meaning, while keyword search is useful for exact policy terms, section names, and specific clauses.

Combining both provides more reliable retrieval.

### Why Grounding?

Even a good search result may not contain enough information to answer a question.

The grounding layer acts as a safety check before the LLM is called.

### Why Citation Validation?

The assistant should not only provide an answer but also show where the information came from.

Citation validation helps ensure that generated citations correspond to the retrieved policy content.

### Why Local Embeddings?

The embedding model can run locally, reducing dependency on an external embedding API and avoiding the need to send the entire policy collection to an external service for embedding.

---

# 📄 License

This project is licensed under the **MIT License**.

Feel free to use, modify, and adapt this project for your own applications or organization.

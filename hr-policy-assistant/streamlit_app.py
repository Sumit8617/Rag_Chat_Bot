import os
import time
import logging
from datetime import datetime


from dotenv import load_dotenv

load_dotenv()

import streamlit as st

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# Page Configuration
# ============================================================

st.set_page_config(
    page_title="HR Policy Assistant",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Synchronize API key and model from settings if not in os.environ
if settings.gemini_api_key and not os.environ.get("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = settings.gemini_api_key

if settings.gemini_model and not os.environ.get("GEMINI_MODEL"):
    os.environ["GEMINI_MODEL"] = settings.gemini_model

try:
    cloud_gemini_key = st.secrets.get("GEMINI_API_KEY")
    if cloud_gemini_key and not os.environ.get("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = str(cloud_gemini_key)

    cloud_gemini_model = st.secrets.get("GEMINI_MODEL")
    if cloud_gemini_model and not os.environ.get("GEMINI_MODEL"):
        os.environ["GEMINI_MODEL"] = str(cloud_gemini_model)
except Exception:
    # Normal for local development when secrets.toml does not exist.
    pass

gemini_configured = bool(
    os.environ.get("GEMINI_API_KEY") or settings.gemini_api_key
)

# ============================================================
# Application Imports
# ============================================================

from app.services.qa_service import QAService
from app.services.ingestion_service import IngestionService
from app.retrieval.vector_store import VectorStore

# ============================================================
# Constants
# ============================================================

REFUSAL_MESSAGE = (
    "I don't have enough information in the uploaded policies "
    "to answer this question. Please contact HR."
)

# ============================================================
# Cached Services
# ============================================================

@st.cache_resource
def get_qa_service():
    """Create and cache the QAService singleton."""
    return QAService()


@st.cache_resource
def get_ingestion_service():
    """Create and cache the IngestionService singleton."""
    return IngestionService()


@st.cache_resource
def ensure_sample_policies_seeded():
    """Seed sample policies if the vector database is empty."""
    try:
        from app.services.startup import seed_sample_policies_if_empty
        return seed_sample_policies_if_empty()
    except TypeError:
        try:
            from app.retrieval.embeddings import EmbeddingService
            from app.services.startup import seed_sample_policies_if_empty
            embedding_service = EmbeddingService()
            return seed_sample_policies_if_empty(embedding_service=embedding_service)
        except Exception as exc:
            logger.warning("Startup policy seeding skipped: %s", exc)
    except Exception as exc:
        logger.warning("Startup policy seeding skipped: %s", exc)
    return None


# Initialize sample policies
ensure_sample_policies_seeded()


def get_library_stats():
    """Extract metadata and chunk distribution from the vector store."""
    try:
        vs = VectorStore()
        chunks = vs.get_all_chunks()
        doc_map = {}
        for c in chunks:
            doc = c.get("document", "unknown")
            sec = c.get("metadata", {}).get("section", "General")
            if doc not in doc_map:
                doc_map[doc] = set()
            doc_map[doc].add(sec)
        return {
            "total_chunks": len(chunks),
            "documents": {doc: len(secs) for doc, secs in sorted(doc_map.items())},
        }
    except Exception as exc:
        logger.warning("Could not read vector store stats: %s", exc)
        return {"total_chunks": 0, "documents": {}}


# ============================================================
# Custom CSS Design System
# ============================================================

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

h1, h2, h3, h4, .hero-title {
    font-family: 'Outfit', 'Inter', sans-serif;
    letter-spacing: -0.02em;
}

/* Limit max width for comfortable reading on wide screens */
.main .block-container {
    max-width: 980px;
    padding-top: 1.5rem;
    padding-bottom: 4rem;
}

/* Hero Section */
.hero-card {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 24px;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.25);
    backdrop-filter: blur(12px);
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(99, 102, 241, 0.15);
    border: 1px solid rgba(99, 102, 241, 0.35);
    color: #a5b4fc;
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 4px 12px;
    border-radius: 9999px;
    margin-bottom: 12px;
}

.hero-title {
    font-size: 2.1rem;
    font-weight: 700;
    margin: 0 0 8px 0;
    background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    color: #94a3b8;
    font-size: 0.98rem;
    line-height: 1.5;
    margin: 0;
}

/* Prompt Card Buttons */
.prompt-box {
    background: rgba(30, 41, 59, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
    transition: all 0.2s ease;
}

.prompt-box:hover {
    border-color: rgba(99, 102, 241, 0.4);
    background: rgba(30, 41, 59, 0.65);
    transform: translateY(-2px);
}

/* Grounding & Verification Badges */
.badge-grounded {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #34d399;
    font-size: 0.8rem;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 9999px;
    margin-top: 8px;
    margin-bottom: 6px;
}

.badge-refused {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.3);
    color: #fbbf24;
    font-size: 0.8rem;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 9999px;
    margin-top: 8px;
    margin-bottom: 6px;
}

/* Citation Pill Tags */
.citation-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 10px;
    margin-bottom: 6px;
}

.citation-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(99, 102, 241, 0.1);
    border: 1px solid rgba(99, 102, 241, 0.25);
    color: #c7d2fe;
    font-size: 0.82rem;
    font-weight: 500;
    padding: 5px 12px;
    border-radius: 8px;
}

.citation-pill .doc-name {
    font-weight: 600;
    color: #e0e7ff;
}

.citation-pill .sec-name {
    color: #a5b4fc;
}

/* Evidence Card in Accordion */
.evidence-card {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 10px;
}

.evidence-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.82rem;
    color: #94a3b8;
    margin-bottom: 6px;
}

.evidence-text {
    font-size: 0.86rem;
    color: #e2e8f0;
    line-height: 1.5;
    background: rgba(0, 0, 0, 0.2);
    padding: 8px 12px;
    border-radius: 6px;
    border-left: 3px solid #6366f1;
}

/* Metric / Latency footer */
.response-meta {
    font-size: 0.76rem;
    color: #64748b;
    margin-top: 6px;
    display: flex;
    align-items: center;
    gap: 12px;
}

/* Sidebar polish */
.sidebar-card {
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 16px;
}

.status-indicator {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 6px;
}

.status-online {
    background-color: #10b981;
    box-shadow: 0 0 8px #10b981;
}

.status-warning {
    background-color: #f59e0b;
    box-shadow: 0 0 8px #f59e0b;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ============================================================
# Session State Initialization
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

# ============================================================
# Sidebar: Diagnostics, Policy Explorer & Admin
# ============================================================

library_stats = get_library_stats()

with st.sidebar:
    st.markdown("### 🏢 HR Policy Center")
    st.caption("AI-powered HR assistant with strict retrieval grounding and verifiable citations.")

    st.divider()



    # Admin: Upload Policy
    st.markdown("#### 📤 Admin: Upload Policy")
    st.caption("Upload a `.md` or `.txt` policy file to immediately chunk and index it.")

    uploaded_file = st.file_uploader(
        "Upload policy file",
        type=["md", "txt"],
        label_visibility="collapsed",
        key="admin_file_uploader",
    )

    if uploaded_file is not None:
        st.caption(f"Selected: `{uploaded_file.name}` ({len(uploaded_file.getvalue())} bytes)")

        if st.button("📥 Ingest & Index Document", use_container_width=True):
            with st.spinner("Chunking and updating vector embeddings..."):
                try:
                    ingestion_service = get_ingestion_service()
                    file_bytes = uploaded_file.getvalue()
                    if not file_bytes:
                        raise ValueError("The uploaded file is empty.")

                    result = ingestion_service.ingest_upload(
                        filename=uploaded_file.name,
                        file_bytes=file_bytes,
                    )

                    st.success(
                        f"Indexed `{result['document']}` with {result['chunks_indexed']} chunks."
                    )
                    get_qa_service.clear()
                    st.rerun()

                except ValueError as exc:
                    st.error(f"Upload error: {exc}")
                except Exception as exc:
                    logger.exception("Upload failed: %s", exc)
                    st.error("Failed to index document. Check file encoding and format.")

    st.divider()

    # Conversation Actions
    col_clear, col_export = st.columns(2)

    with col_clear:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.pending_prompt = None
            st.rerun()

    with col_export:
        if st.session_state.messages:
            # Build markdown export transcript
            export_lines = [
                "# HR Policy Assistant — Conversation Transcript",
                f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Model:** {settings.gemini_model}",
                "\n---\n",
            ]
            for m in st.session_state.messages:
                role = m["role"].capitalize()
                export_lines.append(f"### {role}\n")
                export_lines.append(f"{m['content']}\n")
                if role == "Assistant" and m.get("citations"):
                    export_lines.append("\n**Citations:**")
                    for cit in m["citations"]:
                        export_lines.append(
                            f"- `{cit.get('document')}` → `{cit.get('section')}`"
                        )
                export_lines.append("\n---\n")

            export_text = "\n".join(export_lines)
            st.download_button(
                "📥 Export",
                data=export_text,
                file_name=f"hr_policy_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        else:
            st.button("📥 Export", disabled=True, use_container_width=True)


# ============================================================
# Main Header / Hero Section
# ============================================================

st.markdown(
    f"""
    <div class="hero-card">
        <div class="hero-badge">
            ✨ Enterprise RAG • Grounded & Verifiable
        </div>
        <div class="hero-title">
            HR Policy Assistant
        </div>
        <div class="hero-subtitle">
            Get instant, verifiable answers to company HR policies with strict source citations.
            Answers are guaranteed to be grounded only in official policy documents.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Display Chat Messages
# ============================================================

for idx, msg in enumerate(st.session_state.messages):
    role = msg["role"]
    content = msg["content"]
    citations = msg.get("citations", [])
    grounded = msg.get("grounded", True)
    grounding_reason = msg.get("grounding_reason", "grounded")
    results = msg.get("results", [])
    latency = msg.get("latency")

    with st.chat_message(role, avatar="🧑‍💼" if role == "user" else "🤖"):
        st.markdown(content)

        if role == "assistant":
            # Grounding Status Badge
            if citations and grounded:
                st.markdown(
                    f'<div class="badge-grounded">✓ Verified Grounded ({len(citations)} source{"s" if len(citations) > 1 else ""})</div>',
                    unsafe_allow_html=True,
                )
            elif not grounded or content == REFUSAL_MESSAGE:
                st.markdown(
                    f'<div class="badge-refused">⚠ Policy Refusal — Out of Scope or Insufficient Evidence</div>',
                    unsafe_allow_html=True,
                )

            # Citations Pills
            if citations:
                pills_html = ['<div class="citation-container">']
                for cit in citations:
                    doc = cit.get("document", "Unknown")
                    sec = cit.get("section", "Section")
                    pills_html.append(
                        f'<div class="citation-pill">📄 <span class="doc-name">{doc}</span> <span class="sec-name">→ {sec}</span></div>'
                    )
                pills_html.append('</div>')
                st.markdown("".join(pills_html), unsafe_allow_html=True)

            # Transparency / Evidence Inspection Expander
            if results:
                with st.expander(
                    f"🔍 Inspect Retrieved Evidence ({len(results)} Chunks Analyzed)",
                    expanded=False,
                ):
                    for i, chunk in enumerate(results, start=1):
                        doc = chunk.get("document", "Unknown")
                        sec = chunk.get("metadata", {}).get("section", chunk.get("section", "General"))
                        fused_score = chunk.get("fused_score")
                        dist = chunk.get("distance")
                        text_snippet = chunk.get("text", "")

                        score_desc = []
                        if fused_score is not None:
                            score_desc.append(f"RRF Score: <strong>{fused_score:.4f}</strong>")
                        if dist is not None:
                            score_desc.append(f"Vector Distance: <strong>{dist:.4f}</strong>")

                        score_str = " • ".join(score_desc) if score_desc else ""

                        st.markdown(
                            f"""
                            <div class="evidence-card">
                                <div class="evidence-header">
                                    <span><strong>#{i}</strong> 📄 <code>{doc}</code> &gt; <code>{sec}</code></span>
                                    <span>{score_str}</span>
                                </div>
                                <div class="evidence-text">{text_snippet}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            # Latency and Engine Info
            meta_items = []
            if latency is not None:
                meta_items.append(f"⚡ {latency:.2f}s")
            meta_items.append("🔍 Hybrid RRF Search")
            meta_items.append(f"🤖 {settings.gemini_model}")
            st.markdown(
                f'<div class="response-meta">{" • ".join(meta_items)}</div>',
                unsafe_allow_html=True,
            )


# ============================================================
# Chat Input & Prompt Handling
# ============================================================

user_input = st.chat_input("Ask a question about leave, benefits, security, or office policies...")

prompt_to_run = None
if st.session_state.pending_prompt:
    prompt_to_run = st.session_state.pending_prompt
    st.session_state.pending_prompt = None
elif user_input:
    prompt_to_run = user_input.strip()

if prompt_to_run:
    # Append user question
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt_to_run,
        }
    )

    with st.chat_message("user", avatar="🧑‍💼"):
        st.markdown(prompt_to_run)

    with st.chat_message("assistant", avatar="🤖"):
        qa_service = get_qa_service()

        answer = ""
        citations = []
        grounded = False
        grounding_reason = ""
        results = []
        latency = 0.0

        with st.spinner("🔎 Searching policies and generating grounded answer..."):
            start_t = time.time()
            try:
                result = qa_service.ask(prompt_to_run)
                latency = time.time() - start_t

                if isinstance(result, dict):
                    answer = str(result.get("answer", REFUSAL_MESSAGE)).strip() or REFUSAL_MESSAGE
                    citations = result.get("citations", []) or []
                    grounded = result.get("grounded", False)
                    grounding_reason = result.get("grounding_reason", "")
                    results = result.get("results", []) or []
                else:
                    answer = REFUSAL_MESSAGE
                    citations = []
                    grounded = False
            except Exception as exc:
                latency = time.time() - start_t
                logger.exception("QA Service query execution error: %s", exc)
                answer = "Sorry, an error occurred while querying the policies. Please try again."
                citations = []
                grounded = False
                st.error("Could not complete request.")
                if not gemini_configured:
                    st.warning("⚠️ Gemini API key is missing. Please set `GEMINI_API_KEY`.")

        # Render current assistant response
        st.markdown(answer)

        # Grounding Badge
        if citations and grounded:
            st.markdown(
                f'<div class="badge-grounded">✓ Verified Grounded ({len(citations)} source{"s" if len(citations) > 1 else ""})</div>',
                unsafe_allow_html=True,
            )
        elif not grounded or answer == REFUSAL_MESSAGE:
            st.markdown(
                f'<div class="badge-refused">⚠ Policy Refusal — Out of Scope or Insufficient Evidence</div>',
                unsafe_allow_html=True,
            )

        # Citations Pills
        if citations:
            pills_html = ['<div class="citation-container">']
            for cit in citations:
                doc = cit.get("document", "Unknown")
                sec = cit.get("section", "Section")
                pills_html.append(
                    f'<div class="citation-pill">📄 <span class="doc-name">{doc}</span> <span class="sec-name">→ {sec}</span></div>'
                )
            pills_html.append('</div>')
            st.markdown("".join(pills_html), unsafe_allow_html=True)

        # Transparency / Evidence Inspection Expander
        if results:
            with st.expander(
                f"🔍 Inspect Retrieved Evidence ({len(results)} Chunks Analyzed)",
                expanded=False,
            ):
                for i, chunk in enumerate(results, start=1):
                    doc = chunk.get("document", "Unknown")
                    sec = chunk.get("metadata", {}).get("section", chunk.get("section", "General"))
                    fused_score = chunk.get("fused_score")
                    dist = chunk.get("distance")
                    text_snippet = chunk.get("text", "")

                    score_desc = []
                    if fused_score is not None:
                        score_desc.append(f"RRF Score: <strong>{fused_score:.4f}</strong>")
                    if dist is not None:
                        score_desc.append(f"Vector Distance: <strong>{dist:.4f}</strong>")

                    score_str = " • ".join(score_desc) if score_desc else ""

                    st.markdown(
                        f"""
                        <div class="evidence-card">
                            <div class="evidence-header">
                                <span><strong>#{i}</strong> 📄 <code>{doc}</code> &gt; <code>{sec}</code></span>
                                <span>{score_str}</span>
                            </div>
                            <div class="evidence-text">{text_snippet}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        # Latency and Engine Info
        meta_items = [f"⚡ {latency:.2f}s", "🔍 Hybrid RRF Search", f"🤖 {settings.gemini_model}"]
        st.markdown(
            f'<div class="response-meta">{" • ".join(meta_items)}</div>',
            unsafe_allow_html=True,
        )

        # Save assistant message in session state
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
                "citations": citations,
                "grounded": grounded,
                "grounding_reason": grounding_reason,
                "results": results,
                "latency": latency,
            }
        )
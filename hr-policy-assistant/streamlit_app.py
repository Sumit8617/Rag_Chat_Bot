import logging

import streamlit as st

from app.services.qa_service import QAService
from app.services.ingestion_service import IngestionService

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="HR Policy Assistant",
    page_icon="🤖",
    layout="centered"
)


@st.cache_resource
def get_qa_service():
    return QAService()


@st.cache_resource
def get_ingestion_service():
    return IngestionService()


st.title("🤖 HR Policy Assistant")

st.write(
    "Ask questions about company HR policies. "
    "Answers are generated only from the uploaded policies."
)

with st.sidebar:

    st.header("About")

    st.write(
        "This assistant uses Retrieval-Augmented Generation "
        "(RAG) to answer HR policy questions."
    )

    st.divider()

    st.write("### Supported questions")

    st.write(
        """
        - Casual leave
        - Sick leave
        - Privilege leave
        - Leave carry-forward
        - Leave expiry
        - Leave accrual
        """
    )

    st.divider()

    st.write("### 📤 Admin: Upload a policy")

    uploaded_file = st.file_uploader(
        "Upload a new HR policy (.md or .txt)",
        type=["md", "txt"],
        label_visibility="collapsed"
    )

    if uploaded_file is not None and st.button("Index this document"):

        with st.spinner("Indexing document..."):

            try:

                # Lazy construction, same reasoning as get_qa_service():
                # if GEMINI_API_KEY is unset or the embedding model
                # isn't cached, this raises here -- caught below --
                # rather than crashing the whole page on load.
                ingestion_service = get_ingestion_service()

                result = ingestion_service.ingest_upload(
                    filename=uploaded_file.name,
                    file_bytes=uploaded_file.getvalue()
                )

                st.success(
                    f"Indexed {result['document']} "
                    f"({result['chunks_indexed']} chunks). "
                    "It's searchable immediately -- try asking "
                    "about it below."
                )

            except ValueError as exc:
                # Bad extension, empty file, unreadable content, etc.
                # -- a clean, expected validation failure, not a crash.
                st.error(f"Could not index document: {exc}")

            except Exception as exc:
                logger.exception("Document upload failed: %s", exc)
                st.error(
                    "Something went wrong while indexing this "
                    "document. Check that the embedding model is "
                    "downloaded/cached and try again."
                )

    st.divider()

    if st.button("🗑️ Clear Chat"):

        st.session_state.messages = []

        st.rerun()

if "messages" not in st.session_state:

    st.session_state.messages = []


for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        # Show citations for assistant messages
        if (
            message["role"] == "assistant"
            and message.get("citations")
        ):

            st.markdown("**📚 Sources**")

            for citation in message["citations"]:

                document = citation.get(
                    "document",
                    "Unknown document"
                )

                section = citation.get(
                    "section",
                    "Unknown section"
                )

                st.caption(
                    f"📄 {document} → {section}"
                )

question = st.chat_input(
    "Ask a question about HR policies..."
)

if question:

    question = question.strip()

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    with st.chat_message("user"):

        st.markdown(question)


    with st.chat_message("assistant"):

        with st.spinner("Searching policies..."):

            try:

                # Service is constructed lazily, on first use, not
                # at module import time. If GEMINI_API_KEY is unset
                # or the embedding model isn't cached, this raises
                # here -- caught below -- instead of crashing the
                # whole page before any UI has a chance to render.
                qa_service = get_qa_service()

                result = qa_service.ask(question)

                answer = result.get(
                    "answer",
                    "I could not generate an answer."
                )

                citations = result.get(
                    "citations",
                    []
                )

            except Exception as exc:

                logger.exception("QA Service error: %s", exc)

                answer = (
                    "Sorry, something went wrong while "
                    "processing your question. Please try again, "
                    "or check that GEMINI_API_KEY is set and the "
                    "embedding model is downloaded/cached."
                )

                citations = []

        st.markdown(answer)


        if citations:

            st.markdown("**📚 Sources**")

            for citation in citations:

                document = citation.get(
                    "document",
                    "Unknown document"
                )

                section = citation.get(
                    "section",
                    "Unknown section"
                )

                st.caption(
                    f"📄 {document} → {section}"
                )

        else:

            st.info(
                "No policy sources were found."
            )

    # --------------------------------------------------------
    # Save Assistant Message
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "citations": citations
        }
    )
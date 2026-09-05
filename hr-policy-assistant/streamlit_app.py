import streamlit as st

from app.services.qa_service import QAService

st.set_page_config(
    page_title="HR Policy Assistant",
    page_icon="🤖",
    layout="centered"
)


@st.cache_resource
def get_qa_service():
    return QAService()


qa_service = get_qa_service()

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

                print(f"QA Service error: {exc}")

                answer = (
                    "Sorry, something went wrong while "
                    "processing your question. Please try again."
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
"""Company Policy Assistant: Streamlit chat UI.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import os

import streamlit as st

from policy_assistant.config import Settings
from policy_assistant.indexer import index_bytes, index_directory
from policy_assistant.llm import PROVIDERS, LLMError, available_providers, create_llm, provider_key
from policy_assistant.llm import ChatMessage
from policy_assistant.rag import NOT_FOUND_MESSAGE, PolicyAssistant
from policy_assistant.vectorstore import PolicyVectorStore, Source

st.set_page_config(page_title="Company Policy Assistant", page_icon="📚", layout="wide")

EXAMPLE_QUESTIONS = [
    "How many days of annual leave do I get?",
    "What is the hotel limit per night in Pune?",
    "Do I need a medical certificate for sick leave?",
    "Within how many days must I submit an expense claim?",
]


def _bridge_streamlit_secrets() -> None:
    """Expose Streamlit Cloud secrets as environment variables."""
    try:
        for key in ("GROQ_API_KEY", "GEMINI_API_KEY", "LLM_PROVIDER"):
            if key in st.secrets and not os.getenv(key):
                os.environ[key] = str(st.secrets[key])
    except Exception:  # noqa: BLE001 - no secrets file locally is fine
        pass


_bridge_streamlit_secrets()
SETTINGS = Settings.from_env()


@st.cache_resource(show_spinner="Loading the vector store and embedding model (first run downloads ~80 MB)...")
def get_store() -> PolicyVectorStore:
    store = PolicyVectorStore(SETTINGS.persist_dir, SETTINGS.collection_name)
    if store.count() == 0:  # first launch: index the bundled sample policies
        index_directory(store, SETTINGS.sample_dir, SETTINGS)
    return store


def init_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("pending_question", None)
    st.session_state.setdefault("uploader_key", 0)


def history_for_llm() -> list[ChatMessage]:
    return [ChatMessage(m["role"], m["content"]) for m in st.session_state.messages]


def render_sources(sources: list[Source]) -> None:
    if not sources:
        return
    with st.expander(f"Sources ({len(sources)})"):
        for i, s in enumerate(sources, start=1):
            st.markdown(f"**[S{i}] {s.file}**  ·  page {s.page}  ·  match {s.relevance:.0%}")
            st.caption(s.text)


def sidebar(store: PolicyVectorStore) -> tuple[str | None, str | None, list[str], int]:
    """Render the sidebar. Returns (provider, api_key, selected_documents, top_k)."""
    with st.sidebar:
        st.header("⚙️ Settings")

        configured = available_providers()
        providers = list(PROVIDERS)
        default = SETTINGS.default_provider if SETTINGS.default_provider in providers else providers[0]
        if configured and default not in configured:
            default = configured[0]
        provider = st.selectbox(
            "LLM provider",
            providers,
            index=providers.index(default),
            format_func=lambda p: PROVIDERS[p]["label"] + ("" if p in configured else " (key needed)"),
        )
        api_key = provider_key(provider)
        if not api_key:
            api_key = st.text_input(
                f"{PROVIDERS[provider]['env']}",
                type="password",
                help="Kept only in this browser session. Never stored or logged.",
            ).strip() or None
            if not api_key:
                st.info("Enter a free API key to start chatting. See the README for where to get one.")

        top_k = st.slider("Passages to retrieve", 2, 10, SETTINGS.top_k)

        st.divider()
        st.subheader("📄 Policy documents")
        documents = store.list_documents()
        if not documents:
            st.warning("No documents indexed yet.")
        for doc in documents:
            cols = st.columns([5, 1])
            cols[0].markdown(f"**{doc.name}**  \n{doc.pages} page(s) · {doc.chunks} chunks")
            if cols[1].button("🗑", key=f"del_{doc.name}", help=f"Remove {doc.name}"):
                store.delete_document(doc.name)
                st.rerun()

        names = [d.name for d in documents]
        selected = st.multiselect("Search only in", names, placeholder="All documents")

        st.divider()
        uploads = st.file_uploader(
            "Add your own policy PDFs",
            type=["pdf"],
            accept_multiple_files=True,
            key=f"uploader_{st.session_state.uploader_key}",
        )
        if uploads and st.button("Index uploaded files", type="primary", use_container_width=True):
            with st.spinner("Reading and indexing..."):
                results = [index_bytes(store, f.name, f.getvalue(), SETTINGS) for f in uploads]
            for r in results:
                if r.status == "indexed":
                    st.success(f"{r.name}: {r.chunks} chunks indexed")
                elif r.status == "skipped":
                    st.info(f"{r.name}: already indexed")
                else:
                    st.error(f"{r.name}: {r.message}")
            if any(r.status == "indexed" for r in results):
                st.session_state.uploader_key += 1
                st.rerun()

        if st.button("Reload sample policies", use_container_width=True):
            index_directory(store, SETTINGS.sample_dir, SETTINGS)
            st.rerun()
        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    return provider, api_key, selected, top_k


def answer_question(question: str, assistant: PolicyAssistant, selected: list[str], top_k: int) -> None:
    history = history_for_llm()
    st.session_state.messages.append({"role": "user", "content": question, "sources": []})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Searching policies..."):
                retrieval = assistant.retrieve(question, history, selected or None, top_k)
            text = st.write_stream(
                assistant.stream_answer(retrieval.standalone_question, history, retrieval.sources)
            )
            sources = [] if text.strip() == NOT_FOUND_MESSAGE else retrieval.sources
            render_sources(sources)
            st.session_state.messages.append({"role": "assistant", "content": text, "sources": sources})
        except LLMError as exc:
            st.error(f"{exc}\n\nCheck your API key and rate limits, then try again.")
            st.session_state.messages.pop()  # drop the unanswered question from history


def main() -> None:
    init_state()
    store = get_store()
    provider, api_key, selected, top_k = sidebar(store)

    st.title("📚 Company Policy Assistant")
    st.caption(
        "Ask questions about HR policies. Answers come only from the indexed documents "
        "and include the source file and page."
    )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            render_sources(message.get("sources", []))

    if not st.session_state.messages:
        st.markdown("**Try asking:**")
        cols = st.columns(2)
        for i, example in enumerate(EXAMPLE_QUESTIONS):
            if cols[i % 2].button(example, key=f"ex_{i}", use_container_width=True):
                st.session_state.pending_question = example
                st.rerun()

    typed = st.chat_input("Ask about leave, travel, reimbursement, work from home...")
    question = typed or st.session_state.pending_question
    st.session_state.pending_question = None

    if question:
        if store.count() == 0:
            st.warning("Index at least one policy PDF first (see the sidebar).")
        elif not api_key:
            st.warning("Add an API key in the sidebar to get answers.")
        else:
            try:
                llm = create_llm(provider, api_key, SETTINGS)
            except LLMError as exc:
                st.error(str(exc))
            else:
                answer_question(question, PolicyAssistant(store, llm, SETTINGS), selected, top_k)

    st.divider()
    st.caption("AI-generated answers can be wrong. Verify important decisions with HR.")


main()

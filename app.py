import streamlit as st

import config
from ui.styles import apply_executive_styles
from core.embedder import Embedder
from core.vector_store import VectorStore
from core.retriever import Retriever
from core.generator import Generator
from data_manager.source_manager import SourceManager

# 1. Streamlit Page Setup
st.set_page_config(
    page_title="Adaptive RAG Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply styling — read dark mode preference from session state (persists
# across reruns) before the toggle widget itself is even created below.
dark_mode = st.session_state.get("dark_mode", False)
apply_executive_styles(dark_mode)

# 2. Initialize & Cache Heavy Backend Components
@st.cache_resource
def get_backend_services():
    embedder = Embedder()
    vector_store = VectorStore()
    retriever = Retriever(embedder, vector_store)
    generator = Generator()
    source_manager = SourceManager(embedder, vector_store)
    return embedder, vector_store, retriever, generator, source_manager

embedder, vector_store, retriever, generator, source_manager = get_backend_services()

# Initialize Session State Variables
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

if "vector_memory_mb" not in st.session_state or "vector_points_count" not in st.session_state:
    stats = vector_store.get_collection_stats()
    st.session_state.vector_memory_mb = stats["estimated_vector_memory_mb"]
    st.session_state.vector_points_count = stats["points_count"]


def compute_confidence_tier(chunks: list[dict]) -> str:
    """Buckets a set of retrieved chunks into a simple confidence tier for the badge."""
    if not chunks:
        return "none"
    if any(c.get("low_confidence") for c in chunks):
        return "low"
    avg_score = sum(c["score"] for c in chunks) / len(chunks)
    if avg_score >= 0.55:
        return "high"
    elif avg_score >= 0.35:
        return "medium"
    return "low"


CONFIDENCE_LABELS = {
    "high": ("🟢", "High Confidence"),
    "medium": ("🟡", "Medium Confidence"),
    "low": ("🔴", "Low Confidence"),
    "none": ("⚪", "No Context Found"),
}


def render_confidence_badge(tier: str):
    icon, label = CONFIDENCE_LABELS[tier]
    st.markdown(
        f'<span class="conf-badge conf-{tier}">{icon} {label}</span>',
        unsafe_allow_html=True
    )


def render_sources(chunks: list[dict]):
    with st.expander("🔍 View Retained Source Citations & Similarity Scores"):
        for src in chunks:
            conf_tag = " `LOW CONFIDENCE`" if src.get("low_confidence") else ""
            st.markdown(f"- **{src['source_file']}** (Page {src['page']}) — *Cosine Score:* `{src['score']}`{conf_tag}")
            st.caption(f'"{src["text"][:150]}..."')


def render_followups(followups: list[str], msg_key: str):
    if not followups:
        return
    st.markdown('<div class="followup-row">', unsafe_allow_html=True)
    st.caption("💡 Follow-up suggestions:")
    cols = st.columns(len(followups))
    for i, fq in enumerate(followups):
        with cols[i]:
            if st.button(fq, key=f"followup_{msg_key}_{i}", use_container_width=True):
                st.session_state.pending_prompt = fq
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# --- SIDEBAR: DATA SOURCE CONTROL & HYPERPARAMETERS ---
with st.sidebar:
    st.title("Control Center")
    st.caption("Adaptive Knowledge Assistant")

    st.toggle("🌙 Dark Mode", key="dark_mode")

    st.markdown("---")

    # Document Uploader Section
    st.subheader("Data Source")
    uploaded_files = st.file_uploader(
        "Upload Documents (PDF, TXT, DOCX)",
        type=["pdf", "txt", "docx"],
        accept_multiple_files=True
    )

    if uploaded_files:
        if st.button("Process & Sync to Qdrant Cloud", use_container_width=True, type="primary"):
            with st.spinner("Ingesting, embedding & indexing..."):
                for file in uploaded_files:
                    res = source_manager.add_document(file)
                    if res["status"] == "success":
                        st.success(f"Indexed: {res['filename']} ({res['chunk_count']} chunks)")
                        st.session_state.vector_memory_mb = res["memory_mb"]
                        st.session_state.vector_points_count = res["points_count"]
                    else:
                        st.error(f"Error {file.name}: {res['message']}")
                st.rerun()

    st.markdown("---")

    # Active Documents List with Purge Actions
    st.subheader("Active Knowledge Base")
    active_docs = source_manager.get_active_documents()

    if active_docs:
        for doc_name in active_docs:
            col_name, col_del = st.columns([0.75, 0.25])
            with col_name:
                st.text(f"📄 {doc_name[:18]}..." if len(doc_name) > 18 else f"📄 {doc_name}")
            with col_del:
                if st.button("❌", key=f"del_{doc_name}", help=f"Purge {doc_name} from Qdrant"):
                    del_res = source_manager.remove_document(doc_name)
                    if del_res["status"] == "success":
                        stats = vector_store.get_collection_stats()
                        st.session_state.vector_memory_mb = stats["estimated_vector_memory_mb"]
                        st.session_state.vector_points_count = stats["points_count"]
                        st.toast(f"Purged vectors for {doc_name}")
                        st.rerun()
                    else:
                        # Deliberately NOT calling st.rerun() here — doing so would
                        # immediately wipe this error off the screen before it's readable.
                        st.error(f"Failed to purge {doc_name}: {del_res['message']}")
    else:
        st.info("No documents currently stored.")

    st.markdown("---")

    # Vector Store Memory Usage
    st.subheader("Vector Storage")
    st.metric("Estimated Memory Usage", f"{st.session_state.vector_memory_mb} MB")
    st.caption(
        f"{st.session_state.vector_points_count} vectors stored "
        f"(estimate: {config.EMBEDDING_DIM} dims × 4 bytes/float — actual Qdrant "
        f"RAM usage also includes payload text & index overhead, so real usage will be higher)"
    )

    st.markdown("---")

    # Chat History Control
    st.subheader("Chat Controls")
    if st.button("Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")

    # Hyperparameter Sliders
    st.subheader("RAG Hyperparameters")

    top_k = st.slider(
        "Top-K Chunks",
        min_value=config.TOP_K_MIN,
        max_value=config.TOP_K_MAX,
        value=config.DEFAULT_TOP_K,
        step=config.TOP_K_STEP
    )

    similarity_threshold = st.slider(
        "Cosine Score Threshold",
        min_value=config.THRESHOLD_MIN,
        max_value=config.THRESHOLD_MAX,
        value=config.DEFAULT_SIMILARITY_THRESHOLD,
        step=config.THRESHOLD_STEP
    )

    temperature = st.slider(
        "LLM Temperature",
        min_value=config.TEMP_MIN,
        max_value=config.TEMP_MAX,
        value=config.DEFAULT_TEMPERATURE,
        step=config.TEMP_STEP
    )


# --- MAIN INTERFACE: HEADER & CHAT ---
st.title("Adaptive RAG Assistant")
st.markdown("Real-Time Source Control & Native Vector Search")

# Feature & Engine Badges Showcase
col_b1, col_b2, col_b3 = st.columns(3)
with col_b1:
    st.markdown("""
        **Groq LLaMA 3.3 Engine**  
        <span class='status-badge'>70B Versatile</span>
    """, unsafe_allow_html=True)
with col_b2:
    st.markdown("""
        **Qdrant Vector DB**  
        <span class='status-badge'>HNSW Cloud Index</span>
    """, unsafe_allow_html=True)
with col_b3:
    st.markdown("""
        **HuggingFace Embeddings**  
        <span class='status-badge'>all-MiniLM-L6-v2 (384d)</span>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.subheader("Interactive Chat")

# Display Chat History
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            if "confidence" in message:
                render_confidence_badge(message["confidence"])
            if message.get("sources"):
                render_sources(message["sources"])
            if message.get("followups"):
                render_followups(message["followups"], msg_key=f"hist_{idx}")

# Handle User Input Prompt (either typed, or a clicked follow-up suggestion)
typed_prompt = st.chat_input("Ask a question about your documents...")
prompt = st.session_state.pending_prompt or typed_prompt
st.session_state.pending_prompt = None

if prompt:
    # Render User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Assistant Response
    with st.chat_message("assistant"):
        with st.spinner("Embedding query & searching vector index..."):
            # Step 1: Retrieve context chunks
            retrieved_chunks, raw_hits = retriever.retrieve(
                prompt,
                top_k=top_k,
                threshold=similarity_threshold
            )

            # Step 2: Generate LLM response via Groq
            response_text = generator.generate(
                prompt,
                retrieved_chunks,
                temperature=temperature
            )

            # Step 3: Confidence badge
            confidence_tier = compute_confidence_tier(retrieved_chunks)

            # Step 4: Follow-up suggestions (skip if we had nothing to ground on)
            followups = generator.generate_followups(prompt, response_text) if retrieved_chunks else []

            # Render Response
            st.markdown(response_text)
            render_confidence_badge(confidence_tier)

            if retrieved_chunks:
                render_sources(retrieved_chunks)

            new_msg_idx = len(st.session_state.messages)
            render_followups(followups, msg_key=f"live_{new_msg_idx}")

            # Save message to session state
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text,
                "sources": retrieved_chunks,
                "confidence": confidence_tier,
                "followups": followups
            })
import time
import datetime
import streamlit as st
import pandas as pd
from api_client import RiskAdvisorAPIClient

# Page configuration
st.set_page_config(
    page_title="AI Project Risk Advisor",
    layout="wide",
    initial_sidebar_state="expanded",
)

# High-End Enterprise Design System
st.markdown("""
<style>
    /* Global Typography */
    body, .stApp {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        color: #0F172A;
        background-color: #FAFAFB;
    }

    /* Enterprise App Header */
    .app-header {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 20px 24px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    .header-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }
    .main-title {
        font-size: 1.75rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        color: #0F172A;
        margin: 0;
    }
    .version-tag {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        background-color: #F1F5F9;
        color: #475569;
        padding: 3px 8px;
        border-radius: 4px;
        border: 1px solid #E2E8F0;
    }
    .subtitle {
        font-size: 0.9rem;
        color: #64748B;
        margin: 0;
    }

    /* Pipeline Progression Stepper */
    .pipeline-container {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 12px;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 22px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .pipe-step {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 12px;
        text-align: left;
        position: relative;
    }
    .pipe-step-active {
        border-color: #93C5FD;
        background: #F0F7FF;
    }
    .pipe-step-num {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        color: #2563EB;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .pipe-step-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #0F172A;
        margin-bottom: 4px;
    }
    .pipe-step-desc {
        font-size: 0.72rem;
        color: #64748B;
        line-height: 1.35;
    }

    /* Linear Visual Progress Bars */
    .progress-track {
        background-color: #E2E8F0;
        border-radius: 9999px;
        height: 6px;
        width: 100%;
        overflow: hidden;
        margin-top: 6px;
        margin-bottom: 6px;
    }
    .fill-emerald { background-color: #059669; height: 100%; border-radius: 9999px; }
    .fill-blue { background-color: #2563EB; height: 100%; border-radius: 9999px; }
    .fill-amber { background-color: #D97706; height: 100%; border-radius: 9999px; }

    /* Telemetry Badges */
    .status-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .badge-online { background-color: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; }
    .badge-offline { background-color: #FEF2F2; color: #991B1B; border: 1px solid #FECACA; }

    /* Result Cards */
    .result-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .result-card:hover {
        border-color: #CBD5E1;
    }
    .result-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #F1F5F9;
        padding-bottom: 10px;
        margin-bottom: 12px;
    }
    .result-title {
        font-size: 0.92rem;
        font-weight: 600;
        color: #0F172A;
    }
    .result-meta {
        font-size: 0.8rem;
        color: #64748B;
        margin-left: 10px;
    }
    .result-content {
        font-size: 0.9rem;
        line-height: 1.6;
        color: #334155;
        white-space: pre-wrap;
        background-color: #F8FAFC;
        border: 1px solid #EDF2F7;
        border-radius: 6px;
        padding: 14px;
    }

    /* Metric Cards */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .metric-val {
        font-size: 1.7rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.02em;
    }
    .metric-lbl {
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
        margin-bottom: 4px;
    }
    .metric-sub {
        font-size: 0.75rem;
        color: #94A3B8;
        margin-top: 4px;
    }

    /* Preset Labels */
    .section-label {
        font-size: 0.78rem;
        font-weight: 700;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

api = RiskAdvisorAPIClient()

# Header Banner
st.markdown("""
<div class="app-header">
    <div class="header-top">
        <h1 class="main-title">AI Project Intelligence & Risk Advisor</h1>
        <span class="version-tag">RAG Pipeline Enterprise</span>
    </div>
    <p class="subtitle">Multi-Agent Knowledge Base, Automated Project Risk Discovery and Vector Similarity Engine</p>
</div>
""", unsafe_allow_html=True)

# Sidebar: Live Telemetry Fragment
with st.sidebar:
    @st.fragment(run_every="2s")
    def render_live_telemetry():
        health = api.check_health()
        st.markdown("### Infrastructure Status")

        col1, col2 = st.columns(2)
        with col1:
            st.caption("Document API")
            if health["document_service"]:
                st.markdown('<span class="status-badge badge-online">ACTIVE [8000]</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="status-badge badge-offline">UNAVAILABLE</span>', unsafe_allow_html=True)
        with col2:
            st.caption("Vector RAG API")
            if health["rag_service"]:
                st.markdown('<span class="status-badge badge-online">ACTIVE [8002]</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="status-badge badge-offline">UNAVAILABLE</span>', unsafe_allow_html=True)

        st.markdown("---")
        st.caption("Embedding Inference Engine")
        if health["ollama"]:
            st.markdown(f'<span class="status-badge badge-online">READY ({health["ollama_model"]})</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-badge badge-offline">OFFLINE (Port 11434)</span>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### Repository Index")
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.metric("Documents", health["total_documents"])
        with m_col2:
            st.metric("Vector Chunks", health["total_chunks"])

        st.caption("Live streaming auto-sync (2s interval)")

    render_live_telemetry()

    st.markdown("---")
    st.markdown("### System Architecture")
    st.caption("Stage 1: Multi-Document Ingestion (PDF, DOCX, CSV, TXT)")
    st.caption("Stage 2: SHA-256 Fingerprint Deduplication")
    st.caption("Stage 3: Recursive Boundary Chunking")
    st.caption("Stage 4: Ollama Batch Embeddings (nomic-embed-text)")
    st.caption("Stage 5: ChromaDB Persistent Vector Index")

# Navigation Tabs
tab_ingest, tab_search, tab_analytics, tab_repository = st.tabs([
    "Document Ingestion & Pipeline",
    "Risk Intelligence Search",
    "Repository Analytics",
    "Knowledge Base Repository",
])

# ----------------------------------------------------
# TAB 1: DOCUMENT INGESTION & PIPELINE PROGRESSION
# ----------------------------------------------------
with tab_ingest:
    st.markdown("#### Ingestion Pipeline Progression")
    st.caption("End-to-end transformation from raw project artifacts into persistent semantic vectors.")

    # 5-Stage Visual Progression Stepper
    st.markdown("""
    <div class="pipeline-container">
        <div class="pipe-step pipe-step-active">
            <div class="pipe-step-num">Stage 01</div>
            <div class="pipe-step-title">Batch Upload</div>
            <div class="pipe-step-desc">Accepts 10+ files (PDF, DOCX, CSV, TXT) simultaneously.</div>
        </div>
        <div class="pipe-step pipe-step-active">
            <div class="pipe-step-num">Stage 02</div>
            <div class="pipe-step-title">Verification & Hash</div>
            <div class="pipe-step-desc">SHA-256 checksum generation for vector deduplication.</div>
        </div>
        <div class="pipe-step pipe-step-active">
            <div class="pipe-step-num">Stage 03</div>
            <div class="pipe-step-title">Semantic Chunking</div>
            <div class="pipe-step-desc">Preserves paragraphs, tables, and sentence boundaries.</div>
        </div>
        <div class="pipe-step pipe-step-active">
            <div class="pipe-step-num">Stage 04</div>
            <div class="pipe-step-title">Batch Embedding</div>
            <div class="pipe-step-desc">Ollama inference generates 768-dimensional vectors.</div>
        </div>
        <div class="pipe-step pipe-step-active">
            <div class="pipe-step-num">Stage 05</div>
            <div class="pipe-step-title">ChromaDB Index</div>
            <div class="pipe-step-desc">Persistent HNSW cosine space storage and cataloging.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Select or Drag-and-Drop Project Documents (Supports 10+ files simultaneously):",
        type=["pdf", "docx", "csv", "txt"],
        accept_multiple_files=True,
        help="Upload multiple project files. The system processes each file asynchronously.",
    )

    if uploaded_files:
        st.info(f"{len(uploaded_files)} file(s) staged for batch ingestion.")

        if st.button("Execute Ingestion Pipeline", type="primary"):
            current_health = api.check_health()
            if not current_health["document_service"] or not current_health["rag_service"]:
                st.error("Document Service (:8000) or RAG Service (:8002) is unavailable.")
            else:
                progress_container = st.container()
                with progress_container:
                    prog_bar = st.progress(0, text="Stage 1/5: Initializing file streams and validation...")
                    t_start = time.time()

                    file_payload = []
                    for f in uploaded_files:
                        f.seek(0)
                        file_payload.append(("files", (f.name, f.read(), f.type or "application/octet-stream")))

                    prog_bar.progress(25, text="Stage 2/5: Extracting text & computing SHA-256 fingerprints...")
                    time.sleep(0.3)

                    prog_bar.progress(55, text="Stage 3/5 & 4/5: Recursive chunking & generating Ollama batch embeddings...")
                    response = api.upload_files(file_payload)
                    elapsed = time.time() - t_start

                    prog_bar.progress(100, text=f"Stage 5/5: Persistent ChromaDB indexing completed in {elapsed:.1f}s.")

                total = response.get("total_files", 0)
                success = response.get("successful", 0)
                failed = response.get("failed", 0)

                if success > 0:
                    st.success(f"Pipeline executed successfully: {success} of {total} document(s) indexed in {elapsed:.1f}s.")
                if failed > 0:
                    st.warning(f"{failed} file(s) encountered validation or formatting errors.")

                results = response.get("results", [])
                if results:
                    st.markdown("##### Ingestion Diagnostic Breakdown")
                    table_rows = []
                    for r in results:
                        table_rows.append({
                            "Document Name": r.get("filename"),
                            "Status": r.get("status", "unknown").upper(),
                            "Format": r.get("file_type", "n/a").upper(),
                            "Size (KB)": round(r.get("size_bytes", 0) / 1024, 1),
                            "Characters": r.get("character_count", 0),
                            "Indexed Chunks": r.get("chunks_indexed", "N/A"),
                            "Diagnostics": r.get("detail", "OK"),
                        })
                    st.dataframe(pd.DataFrame(table_rows), use_container_width=True)

# ----------------------------------------------------
# TAB 2: RISK INTELLIGENCE SEARCH
# ----------------------------------------------------
with tab_search:
    st.markdown("#### Risk Intelligence & Semantic Search")
    st.caption("Vector similarity matching against all indexed project deliverables, meeting notes, and risk registers.")

    # Preset Investigation Chips
    st.markdown('<div class="section-label">Investigation Presets</div>', unsafe_allow_html=True)
    p_col1, p_col2, p_col3, p_col4 = st.columns(4)
    selected_preset = None
    with p_col1:
        if st.button("Delivery Delays & Blockers", use_container_width=True):
            selected_preset = "What could delay delivery and what are the critical project risks?"
    with p_col2:
        if st.button("QA & Defect Risks", use_container_width=True):
            selected_preset = "What are the software testing blockers and defect risks?"
    with p_col3:
        if st.button("Scope & Deliverables", use_container_width=True):
            selected_preset = "What is the project scope, key deliverables, and milestones?"
    with p_col4:
        if st.button("Budget & Resource Constraints", use_container_width=True):
            selected_preset = "What is the approved project budget and resource allocation?"

    # Query Input
    default_query = selected_preset if selected_preset else ""
    query_text = st.text_input(
        "Search Query:",
        value=default_query,
        placeholder="Enter natural language query or risk topic...",
    )

    # Search Configuration
    with st.expander("Search Parameters & Document Filters", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            top_k = st.slider("Top Chunks to Retrieve (top_k):", min_value=1, max_value=15, value=5)
        with c2:
            min_similarity = st.slider("Relevance Cutoff Threshold (%):", min_value=0, max_value=100, value=25)

        all_docs = api.get_indexed_documents()
        doc_options = {d["source_filename"]: d["document_id"] for d in all_docs}
        selected_doc_names = st.multiselect(
            "Filter by Specific Documents (Optional):",
            options=list(doc_options.keys()),
            help="Leave empty to query across the entire repository.",
        )
        selected_doc_ids = [doc_options[name] for name in selected_doc_names] if selected_doc_names else None

    # Search Execution
    if st.button("Search Repository", type="primary") or (selected_preset and query_text):
        if not query_text.strip():
            st.warning("Please provide a query string.")
        else:
            t0 = time.time()
            with st.spinner("Embedding query vector and querying ChromaDB..."):
                search_res = api.search_risks(
                    query=query_text,
                    top_k=top_k,
                    document_ids=selected_doc_ids,
                    min_similarity=float(min_similarity),
                )
            duration = time.time() - t0

            total_found = search_res.get("total_results", 0)
            results = search_res.get("results", [])

            if "error" in search_res and search_res["error"]:
                st.error(f"Search failed: {search_res['error']}")
            elif total_found == 0:
                st.info(f"No chunks satisfied the {min_similarity}% similarity threshold. Try adjusting your parameters.")
            else:
                st.success(f"Retrieved {total_found} relevant chunk(s) in {duration:.2f}s for: '{query_text}'")

                for idx, match in enumerate(results, start=1):
                    sim = match.get("similarity_score", 0.0)
                    src = match.get("source_filename", "Unknown")
                    c_idx = match.get("chunk_index", 0)
                    tot_c = match.get("total_chunks", 1)
                    text = match.get("text", "")

                    if sim >= 70:
                        fill_class = "fill-emerald"
                        conf_label = "HIGH CONFIDENCE"
                    elif sim >= 45:
                        fill_class = "fill-blue"
                        conf_label = "MODERATE CONFIDENCE"
                    else:
                        fill_class = "fill-amber"
                        conf_label = "LOW CONFIDENCE"

                    st.markdown(f"""
                    <div class="result-card">
                        <div class="result-header">
                            <div>
                                <span class="result-title">Result #{idx}: {src}</span>
                                <span class="result-meta">Chunk {c_idx + 1} of {tot_c}</span>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 0.82rem; font-weight: 700; color: #0F172A;">{sim:.1f}% Match ({conf_label})</div>
                                <div class="progress-track" style="width: 140px; margin-top: 4px;">
                                    <div class="{fill_class}" style="width: {min(100.0, sim)}%;"></div>
                                </div>
                            </div>
                        </div>
                        <div class="result-content">{text}</div>
                    </div>
                    """, unsafe_allow_html=True)

# ----------------------------------------------------
# TAB 3: REPOSITORY ANALYTICS & PROGRESSIONS
# ----------------------------------------------------
with tab_analytics:
    st.markdown("#### Repository Analytics & Coverage")
    st.caption("Distribution of indexed intelligence, vector density, and knowledge base coverage.")

    docs = api.get_indexed_documents()
    total_docs = len(docs)
    total_chunks = sum(d.get("chunk_count", 0) for d in docs)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">Vectorized Documents</div>
            <div class="metric-val">{total_docs}</div>
            <div class="metric-sub">Active in ChromaDB</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">Total Semantic Chunks</div>
            <div class="metric-val">{total_chunks}</div>
            <div class="metric-sub">HNSW Cosine Vectors</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        avg_chunks = round(total_chunks / total_docs, 1) if total_docs > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">Avg Chunks / Doc</div>
            <div class="metric-val">{avg_chunks}</div>
            <div class="metric-sub">Granularity Index</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        readiness_pct = min(100, int((total_chunks / 30) * 100)) if total_chunks > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">RAG Readiness Score</div>
            <div class="metric-val">{readiness_pct}%</div>
            <div class="metric-sub">Knowledge Density</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("##### Document Vector Density Distribution")

    if not docs:
        st.info("No documents currently indexed to calculate analytics.")
    else:
        for d in docs:
            d_name = d.get("source_filename", "Unknown")
            c_cnt = d.get("chunk_count", 0)
            pct = round((c_cnt / total_chunks) * 100, 1) if total_chunks > 0 else 0

            st.write(f"**{d_name}** — {c_cnt} chunks ({pct}% of total knowledge base)")
            st.markdown(f"""
            <div class="progress-track" style="height: 8px;">
                <div class="fill-blue" style="width: {pct}%;"></div>
            </div>
            """, unsafe_allow_html=True)

# ----------------------------------------------------
# TAB 4: KNOWLEDGE BASE REPOSITORY & MANAGEMENT
# ----------------------------------------------------
with tab_repository:
    st.markdown("#### Knowledge Base Repository")
    st.caption("Active persistent ChromaDB vector collection (Real-time auto-refresh).")

    @st.fragment(run_every="3s")
    def render_repository_catalog():
        current_docs = api.get_indexed_documents()

        if not current_docs:
            st.info("The repository is currently empty. Ingest project documents via the Ingestion tab.")
            return

        st.markdown(f"**Indexed Documents ({len(current_docs)}):**")
        
        doc_table = []
        for d in current_docs:
            ts = d.get("indexed_at", 0)
            date_str = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S") if ts else "N/A"
            doc_table.append({
                "Document Name": d.get("source_filename"),
                "Vector Chunks": d.get("chunk_count"),
                "Document ID": d.get("document_id"),
                "Indexed Date": date_str,
            })
        st.dataframe(pd.DataFrame(doc_table), use_container_width=True)

        st.markdown("---")
        st.markdown("##### Multi-Document Deletion Management")

        col_all, _ = st.columns([1, 2])
        with col_all:
            select_all = st.checkbox("Select all documents", key="select_all_cb")

        default_docs = current_docs if select_all else []
        selected_docs = st.multiselect(
            "Select document(s) to remove:",
            options=current_docs,
            default=default_docs,
            format_func=lambda x: f"{x.get('source_filename')} ({x.get('chunk_count')} chunks)",
            key=f"multi_delete_selector_{select_all}",
            help="Choose one or multiple documents to remove from the vector repository.",
        )

        if selected_docs:
            total_chunks_selected = sum(d.get("chunk_count", 0) for d in selected_docs)
            st.caption(f"Selected: {len(selected_docs)} document(s) | {total_chunks_selected} total vector chunks will be deleted.")

            btn_label = f"Delete Selected ({len(selected_docs)})" if len(selected_docs) > 1 else "Delete Selected Document"
            if st.button(btn_label, type="primary"):
                with st.spinner(f"Deleting {len(selected_docs)} document(s) from repository..."):
                    doc_ids = [d["document_id"] for d in selected_docs]
                    result = api.delete_multiple_documents(doc_ids)

                st.success(f"Successfully deleted {result['successful']} document(s) and purged associated vector embeddings.")
                st.rerun()
        else:
            st.caption("Select one or more documents from the list above to delete them.")

    render_repository_catalog()

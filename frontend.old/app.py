import streamlit as st
import requests

st.set_page_config(
    page_title="Hybrid PageIndex RAG",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# Stage definitions
# =========================================================
STAGES = [
    {"key": "index", "label": "Build Index", "icon": "🗂️", "kicker": "PAGEINDEX"},
    {"key": "okf", "label": "Generate OKF", "icon": "🧩", "kicker": "OKF"},
    {"key": "ask", "label": "Ask", "icon": "💬", "kicker": "RAG"},
]

if "stage" not in st.session_state:
    st.session_state.stage = "index"
if "page" not in st.session_state:
    st.session_state.page = "home"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_info" not in st.session_state:
    st.session_state.uploaded_info = None
if "page_index_data" not in st.session_state:
    st.session_state.page_index_data = None
if "okf_files_data" not in st.session_state:
    st.session_state.okf_files_data = None

active = next(s for s in STAGES if s["key"] == st.session_state.stage)

# =========================================================
# Global CSS — NexusAI-inspired light theme
# =========================================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

        :root {
            --bg: #F7F8FC;
            --bg-raised: #FFFFFF;
            --bg-subtle: #F1F3F9;
            --border: #E4E7EF;
            --border-hover: #CDD1DE;
            --accent: #6366F1;
            --accent-hover: #5558E6;
            --accent-light: #EEF2FF;
            --cyan: #06B6D4;
            --cyan-light: #ECFEFF;
            --text: #0F172A;
            --text-secondary: #475569;
            --text-muted: #94A3B8;
            --success: #10B981;
            --error: #EF4444;
            --warning: #F59E0B;
        }

        html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif !important; }

        .stApp { background: var(--bg) !important; }
        .main .block-container { padding-top: 2rem; max-width: 880px; }

        p, span, label, .stMarkdown, li { color: var(--text) !important; }

        /* ---------- Sidebar ---------- */
        section[data-testid="stSidebar"] {
            background: var(--bg-raised) !important;
            border-right: 1px solid var(--border);
        }
        section[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }

        .brand-row {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            margin-bottom: 1.4rem;
        }
        .brand-badge {
            width: 34px; height: 34px;
            border-radius: 10px;
            background: linear-gradient(135deg, var(--accent), var(--cyan));
            display: flex; align-items: center; justify-content: center;
            color: white; font-weight: 800; font-size: 0.95rem;
            flex-shrink: 0;
        }
        .brand-name { font-weight: 800; font-size: 1.05rem; color: var(--text); line-height: 1.1; }
        .brand-sub { font-size: 0.72rem; color: var(--text-muted); font-weight: 500; }

        .sb-section-label {
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--text-muted);
            margin: 1.1rem 0 0.5rem 0;
        }

        /* File card in sidebar */
        .kb-file-card {
            background: var(--bg-raised);
            border: 1.5px solid var(--border);
            border-radius: 12px;
            padding: 0.7rem 0.8rem;
            margin-bottom: 0.6rem;
        }
        .kb-file-top { display: flex; align-items: flex-start; gap: 0.6rem; }
        .kb-file-icon {
            width: 30px; height: 30px; border-radius: 8px;
            background: var(--accent-light); color: var(--accent);
            display: flex; align-items: center; justify-content: center;
            font-size: 0.9rem; flex-shrink: 0;
        }
        .kb-file-name { font-size: 0.85rem; font-weight: 600; color: var(--text); word-break: break-word; line-height: 1.25; }
        .kb-file-meta { font-size: 0.72rem; color: var(--text-muted); margin-top: 0.15rem; }
        .kb-status {
            display: inline-flex; align-items: center; gap: 0.35rem;
            font-size: 0.68rem; font-weight: 600; margin-top: 0.5rem;
            color: var(--success);
        }
        .kb-status-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--success); }

        .kb-empty {
            border: 1.5px dashed var(--border);
            border-radius: 12px;
            padding: 1.2rem 0.8rem;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.78rem;
        }

        /* Sidebar nav buttons (stage switcher) */
        section[data-testid="stSidebar"] .stButton>button {
            width: 100%;
            text-align: left;
            border-radius: 10px;
            border: 1px solid transparent;
            background: transparent;
            color: var(--text-secondary) !important;
            font-weight: 600;
            font-size: 0.85rem;
            padding: 0.55rem 0.8rem;
            transition: all 0.15s ease;
        }
        section[data-testid="stSidebar"] .stButton>button:hover {
            background: var(--bg-subtle);
            border-color: var(--border);
        }
        section[data-testid="stSidebar"] .stButton>button p { color: inherit !important; }
        section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"] {
            background: var(--accent-light) !important;
            color: var(--accent) !important;
            border: 1px solid var(--accent) !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"] p { color: var(--accent) !important; }

        /* ---------- Main content buttons ---------- */
        .main .stButton>button {
            border-radius: 10px;
            border: 1.5px solid var(--border);
            background: var(--bg-raised);
            color: var(--text) !important;
            font-weight: 600;
            font-size: 0.85rem;
            padding: 0.55rem 1.1rem;
            transition: all 0.15s ease;
        }
        .main .stButton>button:hover { border-color: var(--border-hover); background: var(--bg-subtle); }
        .main .stButton>button p { color: inherit !important; }
        .main div[data-testid="stButton"] button[kind="primary"] {
            background: var(--accent) !important;
            color: white !important;
            border: none !important;
        }
        .main div[data-testid="stButton"] button[kind="primary"] p { color: white !important; }
        .main div[data-testid="stButton"] button[kind="primary"]:hover { background: var(--accent-hover) !important; }

        /* ---------- Cards / containers ---------- */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--bg-raised) !important;
            border: 1px solid var(--border) !important;
            border-radius: 16px !important;
            box-shadow: 0 1px 3px rgba(15,23,42,0.03);
        }

        [data-testid="stFileUploaderDropzone"] {
            background: var(--bg-subtle) !important;
            border: 1.5px dashed var(--border) !important;
            border-radius: 14px !important;
        }

        [data-testid="stExpander"] {
            background: var(--bg-raised) !important;
            border: 1px solid var(--border) !important;
            border-radius: 12px !important;
        }
        [data-testid="stExpander"] summary { color: var(--text) !important; font-size: 0.85rem !important; font-weight: 600; }

        [data-testid="stAlert"] { border-radius: 12px; }

        /* ---------- Chat (Ask stage) ---------- */
        [data-testid="stChatInput"] {
            background: rgba(255,255,255,0.85) !important;
            backdrop-filter: blur(10px);
            border-radius: 16px !important;
            border: 1.5px solid var(--border) !important;
        }
        [data-testid="stChatMessage"] {
            background: transparent !important;
            border: none !important;
        }

        /* ---------- Hero ---------- */
        .page-kicker {
            font-size: 0.72rem; font-weight: 700; letter-spacing: 0.14em;
            text-transform: uppercase; color: var(--accent); margin-bottom: 0.3rem;
        }
        .page-title { font-size: 1.9rem; font-weight: 800; color: var(--text); margin-bottom: 1.2rem; }

        .hero-wrap { text-align: center; padding: 1.5rem 0 1rem 0; }
        .hero-badge {
            width: 56px; height: 56px; margin: 0 auto 1.1rem auto;
            border-radius: 16px;
            background: linear-gradient(135deg, var(--accent-light), var(--cyan-light));
            display: flex; align-items: center; justify-content: center;
            font-size: 1.6rem;
        }
        .hero-title { font-size: 1.6rem; font-weight: 800; color: var(--text); margin-bottom: 0.5rem; }
        .hero-sub { color: var(--text-muted); font-size: 0.9rem; max-width: 440px; margin: 0 auto; line-height: 1.6; }

        .idx-row { display: flex; align-items: baseline; gap: 0.6rem; margin: 0.35rem 0; }
        .idx-title { color: var(--text); font-weight: 600; font-size: 0.9rem; }
        .idx-range {
            font-size: 0.68rem; color: var(--accent); background: var(--accent-light);
            border-radius: 10px; padding: 0.1rem 0.5rem; white-space: nowrap; font-weight: 600;
        }
        .idx-summary { color: var(--text-muted); font-size: 0.8rem; margin: 0.15rem 0 0.5rem 0; }
    </style>
""", unsafe_allow_html=True)


# =========================================================
# SIDEBAR — brand, knowledge base file card, stage nav
# =========================================================
with st.sidebar:
    st.markdown("""
        <div class="brand-row">
            <div class="brand-badge">H</div>
            <div>
                <div class="brand-name">Hybrid·RAG</div>
                <div class="brand-sub">Document Lab</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("＋  New Document", use_container_width=True):
        st.session_state.page = "home"
        st.session_state.uploaded_info = None
        st.session_state.messages = []
        st.session_state.page_index_data = None
        st.session_state.okf_files_data = None
        st.session_state.stage = "index"
        st.rerun()

    st.markdown('<div class="sb-section-label">Knowledge Base</div>', unsafe_allow_html=True)

    if st.session_state.uploaded_info:
        info = st.session_state.uploaded_info
        meta_bits = []
        if info.get("total_pages"):
            meta_bits.append(f'{info["total_pages"]} pages')
        if info.get("total_words"):
            meta_bits.append(f'{info["total_words"]} words')
        meta_text = " · ".join(meta_bits) if meta_bits else "Converted"

        st.markdown(f"""
            <div class="kb-file-card">
                <div class="kb-file-top">
                    <div class="kb-file-icon">📄</div>
                    <div>
                        <div class="kb-file-name">{info['filename']}</div>
                        <div class="kb-file-meta">{meta_text}</div>
                    </div>
                </div>
                <div class="kb-status"><span class="kb-status-dot"></span>Ready</div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="kb-empty">No document yet.<br>Upload one to get started.</div>', unsafe_allow_html=True)

    if st.session_state.page == "workspace":
        st.markdown('<div class="sb-section-label">Workspace</div>', unsafe_allow_html=True)
        for s in STAGES:
            is_active = s["key"] == st.session_state.stage
            if st.button(
                f"{s['icon']}  {s['label']}",
                key=f"nav_{s['key']}",
                type="primary" if is_active else "secondary",
                use_container_width=True
            ):
                st.session_state.stage = s["key"]
                st.rerun()


# =========================================================
# HOME — upload screen
# =========================================================
def render_home():
    st.markdown("""
        <div class="hero-wrap">
            <div class="hero-badge">✨</div>
            <div class="hero-title">Ask anything about your documents</div>
            <div class="hero-sub">
                Upload a document and compare three retrieval engines —
                RAG, OKF, and PageIndex — side by side.
            </div>
        </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Choose a document",
        type=["pdf", "doc", "docx", "odt", "ppt", "pptx", "rtf", "epub", "xls", "xlsx", "ods", "odp", "csv"],
        label_visibility="collapsed"
    )

    if uploaded_file is not None:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"📄 **{uploaded_file.name}** · {uploaded_file.size / 1024:.1f} KB")
        with col2:
            upload_clicked = st.button("Get started", type="primary", use_container_width=True)

        if upload_clicked:
            with st.spinner("Parsing document..."):
                files = {"file": (uploaded_file.name, uploaded_file, "application/octet-stream")}
                response = requests.post("http://127.0.0.1:8000/upload", files=files)
                result = response.json()

            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                st.session_state.uploaded_info = result
                st.session_state.stage = "index"
                pages_note = f" — {result['total_pages']} pages, {result['total_words']} words" if result.get("total_pages") else ""
                st.success(f"✅ Converted successfully{pages_note}")
                st.session_state.page = "workspace"
                st.rerun()


# =========================================================
# Helper — recursively render a page index node
# =========================================================
def render_index_node(node, level=0):
    title = node.get("title", "Untitled")
    start = node.get("start_index", "?")
    end = node.get("end_index", "?")
    summary = node.get("summary", "")
    children = node.get("nodes", [])
    indent = "&nbsp;&nbsp;&nbsp;&nbsp;" * level

    if children:
        with st.expander(f"{title}   (p.{start}–{end})"):
            if summary:
                st.markdown(f'<div class="idx-summary">{summary}</div>', unsafe_allow_html=True)
            for child in children:
                render_index_node(child, level + 1)
    else:
        st.markdown(
            f'<div class="idx-row">{indent}<span class="idx-title">{title}</span>'
            f'<span class="idx-range">p.{start}–{end}</span></div>',
            unsafe_allow_html=True
        )
        if summary:
            st.markdown(f'<div class="idx-summary">{indent}{summary}</div>', unsafe_allow_html=True)


# =========================================================
# WORKSPACE — stage content (sidebar handles nav + doc card)
# =========================================================
def render_workspace():
    st.markdown(f'<div class="page-kicker">{active["kicker"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-title">{active["icon"]}  {active["label"]}</div>', unsafe_allow_html=True)

    if active["key"] == "index":
        with st.container(border=True):
            if st.button("Build index", type="primary"):
                with st.spinner("Building index..."):
                    response = requests.post("http://127.0.0.1:8000/build-index")
                    result = response.json()
                if "error" in result:
                    st.error(f"❌ {result['error']}")
                else:
                    st.success(f"✅ Index built — {result.get('sections', 'N/A')} sections")

            st.divider()

            if st.button("Load page index"):
                with st.spinner("Loading index..."):
                    response = requests.get("http://127.0.0.1:8000/page-index")
                    result = response.json()
                if "error" in result:
                    st.error(f"❌ {result['error']}")
                else:
                    st.session_state.page_index_data = result["index"]

            if st.session_state.page_index_data:
                render_index_node(st.session_state.page_index_data)

    elif active["key"] == "okf":
        with st.container(border=True):
            if st.button("Generate OKF", type="primary"):
                with st.spinner("Generating OKF structure..."):
                    response = requests.post("http://127.0.0.1:8000/generate-okf")
                    result = response.json()
                if "error" in result:
                    st.error(f"❌ {result['error']}")
                else:
                    st.success(f"✅ OKF generated — {result.get('files', 'N/A')} files")

            st.divider()

            if st.button("Load OKF files"):
                with st.spinner("Loading OKF files..."):
                    response = requests.get("http://127.0.0.1:8000/okf-files")
                    result = response.json()
                if "error" in result:
                    st.error(f"❌ {result['error']}")
                else:
                    st.session_state.okf_files_data = result["files"]

            if st.session_state.okf_files_data:
                for file in st.session_state.okf_files_data:
                    with st.expander(f"{file['filename']}"):
                        st.markdown(file["content"])

    elif active["key"] == "ask":
        for msg in st.session_state.messages:
            avatar = "🧑" if msg["role"] == "user" else "✨"
            st.chat_message(msg["role"], avatar=avatar).write(msg["content"])

        question = st.chat_input("Ask about your document...")

        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            st.chat_message("user", avatar="🧑").write(question)

            with st.chat_message("assistant", avatar="✨"):
                with st.spinner("Thinking..."):
                    response = requests.post("http://127.0.0.1:8000/ask", params={"question": question})
                    answer = response.json().get("answer", "No answer received")
                st.write(answer)

            st.session_state.messages.append({"role": "assistant", "content": answer})


# =========================================================
# Router
# =========================================================
if st.session_state.page == "home":
    render_home()
else:
    render_workspace()
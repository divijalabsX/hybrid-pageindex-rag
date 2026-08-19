import streamlit as st
import requests

st.set_page_config(
    page_title="Hybrid PageIndex RAG",
    page_icon="🪐",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# =========================================================
# Stage definitions — each stage gets its own accent + backdrop
# =========================================================
STAGES = [
    {"key": "index", "num": "02", "label": "Build Index", "kicker": "PAGEINDEX", "c1": "#3FA9E8", "c2": "#2E5FE0"},
    {"key": "okf", "num": "03", "label": "Generate OKF", "kicker": "OKF", "c1": "#E8B34F", "c2": "#D97706"},
    {"key": "ask", "num": "04", "label": "Ask", "kicker": "RAG", "c1": "#E85D75", "c2": "#C23B6B"},
]

if "stage" not in st.session_state:
    st.session_state.stage = "index"

active = next(s for s in STAGES if s["key"] == st.session_state.stage)

# =========================================================
# Global CSS
# =========================================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; }

        .main { padding-top: 1.2rem; }
        .main .block-container { background: transparent; max-width: 720px; }

        .topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.4rem 0 1.6rem 0;
        }
        .wordmark {
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 700;
            font-size: 1.05rem;
            color: #F5F3FF;
            letter-spacing: 0.01em;
        }
        .wordmark span { color: #8B93F5; }
        .navtag {
            font-family: 'Inter', sans-serif;
            font-size: 0.7rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #A9A6C9;
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 20px;
            padding: 0.35rem 0.9rem;
        }

        .kicker {
            font-family: 'Inter', sans-serif;
            font-size: 0.75rem;
            letter-spacing: 0.22em;
            text-transform: uppercase;
            color: #A9A6C9;
            text-align: center;
            margin-bottom: 0.6rem;
        }
        .hero-title {
            text-align: center;
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 700;
            font-size: 3rem;
            letter-spacing: 0.01em;
            color: #FFFFFF;
            margin: 0 0 0.9rem 0;
            line-height: 1.05;
        }
        .hero-rule {
            width: 56px;
            height: 3px;
            border-radius: 2px;
            margin: 0 auto 1.2rem auto;
        }
        .hero-sub {
            text-align: center;
            color: #C7C4E0;
            font-size: 0.95rem;
            max-width: 480px;
            margin: 0 auto 1.6rem auto;
            line-height: 1.6;
        }

        @keyframes heroFade {
            from { opacity: 0; transform: translateY(10px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        .hero-anim { animation: heroFade 0.55s ease-out; }

        .legend-trio {
            display: flex;
            justify-content: center;
            gap: 0.7rem;
            flex-wrap: wrap;
            margin-bottom: 2rem;
        }
        .legend-chip {
            display: flex;
            align-items: center;
            gap: 0.45rem;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 20px;
            padding: 0.45rem 0.95rem;
            font-size: 0.8rem;
            color: #E4E2F5;
        }
        .legend-dot { width: 8px; height: 8px; border-radius: 50%; }

        [data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255,255,255,0.04) !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            border-radius: 14px !important;
            backdrop-filter: blur(6px);
        }

        p, span, label, .stMarkdown { color: #E4E2F5 !important; }

        .stButton>button {
            width: 100%;
            border-radius: 24px;
            height: 2.9em;
            background: rgba(255,255,255,0.06);
            color: #F5F3FF !important;
            font-weight: 600;
            font-size: 0.85rem;
            border: 1px solid rgba(255,255,255,0.2);
            transition: all 0.2s ease;
        }
        .stButton>button:hover {
            background: rgba(255,255,255,0.14);
            border-color: rgba(255,255,255,0.4);
            transform: translateY(-1px);
        }
        .stButton>button p { color: inherit !important; }

        div[data-testid="stButton"] button[kind="primary"] {
            background: #F5F3FF !important;
            color: #0B0E1F !important;
            border: none !important;
        }
        div[data-testid="stButton"] button[kind="primary"] p { color: #0B0E1F !important; }
        div[data-testid="stButton"] button[kind="primary"]:hover {
            background: #FFFFFF !important;
            transform: translateY(-1px);
        }

        [data-testid="stFileUploaderDropzone"] {
            background: rgba(255,255,255,0.03) !important;
            border: 1px dashed rgba(255,255,255,0.25) !important;
            border-radius: 14px !important;
        }

        [data-testid="stExpander"] {
            background: rgba(255,255,255,0.03) !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            border-radius: 12px !important;
        }
        [data-testid="stExpander"] summary { color: #F5F3FF !important; font-size: 0.85rem !important; }

        [data-testid="stChatInput"] {
            background: rgba(255,255,255,0.05) !important;
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.15) !important;
        }
        [data-testid="stChatMessage"] {
            background: rgba(255,255,255,0.03) !important;
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.1);
        }

        [data-testid="stAlert"] {
            background: rgba(255,255,255,0.05) !important;
            border-radius: 12px;
        }

        /* ---------- Document info bar — visually distinct from nav pills ---------- */
        .doc-info-label {
            font-size: 0.68rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: #6F6C93;
            margin-bottom: 0.5rem;
        }
        .doc-info-bar {
            display: flex;
            align-items: center;
            gap: 1rem;
            background: rgba(255,255,255,0.02);
            border-left: 3px solid #8B93F5;
            border-radius: 4px;
            padding: 0.7rem 1rem;
            margin-bottom: 1.8rem;
        }
        .doc-info-name {
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 600;
            font-size: 0.9rem;
            color: #F5F3FF;
        }
        .doc-info-meta {
            font-size: 0.78rem;
            color: #8B88A8;
        }
        .doc-info-dot { color: #454266; margin: 0 0.15rem; }

        .subsection-divider {
            border: none;
            border-top: 1px dashed rgba(255,255,255,0.14);
            margin: 1.6rem 0 1.2rem 0;
        }
        .subsection-label {
            font-size: 0.72rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #8B88A8;
            margin-bottom: 0.8rem;
        }

        .idx-row { display: flex; align-items: baseline; gap: 0.6rem; margin: 0.35rem 0; }
        .idx-title { color: #F5F3FF; font-weight: 500; font-size: 0.92rem; }
        .idx-range {
            font-size: 0.72rem;
            color: #0B0E1F;
            background: #A9A6C9;
            border-radius: 10px;
            padding: 0.1rem 0.5rem;
            white-space: nowrap;
        }
        .idx-summary { color: #A9A6C9; font-size: 0.82rem; margin: 0.15rem 0 0.5rem 0; }
    </style>
""", unsafe_allow_html=True)

# ---------- Dynamic per-stage backdrop (the "live transition") ----------
def apply_backdrop(c1, c2):
    st.markdown(f"""
        <style>
        .stApp {{
            background-color: #05070F !important;
            background-image:
                radial-gradient(ellipse 60% 45% at 25% 15%, {c1}33, transparent 60%),
                radial-gradient(ellipse 55% 40% at 80% 85%, {c2}2E, transparent 55%),
                linear-gradient(180deg, #05070F 0%, #090C1C 55%, #05070F 100%) !important;
            transition: background 0.6s ease;
        }}
        </style>
    """, unsafe_allow_html=True)

# ---------- Session state setup ----------
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


# =========================================================
# PAGE 1 — HOME (Hero + Upload)
# =========================================================
def render_home():
    apply_backdrop("#7C6FE0", "#3FA9E8")

    st.markdown("""
        <div class="topbar">
            <div class="wordmark">HYBRID<span>·</span>RAG</div>
            <div class="navtag">DOCUMENT LAB</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="hero-anim">
            <div class="kicker">Upload once · compare three retrieval engines</div>
            <div class="hero-title">Chart your document</div>
            <div class="hero-rule" style="background:#8B93F5;"></div>
            <div class="hero-sub">
                Drop in a document and this app maps it three different ways —
                so you can see, side by side, how each method finds its way around.
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="legend-trio">
            <div class="legend-chip"><span class="legend-dot" style="background:#E85D75;"></span>RAG · vector retrieval</div>
            <div class="legend-chip"><span class="legend-dot" style="background:#E8B34F;"></span>OKF · linked knowledge</div>
            <div class="legend-chip"><span class="legend-dot" style="background:#3FA9E8;"></span>PageIndex · hierarchical reasoning</div>
        </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Choose a document",
        type=["pdf", "doc", "docx", "odt", "ppt", "pptx", "rtf", "epub", "xlsx", "ods", "odp", "csv"],
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
# Helper — recursively render a page index node as a tree
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
# PAGE 2 — WORKSPACE (stage-switching hero)
# =========================================================
def render_workspace():
    apply_backdrop(active["c1"], active["c2"])

    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<div class="wordmark">HYBRID<span>·</span>RAG</div>', unsafe_allow_html=True)
    with col2:
        if st.button("↺ New doc"):
            st.session_state.page = "home"
            st.session_state.uploaded_info = None
            st.session_state.messages = []
            st.session_state.page_index_data = None
            st.session_state.okf_files_data = None
            st.session_state.stage = "index"
            st.rerun()

    if st.session_state.uploaded_info:
        info = st.session_state.uploaded_info
        st.markdown('<div class="doc-info-label">Document</div>', unsafe_allow_html=True)
        meta_bits = []
        if info.get("total_pages"):
            meta_bits.append(f'{info["total_pages"]} pages')
        if info.get("total_words"):
            meta_bits.append(f'{info["total_words"]} words')
        meta_html = f'<span class="doc-info-dot">·</span>'.join(meta_bits) if meta_bits else "converted"
        st.markdown(
            f'<div class="doc-info-bar">'
            f'<span class="doc-info-name">📄 {info["filename"]}</span>'
            f'<span class="doc-info-meta">{meta_html}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    # ---------- Nav pills (stage switcher) ----------
    nav_cols = st.columns(len(STAGES))
    for i, s in enumerate(STAGES):
        with nav_cols[i]:
            is_active = s["key"] == st.session_state.stage
            if st.button(s["label"], key=f"nav_{s['key']}", type="primary" if is_active else "secondary", use_container_width=True):
                st.session_state.stage = s["key"]
                st.rerun()

    # ---------- Hero for active stage ----------
    st.markdown(f"""
        <div class="hero-anim">
            <div class="kicker" style="margin-top:1.8rem;">STAGE {active['num']} · {active['kicker']}</div>
            <div class="hero-title" style="font-size:2.3rem;">{active['label']}</div>
            <div class="hero-rule" style="background:{active['c1']};"></div>
        </div>
    """, unsafe_allow_html=True)

    idx = STAGES.index(active)
    prev_s = STAGES[idx - 1] if idx > 0 else None
    next_s = STAGES[idx + 1] if idx < len(STAGES) - 1 else None
    peek_cols = st.columns([1, 2, 1])
    with peek_cols[0]:
        if prev_s and st.button(f"← {prev_s['label']}", key="peek_prev"):
            st.session_state.stage = prev_s["key"]
            st.rerun()
    with peek_cols[2]:
        if next_s and st.button(f"{next_s['label']} →", key="peek_next"):
            st.session_state.stage = next_s["key"]
            st.rerun()

    st.write("")

    # ---------- Stage content ----------
    with st.container(border=True):

        if active["key"] == "index":
            if st.button("Build index", type="primary"):
                with st.spinner("Building index..."):
                    response = requests.post("http://127.0.0.1:8000/build-index")
                    result = response.json()
                if "error" in result:
                    st.error(f"❌ {result['error']}")
                else:
                    st.success(f"✅ Index built — {result.get('sections', 'N/A')} sections")

            st.markdown('<hr class="subsection-divider">', unsafe_allow_html=True)

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
            if st.button("Generate OKF", type="primary"):
                with st.spinner("Generating OKF structure..."):
                    response = requests.post("http://127.0.0.1:8000/generate-okf")
                    result = response.json()
                if "error" in result:
                    st.error(f"❌ {result['error']}")
                else:
                    st.success(f"✅ OKF generated — {result.get('files', 'N/A')} files")

            st.markdown('<hr class="subsection-divider">', unsafe_allow_html=True)

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
                st.chat_message(msg["role"]).write(msg["content"])

            question = st.chat_input("Type your question here...")

            if question:
                st.session_state.messages.append({"role": "user", "content": question})
                st.chat_message("user").write(question)

                with st.chat_message("assistant"):
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
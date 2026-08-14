import streamlit as st
import requests

st.set_page_config(
    page_title="Hybrid PageIndex RAG",
    page_icon="🌌",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Space Grotesk', sans-serif;
        }
        
        .stApp {
            background-image: 
                linear-gradient(rgba(10, 3, 20, 0.25), rgba(10, 3, 20, 0.5)),
                url('https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?auto=format&fit=crop&w=1920&q=90');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            background-repeat: no-repeat;
        }
        
        .main { padding-top: 2rem; }
        
        .hero {
            text-align: center;
            margin-bottom: 2rem;
        }
        .hero h1 {
            color: #FDF4FF;
            font-size: 2.6rem;
            font-weight: 700;
            margin: 0;
            letter-spacing: 0.02em;
            text-shadow: 
                0 0 20px rgba(240, 171, 252, 0.9),
                0 0 45px rgba(217, 70, 239, 0.6),
                0 0 90px rgba(139, 92, 246, 0.4);
            animation: starGlow 3s ease-in-out infinite alternate;
        }
        @keyframes starGlow {
            from { text-shadow: 0 0 20px rgba(240, 171, 252, 0.7), 0 0 40px rgba(217, 70, 239, 0.5), 0 0 80px rgba(139, 92, 246, 0.3); }
            to   { text-shadow: 0 0 30px rgba(240, 171, 252, 1), 0 0 55px rgba(217, 70, 239, 0.8), 0 0 100px rgba(139, 92, 246, 0.6); }
        }
        .hero p {
            color: #E9D5FF;
            font-size: 0.95rem;
            margin-top: 0.7rem;
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: 0.05em;
            text-shadow: 0 0 12px rgba(233, 213, 255, 0.5);
        }
        
        /* Overview card on page 1 */
        .overview-box {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(240, 171, 252, 0.2);
            border-radius: 16px;
            padding: 1.8rem;
            margin-bottom: 2rem;
            backdrop-filter: blur(6px);
        }
        .overview-box h3 {
            color: #F0ABFC;
            font-size: 1.1rem;
            margin-top: 0;
            text-shadow: 0 0 10px rgba(217, 70, 239, 0.4);
        }
        .overview-box p, .overview-box li {
            color: #E9D5FF;
            font-size: 0.92rem;
            line-height: 1.6;
        }
        
        .section-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: #FDF4FF;
            margin-bottom: 1.2rem;
            display: flex;
            align-items: center;
            gap: 0.8rem;
            text-shadow: 0 0 16px rgba(255, 255, 255, 0.3);
        }
        
        .star-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
            animation: twinkleStar 2.2s ease-in-out infinite alternate;
        }
        .star-upload {
            background: #FDE68A;
            box-shadow: 0 0 8px #FDE68A, 0 0 20px #F59E0B, 0 0 45px rgba(245, 158, 11, 0.7);
        }
        .star-index {
            background: #BAE6FD;
            box-shadow: 0 0 8px #BAE6FD, 0 0 20px #38BDF8, 0 0 45px rgba(56, 189, 248, 0.7);
        }
        .star-okf {
            background: #86EFAC;
            box-shadow: 0 0 8px #86EFAC, 0 0 20px #22C55E, 0 0 45px rgba(34, 197, 94, 0.7);
        }
        .star-ask {
            background: #F0ABFC;
            box-shadow: 0 0 8px #F0ABFC, 0 0 20px #D946EF, 0 0 45px rgba(217, 70, 239, 0.7);
        }
        @keyframes twinkleStar {
            from { opacity: 0.6; transform: scale(0.9); }
            to   { opacity: 1; transform: scale(1.25); }
        }
        
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        
        .divider-glow {
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(240, 171, 252, 0.5), transparent);
            margin: 2.5rem 0;
            box-shadow: 0 0 10px rgba(240, 171, 252, 0.4);
        }
        
        p, span, label, .stMarkdown { color: #F3E8FF !important; }
        
        .stButton>button {
            width: 100%;
            border-radius: 30px;
            height: 3em;
            background: rgba(217, 70, 239, 0.12);
            color: #FDF4FF;
            font-weight: 600;
            border: 1px solid rgba(240, 171, 252, 0.5);
            box-shadow: 0 0 16px rgba(217, 70, 239, 0.35);
            transition: all 0.3s;
        }
        .stButton>button:hover {
            background: rgba(217, 70, 239, 0.25);
            box-shadow: 0 0 28px rgba(240, 171, 252, 0.7);
            transform: translateY(-2px);
        }
        
        [data-testid="stFileUploaderDropzone"] {
            background: rgba(255, 255, 255, 0.02) !important;
            border: 1px dashed rgba(240, 171, 252, 0.35) !important;
            border-radius: 14px !important;
        }
        
        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(240, 171, 252, 0.2);
            border-radius: 12px;
            padding: 0.8rem;
        }
        [data-testid="stMetricValue"] { 
            color: #F0ABFC !important; 
            text-shadow: 0 0 12px rgba(217, 70, 239, 0.6);
        }
        [data-testid="stMetricLabel"] { color: #E9D5FF !important; }
        
        [data-testid="stChatInput"] {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 14px;
            border: 1px solid rgba(240, 171, 252, 0.2) !important;
        }
        [data-testid="stChatMessage"] {
            background: rgba(255, 255, 255, 0.02) !important;
            border-radius: 14px;
            border: 1px solid rgba(240, 171, 252, 0.12);
        }
        
        [data-testid="stAlert"] {
            background: rgba(255, 255, 255, 0.03) !important;
            border-radius: 12px;
            backdrop-filter: blur(3px);
        }
        
        .file-badge {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(240, 171, 252, 0.25);
            border-radius: 12px;
            padding: 0.6rem 1rem;
            font-size: 0.85rem;
            color: #E9D5FF;
            margin-bottom: 1.5rem;
            display: inline-block;
        }
    </style>
""", unsafe_allow_html=True)

# ---------- Session state setup ----------
if "page" not in st.session_state:
    st.session_state.page = "home"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_info" not in st.session_state:
    st.session_state.uploaded_info = None


# =========================================================
# PAGE 1 — HOME (Overview + Upload)
# =========================================================
def render_home():
    st.markdown("""
        <div class="hero">
            <h1>🌌 HYBRID PAGEINDEX RAG</h1>
            <p>>> upload · index · query — powered by RAG / OKF / PageIndex</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="overview-box">
            <h3>What this app does</h3>
            <p>
                This app lets you upload a document and ask questions about it — combining three retrieval
                approaches to compare how well each understands your document:
            </p>
            <p>
                📄 <b>RAG</b> — chunks your document and retrieves relevant parts using vector similarity<br>
                🗂️ <b>OKF</b> — organizes content into a linked, structured knowledge format<br>
                🌳 <b>PageIndex</b> — builds a hierarchical index and reasons over it like a table of contents
            </p>
            <p>
                Upload a PDF below to get started — you'll be taken to the workspace where you can
                build an index and start asking questions.
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title"><span class="star-dot star-upload"></span> Upload Document</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf", label_visibility="collapsed")

    if uploaded_file is not None:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"📄 **{uploaded_file.name}** · {uploaded_file.size / 1024:.1f} KB")
        with col2:
            upload_clicked = st.button("Upload", use_container_width=True)

        if upload_clicked:
            with st.spinner("Parsing document..."):
                files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
                response = requests.post("http://127.0.0.1:8000/upload", files=files)
                result = response.json()

            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                st.session_state.uploaded_info = result
                st.success(f"✅ Parsed successfully — {result['total_pages']} pages, {result['total_words']} words")
                st.session_state.page = "workspace"
                st.rerun()


# =========================================================
# PAGE 2 — WORKSPACE (Build Index, Generate OKF, Ask)
# =========================================================
def render_workspace():
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("""
            <div class="hero" style="text-align:left; margin-bottom: 1rem;">
                <h1 style="font-size: 1.8rem;">🌌 Workspace</h1>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("⬅ New doc"):
            st.session_state.page = "home"
            st.session_state.uploaded_info = None
            st.session_state.messages = []
            st.rerun()

    if st.session_state.uploaded_info:
        info = st.session_state.uploaded_info
        st.markdown(
            f'<div class="file-badge">📄 {info["filename"]} · {info["total_pages"]} pages · {info["total_words"]} words</div>',
            unsafe_allow_html=True
        )

    # ---------- Build Index ----------
    with st.container(border=True):
        st.markdown('<div class="section-title"><span class="star-dot star-index"></span> Build Index</div>', unsafe_allow_html=True)

        if st.button("🔨 Build Index"):
            with st.spinner("Building index..."):
                response = requests.post("http://127.0.0.1:8000/build-index")
                result = response.json()
            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                st.success(f"✅ Index built — {result.get('sections', 'N/A')} sections")

    st.markdown('<div class="divider-glow"></div>', unsafe_allow_html=True)

    # ---------- Generate OKF ----------
    with st.container(border=True):
        st.markdown('<div class="section-title"><span class="star-dot star-okf"></span> Generate OKF</div>', unsafe_allow_html=True)

        if st.button("🗂️ Generate OKF"):
            with st.spinner("Generating OKF structure..."):
                response = requests.post("http://127.0.0.1:8000/generate-okf")
                result = response.json()
            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                st.success(f"✅ OKF generated — {result.get('files', 'N/A')} files")

    st.markdown('<div class="divider-glow"></div>', unsafe_allow_html=True)

    # ---------- Ask a Question ----------
    with st.container(border=True):
        st.markdown('<div class="section-title"><span class="star-dot star-ask"></span> Ask a Question</div>', unsafe_allow_html=True)

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
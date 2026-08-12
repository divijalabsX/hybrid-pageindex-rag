import streamlit as st
import requests

st.title("Hybrid PageIndex RAG")

# Upload section
st.header("Upload PDF")
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    if st.button("Upload"):
        files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
        response = requests.post("http://127.0.0.1:8000/upload", files=files)
        st.success(f"Uploaded: {response.json()}")

# Build Index section
st.header("Build Index")
if st.button("Build Index"):
    with st.spinner("Processing..."):
        response = requests.post("http://127.0.0.1:8000/build-index")
        st.success(f"Index built: {response.json()}")

# Chat section
st.header("Ask a Question")
question = st.chat_input("Type your question here")

if question:
    st.chat_message("user").write(question)
    response = requests.post("http://127.0.0.1:8000/ask", params={"question": question})
    answer = response.json().get("answer", "No answer received")
    st.chat_message("assistant").write(answer)
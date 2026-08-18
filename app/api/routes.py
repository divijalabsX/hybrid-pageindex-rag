from fastapi import APIRouter, UploadFile, File
import os
import json
from app.parser.pdf_parser import parse_pdf
from app.llm.gemini_client import generate_text
from app.indexer.page_index import create_llm_page_index, save_page_index
from app.okf.okf_generator import load_page_index, node_to_okf, write_okf_item

router = APIRouter()

# Global variable — upload hui pages temporarily yahan store honge
# (production mein isse better session/db management chahiye hoga, abhi ke liye simple)
current_pages = []
current_filename = None


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    global current_pages, current_filename
    try:
        os.makedirs("data/uploads", exist_ok=True)
        file_path = f"data/uploads/{file.filename}"

        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        pages = parse_pdf(file_path)
        current_pages = pages
        current_filename = file.filename
        total_words = sum(p.word_count for p in pages)

        return {
            "filename": file.filename,
            "total_pages": len(pages),
            "total_words": total_words
        }
    except FileNotFoundError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}


@router.post("/build-index")
async def build_index():
    global current_pages
    if not current_pages:
        return {"error": "No document uploaded yet. Please upload a PDF first."}

    try:
        page_index = create_llm_page_index(current_pages)
        save_page_index(page_index, "data/pageindex/index.json")

        def count_nodes(node):
            return 1 + sum(count_nodes(child) for child in node.nodes)

        total_sections = count_nodes(page_index) - 1  # root exclude

        return {"status": "index built", "sections": total_sections}
    except Exception as e:
        return {"error": f"Failed to build index: {str(e)}"}


@router.post("/generate-okf")
async def generate_okf():
    global current_filename

    index_path = "data/pageindex/index.json"
    if not os.path.exists(index_path):
        return {"error": "No page index found. Please build the index first."}

    try:
        page_index = load_page_index(index_path)
        source = current_filename or "document"

        okf_root = node_to_okf(page_index, source)

        output_dir = "data/okf"
        files_written = []

        def write_recursive(item, is_root=False):
            path = write_okf_item(item, output_dir, is_root=is_root)
            files_written.append(path)
            for child in item.children:
                write_recursive(child, is_root=False)

        write_recursive(okf_root, is_root=True)

        return {"status": "okf generated", "files": len(files_written)}
    except Exception as e:
        return {"error": f"Failed to generate OKF: {str(e)}"}


@router.get("/page-index")
async def get_page_index():
    index_path = "data/pageindex/index.json"
    if not os.path.exists(index_path):
        return {"error": "No page index found. Please build the index first."}

    try:
        with open(index_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {"index": data}
    except Exception as e:
        return {"error": f"Failed to load page index: {str(e)}"}


@router.get("/okf-files")
async def get_okf_files():
    okf_dir = "data/okf"
    if not os.path.exists(okf_dir):
        return {"error": "No OKF files found. Please generate OKF first."}

    try:
        files_data = []
        for filename in sorted(os.listdir(okf_dir)):
            if filename.endswith(".md"):
                file_path = os.path.join(okf_dir, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                files_data.append({"filename": filename, "content": content})

        return {"files": files_data}
    except Exception as e:
        return {"error": f"Failed to load OKF files: {str(e)}"}


@router.post("/ask")
async def ask_question(question: str):
    global current_pages

    if not current_pages:
        return {"answer": "Please upload a document first before asking questions."}

    try:
        document_text = "\n\n".join(
            [f"Page {p.page_number}: {p.text}" for p in current_pages]
        )

        prompt = f"""Answer the question based on the following document content.

DOCUMENT:
{document_text}

QUESTION: {question}

Answer based only on the document content above."""

        answer = generate_text(prompt)
        return {"answer": answer}
    except Exception as e:
        return {"error": f"Failed to generate answer: {str(e)}"}
from fastapi import APIRouter, UploadFile, File
import os
import json
from app.parser.pdf_parser import parse_pdf
from app.parser.document_parser import parse_document
from app.parser.markdown_chunker import chunk_markdown_to_pages
from app.llm.gemini_client import generate_text
from app.indexer.page_index import create_llm_page_index, save_page_index
from app.okf.okf_generator import load_page_index, node_to_okf, write_okf_item

router = APIRouter()

# Global variable — uploaded PDF pages temporarily stored here.
current_pages = []
current_filename = None
current_markdown = None


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    global current_pages, current_filename, current_markdown
    try:
        os.makedirs("data/uploads", exist_ok=True)
        os.makedirs("data/markdown", exist_ok=True)

        file_path = f"data/uploads/{file.filename}"

        contents = await file.read()

        with open(file_path, "wb") as f:
            f.write(contents)

        # Convert the uploaded document into standard Markdown using AnyDoc.
        markdown = parse_document(file_path)

        markdown_filename = f"{file.filename}.md"
        markdown_path = f"data/markdown/{markdown_filename}"

        with open(markdown_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        current_filename = file.filename
        current_markdown = markdown

        # Parse PDF pages for the existing PageIndex/RAG pipeline.
        if file.filename.lower().endswith(".pdf"):
            pages = parse_pdf(file_path)
            current_pages = pages
            total_pages = len(pages)
            total_words = sum(p.word_count for p in pages)
        else:
            # Non-PDF upload: chunk the converted Markdown into artificial
            # "pages" so the same PageIndex/RAG pipeline used for PDFs
            # (which only needs page_number/text/word_count) also works
            # here. This replaces any stale pages from a previous document.
            pages = chunk_markdown_to_pages(markdown)
            current_pages = pages
            total_pages = len(pages)
            total_words = sum(p.word_count for p in pages)

        return {
            "filename": file.filename,
            "status": "converted",
            "markdown_file": markdown_filename,
            "characters": len(markdown),
            "total_pages": total_pages,
            "total_words": total_words,
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

        total_sections = count_nodes(page_index) - 1

        return {
            "status": "index built",
            "sections": total_sections
        }

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
    global current_pages, current_markdown

    if not current_pages and not current_markdown:
        return {
            "answer": "Please upload a document first before asking questions."
        }

    try:
        if current_pages:
            document_text = "\n\n".join(
                [f"Page {p.page_number}: {p.text}" for p in current_pages]
            )
        else:
            document_text = current_markdown

        prompt = f"""Answer the question based on the following document content.

DOCUMENT:
{document_text}

QUESTION: {question}

Answer based only on the document content above."""

        answer = generate_text(prompt)

        return {"answer": answer}

    except Exception as e:
        return {"error": f"Failed to generate answer: {str(e)}"}
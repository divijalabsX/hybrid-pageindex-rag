from fastapi import APIRouter, UploadFile, File
import os
import json

from streamlit import markdown

from app.parser.pdf_parser import parse_pdf
from app.parser.xlsx_parser import parse_xlsx_to_pages
from app.parser.document_parser import (
    parse_document,
    parse_document_to_canonical,
)
from app.parser.markdown_chunker import chunk_markdown_to_pages

from app.llm.ollama_client import generate_text

from app.config.settings import USE_GEMINI

from app.indexer.page_index import (
    create_llm_page_index,
    create_ollama_page_index,
    load_page_index,
    retrieve_relevant_pages,
    create_canonical_page_index,
    save_page_index,
)

from app.okf.okf_generator import (
    load_page_index,
    node_to_okf,
    write_okf_item,
)
from pageindex.tree_optimize import pages


router = APIRouter()


# Global variables — uploaded document data temporarily stored here.
current_pages = []
current_filename = None
current_markdown = None
current_canonical_document = None


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    global current_pages, current_filename, current_markdown
    global current_canonical_document

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

        # Build the canonical structured representation using AnyDoc.
        # This preserves semantic information such as:
        # headings, heading levels, paragraphs, tables and lists
        # whenever the source format exposes that information.
        current_canonical_document = parse_document_to_canonical(
            file_path
        )

        # ---------------------------------------------------------
        # PDF
        # ---------------------------------------------------------

        if file.filename.lower().endswith(".pdf"):

            pages = parse_pdf(file_path)

        # ---------------------------------------------------------
        # XLSX
        # ---------------------------------------------------------

        elif file.filename.lower().endswith(".xlsx"):

            pages = parse_xlsx_to_pages(
            file_path
            )

        # ---------------------------------------------------------
        # Other formats
        # ---------------------------------------------------------

        else:

            pages = chunk_markdown_to_pages(
                markdown
            )

        current_pages = pages

        total_pages = len(pages)

        total_words = sum(
            p.word_count
            for p in pages
        )

        return {
            "filename": file.filename,
            "status": "converted",
            "markdown_file": markdown_filename,
            "characters": len(markdown),
            "total_pages": total_pages,
            "total_words": total_words,
        }

    except FileNotFoundError as e:

        return {
            "error": str(e)
        }

    except ValueError as e:

        return {
            "error": str(e)
        }


@router.post("/build-index")
async def build_index():
    global current_pages, current_filename, current_canonical_document

    if not current_pages:
        return {
            "error": "No document uploaded yet. Please upload a document first."
        }

    try:

        # ---------------------------------------------------------
        # PDF documents use the existing PageIndex pipeline.
        #
        # Non-PDF documents first use AnyDoc's explicit structure.
        #
        # If the canonical document has no explicit headings,
        # fall back to Ollama/Qwen.
        # ---------------------------------------------------------

        is_pdf = (
            current_filename
            and current_filename.lower().endswith(".pdf")
        )

        if not is_pdf and current_canonical_document is not None:

            try:

                print(
                    "\n[BUILD-INDEX] Trying canonical document structure..."
                )

                page_index = create_canonical_page_index(
                    current_canonical_document,
                    current_pages
                )

                pipeline = "Canonical/AnyDoc"

                print(
                    "[BUILD-INDEX] Using explicit structure from AnyDoc."
                )

            except ValueError as e:

                print(
                    f"\n[BUILD-INDEX] Canonical structure unavailable: {e}"
                )

                print(
                    "[BUILD-INDEX] Falling back to Ollama/Qwen..."
                )

                page_index = create_ollama_page_index(
                    current_pages
                )

                pipeline = "Ollama/Qwen fallback"

        else:

            # -----------------------------------------------------
            # Existing PDF pipeline.
            # -----------------------------------------------------

            if USE_GEMINI:

                print(
                    "\n[BUILD-INDEX] Using Gemini pipeline..."
                )

                page_index = create_llm_page_index(
                    current_pages
                )

                pipeline = "Gemini"

            else:

                print(
                    "\n[BUILD-INDEX] Using Ollama/Qwen pipeline..."
                )

                page_index = create_ollama_page_index(
                    current_pages
                )

                pipeline = "Ollama/Qwen"

        # ---------------------------------------------------------
        # Save the generated PageIndex.
        # ---------------------------------------------------------

        save_page_index(
            page_index,
            "data/pageindex/index.json"
        )

        # ---------------------------------------------------------
        # Count all non-root nodes.
        # ---------------------------------------------------------

        def count_nodes(node):
            return 1 + sum(
                count_nodes(child)
                for child in node.nodes
            )

        total_sections = count_nodes(
            page_index
        ) - 1

        print(
            f"[BUILD-INDEX] Index built successfully using {pipeline}"
        )

        return {
            "status": "index built",
            "sections": total_sections,
            "pipeline": pipeline,
        }

    except Exception as e:

        print(
            f"[BUILD-INDEX] Failed: {str(e)}"
        )

        return {
            "error": f"Failed to build index: {str(e)}"
        }


@router.post("/generate-okf")
async def generate_okf():
    global current_filename

    index_path = "data/pageindex/index.json"

    if not os.path.exists(index_path):

        return {
            "error": "No page index found. Please build the index first."
        }

    try:

        page_index = load_page_index(
            index_path
        )

        source = (
            current_filename
            or "document"
        )

        okf_root = node_to_okf(
            page_index,
            source
        )

        output_dir = "data/okf"

        # Clear previously generated OKF files before creating
        # the OKF for the newly uploaded document.
        os.makedirs(output_dir, exist_ok=True)

        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)

            if os.path.isfile(file_path) and filename.endswith(".md"):
                os.remove(file_path)

        files_written = []

        def write_recursive(
            item,
            is_root=False
        ):

            path = write_okf_item(
                item,
                output_dir,
                is_root=is_root
            )

            files_written.append(path)

            for child in item.children:

                write_recursive(
                    child,
                    is_root=False
                )

        write_recursive(
            okf_root,
            is_root=True
        )

        return {
            "status": "okf generated",
            "files": len(files_written)
        }

    except Exception as e:

        return {
            "error": f"Failed to generate OKF: {str(e)}"
        }


@router.get("/page-index")
async def get_page_index():

    index_path = "data/pageindex/index.json"

    if not os.path.exists(index_path):

        return {
            "error": "No page index found. Please build the index first."
        }

    try:

        with open(
            index_path,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        return {
            "index": data
        }

    except Exception as e:

        return {
            "error": f"Failed to load page index: {str(e)}"
        }


@router.get("/okf-files")
async def get_okf_files():

    okf_dir = "data/okf"

    if not os.path.exists(okf_dir):

        return {
            "error": "No OKF files found. Please generate OKF first."
        }

    try:

        files_data = []

        for filename in sorted(
            os.listdir(okf_dir)
        ):

            if filename.endswith(".md"):

                file_path = os.path.join(
                    okf_dir,
                    filename
                )

                with open(
                    file_path,
                    "r",
                    encoding="utf-8"
                ) as f:

                    content = f.read()

                files_data.append(
                    {
                        "filename": filename,
                        "content": content
                    }
                )

        return {
            "files": files_data
        }

    except Exception as e:

        return {
            "error": f"Failed to load OKF files: {str(e)}"
        }


@router.post("/ask")
async def ask_question(question: str):
    global current_pages, current_markdown

    if not current_pages and not current_markdown:
        return {
            "answer": "Please upload a document first before asking questions."
        }

    try:
        # Use PageIndex-based retrieval when pages are available
        if current_pages:
            page_index = load_page_index(
                "data/pageindex/index.json"
            )

            relevant_pages = retrieve_relevant_pages(
                question=question,
                pages=current_pages,
                page_index=page_index,
                top_k=2
            )

            # If no keyword matches are found, fall back to first page
            if not relevant_pages:
                relevant_pages = current_pages[:1]

            document_text = "\n\n".join(
                [
                    f"Page {p.page_number}: {p.text}"
                    for p in relevant_pages
                ]
            )

        else:
            document_text = current_markdown

        prompt = f"""Answer the question based only on the provided document content.

DOCUMENT:
{document_text}

QUESTION:
{question}

Give a concise and accurate answer. If the answer is not present in the document, say that it is not found in the provided document."""

        answer = generate_text(prompt)

        print(f"[ASK] Ollama answer: {repr(answer)}")

        return {
            "answer": answer
        }

    except Exception as e:
        print(f"[ASK] Failed: {str(e)}")
        return {
            "error": f"Failed to generate answer: {str(e)}"
        }
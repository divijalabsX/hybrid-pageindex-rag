from fastapi import APIRouter, UploadFile, File
import os
from app.parser.pdf_parser import parse_pdf
from app.llm.gemini_client import generate_text
from app.indexer.page_index import create_llm_page_index, save_page_index

router = APIRouter()

# Global variable — upload hui pages temporarily yahan store honge
# (production mein isse better session/db management chahiye hoga, abhi ke liye simple)
current_pages = []


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    global current_pages
    try:
        os.makedirs("data/uploads", exist_ok=True)
        file_path = f"data/uploads/{file.filename}"

        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        pages = parse_pdf(file_path)
        current_pages = pages
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
    return {"status": "okf generated", "files": 8}


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
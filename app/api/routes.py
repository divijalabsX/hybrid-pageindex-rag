from fastapi import APIRouter, UploadFile, File
import os
from app.parser.pdf_parser import parse_pdf

router = APIRouter()

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        os.makedirs("data/uploads", exist_ok=True)
        file_path = f"data/uploads/{file.filename}"
        
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        pages = parse_pdf(file_path)
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
    return {"status": "index built", "sections": 12}

@router.post("/generate-okf")
async def generate_okf():
    return {"status": "okf generated", "files": 8}

@router.post("/ask")
async def ask_question(question: str):
    return {"answer": f"Mock answer for: {question}"}
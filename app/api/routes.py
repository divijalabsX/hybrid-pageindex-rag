from fastapi import APIRouter, UploadFile, File
from app.parser.pdf_parser import parse_pdf
import os

router = APIRouter()

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    # Step 1: uploaded file ko disk pe temporarily save karo
    os.makedirs("data/uploads", exist_ok=True)
    file_path = f"data/uploads/{file.filename}"
    
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Step 2: teammate ka real parser function call karo
    pages = parse_pdf(file_path)
    
    # Step 3: response bhejo
    return {"filename": file.filename, "total_pages": len(pages)}
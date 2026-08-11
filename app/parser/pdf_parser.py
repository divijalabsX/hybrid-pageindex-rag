import os

import fitz

from app.models.page import Page


def parse_pdf(file_path: str) -> list[Page]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    if not file_path.lower().endswith(".pdf"):
        raise ValueError("The provided file is not a PDF.")

    try:
        document = fitz.open(file_path)
    except Exception as e:
        raise ValueError(f"Unable to open PDF: {e}")

    pages = []

    for page_number, pdf_page in enumerate(document, start=1):
        text = pdf_page.get_text().strip()

        if not text:
            print(f"Warning: Page {page_number} contains no extractable text.")

        page = Page(
    page_number=page_number,
    text=text,
    word_count=len(text.split()),
    char_count=len(text)
)

        pages.append(page)

    document.close()

    return pages
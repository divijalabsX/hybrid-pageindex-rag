import fitz

from app.models.page import Page


def parse_pdf(file_path: str) -> list[Page]:
    pages = []

    document = fitz.open(file_path)

    for page_number, pdf_page in enumerate(document, start=1):
        text = pdf_page.get_text()

        page = Page(
            page_number=page_number,
            text=text,
            word_count=len(text.split())
        )

        pages.append(page)

    document.close()

    return pages
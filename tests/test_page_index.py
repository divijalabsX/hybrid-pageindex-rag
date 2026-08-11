from app.parser.pdf_parser import parse_pdf
from app.indexer.page_index import (
    create_llm_page_index,
    save_page_index
)


PDF_PATH = "data/uploads/sample.pdf"
OUTPUT_PATH = "data/pageindex/pageindex.json"


pages = parse_pdf(PDF_PATH)

print(f"Parsed {len(pages)} pages.")

page_index = create_llm_page_index(pages)

save_page_index(
    page_index,
    OUTPUT_PATH
)

print(f"PageIndex saved to: {OUTPUT_PATH}")
from app.parser.pdf_parser import parse_pdf


PDF_PATH = "data/uploads/sample.pdf"


pages = parse_pdf(PDF_PATH)

print(f"Total pages: {len(pages)}")

if pages:
    print("\nFirst page:")
    print(f"Page number: {pages[0].page_number}")
    print(f"Word count: {pages[0].word_count}")
    print(f"Text preview:\n{pages[0].text[:500]}")
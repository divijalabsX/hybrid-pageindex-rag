import fitz

from app.parser.pdf_parser import parse_pdf


def test_parse_pdf(tmp_path):
    pdf_path = tmp_path / "sample.pdf"

    # Create a small test PDF dynamically.
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "This is a test PDF document.")
    document.save(pdf_path)
    document.close()

    pages = parse_pdf(str(pdf_path))

    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert pages[0].word_count > 0
    assert pages[0].char_count > 0
    assert "test PDF document" in pages[0].text
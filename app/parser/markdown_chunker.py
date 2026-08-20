from app.models.page import Page

# Roughly how many characters go into one artificial "page".
# Kept modest so each page stays well within LLM prompt limits
# and the resulting PageIndex has a sensible number of pages.
DEFAULT_CHUNK_SIZE = 3000


def chunk_markdown_to_pages(markdown: str, chunk_size: int = DEFAULT_CHUNK_SIZE) -> list[Page]:
    """
    Split converted Markdown (from anydoc, for non-PDF documents) into
    artificial "pages" so it can be fed into the same PageIndex / RAG
    pipeline that expects a list[Page] (normally produced by parse_pdf).

    We split on paragraph boundaries (blank lines) so we don't cut a
    sentence in half, and accumulate paragraphs until we hit roughly
    chunk_size characters, then start a new page.
    """
    paragraphs = [p for p in markdown.split("\n\n") if p.strip()]

    if not paragraphs:
        return []

    pages: list[Page] = []
    current_paragraphs: list[str] = []
    current_length = 0
    page_number = 1

    for paragraph in paragraphs:
        paragraph_length = len(paragraph)

        if current_paragraphs and current_length + paragraph_length > chunk_size:
            page_text = "\n\n".join(current_paragraphs).strip()
            pages.append(
                Page(
                    page_number=page_number,
                    text=page_text,
                    word_count=len(page_text.split()),
                    char_count=len(page_text),
                )
            )
            page_number += 1
            current_paragraphs = []
            current_length = 0

        current_paragraphs.append(paragraph)
        current_length += paragraph_length

    if current_paragraphs:
        page_text = "\n\n".join(current_paragraphs).strip()
        pages.append(
            Page(
                page_number=page_number,
                text=page_text,
                word_count=len(page_text.split()),
                char_count=len(page_text),
            )
        )

    return pages
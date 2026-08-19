from app.models.page import Page


def parse_markdown_pages(markdown: str) -> list[Page]:
    """
    Convert AnyDoc-generated Markdown into logical Page objects.

    These are logical document units, not physical PDF pages.
    """

    if not markdown or not markdown.strip():
        return []

    lines = markdown.splitlines()

    chunks = []
    current_chunk = []

    for line in lines:
        stripped = line.strip()

        # Ignore completely empty lines unless we already
        # have meaningful content.
        if not stripped:
            if current_chunk:
                current_chunk.append("")
            continue

        current_chunk.append(line)

        # A Markdown heading starts a new logical section.
        # We don't split before the first heading.
        if (
            len(current_chunk) > 1
            and stripped.startswith("# ")
        ):
            chunks.append("\n".join(current_chunk[:-1]).strip())
            current_chunk = [line]

    if current_chunk:
        chunk = "\n".join(current_chunk).strip()
        if chunk:
            chunks.append(chunk)

    # If there were no headings, keep the whole document
    # as one logical page.
    if not chunks:
        chunks = [markdown.strip()]

    pages = []

    for page_number, text in enumerate(chunks, start=1):
        pages.append(
            Page(
                page_number=page_number,
                text=text,
                word_count=len(text.split()),
                char_count=len(text),
            )
        )

    return pages
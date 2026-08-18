import re
from dataclasses import dataclass, field


@dataclass
class Section:
    title: str
    level: int
    content: str = ""
    start_page: int | None = None
    end_page: int | None = None
    children: list["Section"] = field(default_factory=list)

@dataclass
class StructuredDocument:
    title: str
    sections: list[Section] = field(default_factory=list)


def parse_markdown(markdown: str) -> StructuredDocument:
    """
    Convert Markdown into a hierarchical document structure.

    Only meaningful document headings are treated as sections.
    """

    lines = markdown.splitlines()

    document_title = "Untitled Document"
    root_sections = []
    stack = []

    for line in lines:
        line = line.strip()

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", line)

        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()

            # First # heading becomes the document title.
            if level == 1 and document_title == "Untitled Document":
                document_title = title
                continue

            # Ignore empty/separator headings such as:
            # ### --------------------
            if not title or re.fullmatch(r"[-_=]+", title):
                continue

            # Ignore metadata headings before the actual sections.
            # For this document, numbered sections and Abstract
            # represent meaningful structure.
            is_numbered_section = bool(
                re.match(r"^\d+(\.\d+)*\.?\s+", title)
            )

            is_abstract = title.lower() == "abstract"

            if not is_numbered_section and not is_abstract:
                continue

            section = Section(
                title=title,
                level=level
            )

            while stack and stack[-1].level >= level:
                stack.pop()

            if stack:
                stack[-1].children.append(section)
            else:
                root_sections.append(section)

            stack.append(section)

        else:
            # Normal text belongs to the current section.
            if stack and line:
                if stack[-1].content:
                    stack[-1].content += "\n"

                stack[-1].content += line

    return StructuredDocument(
        title=document_title,
        sections=root_sections
    )

def map_sections_to_pages(
    document: StructuredDocument,
    pages: list
) -> StructuredDocument:
    """
    Map each top-level section to the PDF pages where it appears.
    """

    for section in document.sections:

        matching_pages = [
            page.page_number
            for page in pages
            if section.title.lower() in page.text.lower()
        ]

        if matching_pages:
            section.start_page = min(matching_pages)

    # Determine end pages using the next section's start page.
    for index, section in enumerate(document.sections):

        if section.start_page is None:
            continue

        if index + 1 < len(document.sections):
            next_section = document.sections[index + 1]

        if next_section.start_page is not None:
           section.end_page = max(
                section.start_page,
                next_section.start_page - 1
       )
        else:
            section.end_page = section.start_page
    else:
        section.end_page = pages[-1].page_number

    return document
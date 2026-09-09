import os
import statistics
from pathlib import Path
import re

import fitz

from app.models.page import Page
from app.parser.canonical_document import (
    CanonicalDocument,
    DocumentBlock,
    DocumentImage,
)


# ============================================================
# BASIC PDF PAGE PARSER
# ============================================================

def parse_pdf(file_path: str) -> list[Page]:

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"PDF file not found: {file_path}"
        )

    if not file_path.lower().endswith(".pdf"):
        raise ValueError(
            "The provided file is not a PDF."
        )

    try:
        document = fitz.open(file_path)

    except Exception as e:
        raise ValueError(
            f"Unable to open PDF: {e}"
        )

    pages = []

    for page_number, pdf_page in enumerate(
        document,
        start=1
    ):

        text = pdf_page.get_text().strip()

        if not text:
            print(
                f"Warning: Page {page_number} "
                f"contains no extractable text."
            )

        page = Page(
            page_number=page_number,
            text=text,
            word_count=len(text.split()),
            char_count=len(text),
        )

        pages.append(page)

    document.close()

    return pages


# ============================================================
# TEXT STRUCTURE HELPERS
# ============================================================

def _extract_text_lines(pdf_page) -> list[dict]:
    """
    Extract individual visual text lines from a PDF page.

    Also merges Roman-numbered headings that some PDFs store
    as separate visual lines, for example:

        I.
        I NTRODUCTION

    into:

        I. INTRODUCTION
    """

    page_dict = pdf_page.get_text("dict")

    lines = []

    for block in page_dict.get("blocks", []):

        # Ignore image blocks.
        if block.get("type") != 0:
            continue

        for line in block.get("lines", []):

            spans = line.get("spans", [])

            if not spans:
                continue

            text_parts = []
            font_sizes = []
            bold = False

            for span in spans:

                text = span.get("text", "")

                if not text.strip():
                    continue

                text_parts.append(text)

                font_sizes.append(
                    span.get("size", 0)
                )

                font_name = span.get(
                    "font",
                    ""
                ).lower()

                if (
                    "bold" in font_name
                    or "black" in font_name
                    or "heavy" in font_name
                ):
                    bold = True

            text = "".join(text_parts).strip()

            if not text:
                continue

            if font_sizes:
                font_size = max(font_sizes)
            else:
                font_size = 0

            bbox = line.get(
                "bbox",
                [0, 0, 0, 0]
            )

            lines.append(
                {
                    "text": text,
                    "font_size": font_size,
                    "bold": bold,
                    "bbox": bbox,
                }
            )

    # --------------------------------------------------------
    # Merge Roman-numbered headings split across PDF lines.
    #
    # Example:
    #   I.
    #   I NTRODUCTION
    #
    # becomes:
    #   I. INTRODUCTION
    # --------------------------------------------------------

    merged_lines = []

    i = 0

    while i < len(lines):

        current = lines[i]

        roman_match = re.match(
            r"^([IVXLCDM]+)\.\s*$",
            current["text"],
            re.IGNORECASE
        )

        if (
            roman_match
            and i + 1 < len(lines)
        ):
            next_line = lines[i + 1]

            next_text = next_line["text"].strip()

            # The following line should look like a heading:
            # reasonably short and not sentence-like.
            next_words = next_text.split()

            if (
                next_text
                and len(next_words) <= 12
                and not next_text.endswith(
                    (".", "?", "!", ",", ";", ":")
                )
            ):
                merged_lines.append(
                    {
                        "text": (
                            roman_match.group(1)
                            + ". "
                            + next_text
                        ),
                        "font_size": max(
                            current["font_size"],
                            next_line["font_size"]
                        ),
                        "bold": (
                            current["bold"]
                            or next_line["bold"]
                        ),
                        "bbox": [
                            min(
                                current["bbox"][0],
                                next_line["bbox"][0]
                            ),
                            min(
                                current["bbox"][1],
                                next_line["bbox"][1]
                            ),
                            max(
                                current["bbox"][2],
                                next_line["bbox"][2]
                            ),
                            max(
                                current["bbox"][3],
                                next_line["bbox"][3]
                            ),
                        ],
                    }
                )

                i += 2
                continue

        merged_lines.append(current)
        i += 1

    return merged_lines

def _looks_like_numbered_heading(text: str) -> bool:
    stripped = text.strip()

    # Arabic numbering:
    # 1. Something
    # 12. Something
    match = re.match(r"^\d+\.\s+(.+)$", stripped)

    if match:
        title = match.group(1).strip()

        words = title.split()

        if len(words) > 12:
            return False

        if title.endswith((".", ",", ";", ":")):
            return False

        return True

    # Roman numbering:
    # I. Introduction
    # II. Resume of Hotel Room
    # III. The Art and Technique...
    roman_match = re.match(
        r"^(?=[IVXLCDM]+\.)[IVXLCDM]+\.\s+(.+)$",
        stripped,
        re.IGNORECASE
    )

    if roman_match:
        title = roman_match.group(1).strip()

        words = title.split()

        if len(words) > 12:
            return False

        if title.endswith((".", ",", ";", ":")):
            return False

        return True

    return False

def _looks_like_heading(
    line: dict,
    body_font_size: float
) -> bool:
    """
    Conservative heading detector for PDFs.

    Recognizes:
    - Arabic numbered headings: 1., 2., 3.
    - Roman numbered headings: I., II., III.
    - Alphabetic subsections: A., B., C.
    - Visually prominent unnumbered headings

    Avoids promoting ordinary paragraph fragments merely
    because they are bold.
    """

    text = line["text"].strip()

    if not text:
        return False

    # --------------------------------------------------------
    # Obvious non-heading content
    # --------------------------------------------------------

    if text.startswith(
        "International Journal of Scientific Research"
    ):
        return False

    if text.startswith(("Fig ", "Fig. ")):
        return False

    if text.startswith(
        ("Ms. ", "Mr. ", "Mrs. ", "Dr. ")
    ):
        return False

    if text.startswith(
        ("â€¢", "â—", "â–ª", "â—¦", "â€£", "o")
    ):
        return False

    # Very long text is paragraph content.
    if len(text) > 100:
        return False

    if text.isdigit():
        return False

    if line["font_size"] < 8:
        return False

    # --------------------------------------------------------
    # Front-matter labels followed by their actual text
    #
    # Example:
    # Abstract—Thanks to the rapid economic development...
    # Keywords—the design for hotels...
    # --------------------------------------------------------

    if re.match(
        r"^(abstract|keywords)\s*[-—–]",
        text,
        re.IGNORECASE
    ):
        return False

    # --------------------------------------------------------
    # Arabic / Roman numbered structural headings
    # --------------------------------------------------------

    if _looks_like_numbered_heading(text):
        return True

    # --------------------------------------------------------
    # Alphabetic structural headings
    #
    # A. Color Coordination
    # B. Materials' Match
    # C. Style Design
    # --------------------------------------------------------

    alpha_match = re.match(
        r"^[A-Z]\.\s+(.+)$",
        text
    )

    if alpha_match:
        title = alpha_match.group(1).strip()
        words = title.split()

        if 0 < len(words) <= 12:
            if not title.endswith(
                (".", ",", ";", ":")
            ):
                return True

    # --------------------------------------------------------
    # Footer / header-like text
    # --------------------------------------------------------

    lowered = text.lower()

    if (
        "www." in lowered
        or "http://" in lowered
        or "https://" in lowered
        or "doi:" in lowered
        or "issn:" in lowered
        or "â©" in text
        or "page " in lowered
    ):
        return False

    # --------------------------------------------------------
    # Sentence-like text
    # --------------------------------------------------------

    if text.endswith((".", "?", "!")):
        return False

    words = text.split()

    if len(words) > 12:
        return False

    # --------------------------------------------------------
    # Strong visual hierarchy
    # --------------------------------------------------------

    larger_than_body = (
        body_font_size > 0
        and line["font_size"] >= body_font_size * 1.18
    )

    if larger_than_body:
        return True

    # --------------------------------------------------------
    # Bold text
    #
    # Keep this conservative. Bold alone should not turn
    # paragraph fragments into headings.
    # --------------------------------------------------------

    if line["bold"] and len(words) <= 4:
        return True

    return False


def _is_list_item(text: str) -> bool:
    stripped = text.strip()

    if not stripped:
        return False

    # Common bullet characters
    if stripped[0] in "•●▪◦‣–-*" :
        return True

    # Numbered lists: 1. Something
    parts = stripped.split(".", 1)

    if (
        len(parts) == 2
        and parts[0].isdigit()
        and parts[1].strip()
    ):
        return True

    return False


# ============================================================
# PDF → CANONICAL DOCUMENT
# ============================================================

def parse_pdf_to_canonical(
    file_path: str
) -> CanonicalDocument:
    """
    Parse a PDF into the canonical document representation.

    The canonical representation preserves:

        - pages
        - headings
        - paragraphs
        - lists
        - images
        - page locations
        - image/page relationships

    Heading detection is intentionally heuristic because PDFs
    do not contain a reliable semantic heading structure like
    HTML or DOCX.
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"PDF file not found: {file_path}"
        )

    if not file_path.lower().endswith(".pdf"):
        raise ValueError(
            "The provided file is not a PDF."
        )

    try:
        document = fitz.open(file_path)

    except Exception as e:
        raise ValueError(
            f"Unable to open PDF: {e}"
        )

    blocks: list[DocumentBlock] = []
    images: list[DocumentImage] = []

    image_output_dir = (
        Path("data/images")
        / Path(file_path).stem
    )

    image_output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # ========================================================
    # PROCESS EACH PAGE
    # ========================================================

    for page_number, pdf_page in enumerate(
        document,
        start=1
    ):

        # ----------------------------------------------------
        # TEXT
        # ----------------------------------------------------

        lines = _extract_text_lines(
            pdf_page
        )

        if lines:

            font_sizes = [
                line["font_size"]
                for line in lines
                if line["font_size"] > 0
            ]

            if font_sizes:
                body_font_size = statistics.median(
                    font_sizes
                )
            else:
                body_font_size = 0

            for line_index, line in enumerate(
                lines
            ):

                text = line["text"].strip()

                if not text:
                    continue

                # ------------------------------------------------
                # Determine semantic block type.
                # ------------------------------------------------

                if _looks_like_heading(
                    line,
                    body_font_size
                ):

                    block_type = "heading"

                    # Large/bold headings are generally
                    # top-level. Smaller headings can later
                    # be refined by PageIndex.
                    level = 1

                elif _is_list_item(
                    text
                ):

                    block_type = "list"
                    level = None

                else:

                    block_type = "paragraph"
                    level = None

                blocks.append(
                    DocumentBlock(
                        type=block_type,
                        text=text,
                        level=level,
                        location={
                            "page": page_number,
                            "line": line_index + 1,
                            "bbox": line["bbox"],
                        },
                        metadata={
                            "source_type": "pdf",
                            "font_size": line["font_size"],
                            "bold": line["bold"],
                        },
                    )
                )

        # ====================================================
        # IMAGES
        # ====================================================

        page_images = pdf_page.get_images(
            full=True
        )

        for image_position, image_info in enumerate(
            page_images,
            start=1
        ):

            xref = image_info[0]

            try:

                image_data = document.extract_image(
                    xref
                )

                extension = image_data.get(
                    "ext",
                    "png"
                )

                image_id = (
                    f"pdf-page-{page_number:04d}"
                    f"-image-{image_position:02d}"
                )

                filename = (
                    f"{image_id}.{extension}"
                )

                output_file = (
                    image_output_dir
                    / filename
                )

                with open(
                    output_file,
                    "wb"
                ) as file:

                    file.write(
                        image_data["image"]
                    )

                width = image_data.get(
                    "width"
                )

                height = image_data.get(
                    "height"
                )

                image = DocumentImage(
                    image_id=image_id,
                    path=str(output_file),
                    filename=filename,
                    source_page=page_number,
                    width=width,
                    height=height,
                    metadata={
                        "xref": xref,
                        "source_type": "pdf",
                        "image_position": image_position,
                    },
                )

                images.append(
                    image
                )

                # ---------------------------------------------
                # Create an image block connected to the page.
                # ---------------------------------------------

                blocks.append(
                    DocumentBlock(
                        type="image",
                        text="",
                        location={
                            "page": page_number,
                            "image_position": image_position,
                        },
                        metadata={
                            "source_type": "pdf",
                            "image_id": image_id,
                            "xref": xref,
                        },
                        image_ids=[
                            image_id
                        ],
                    )
                )

            except Exception as e:

                print(
                    f"Warning: Could not extract image "
                    f"from PDF page {page_number}: {e}"
                )

    page_count = document.page_count

    document.close()

    # ========================================================
    # FINAL CANONICAL DOCUMENT
    # ========================================================


    heading_count = sum(
        1
        for block in blocks
        if block.type == "heading"
    )

    paragraph_count = sum(
        1
        for block in blocks
        if block.type == "paragraph"
    )

    list_count = sum(
        1
        for block in blocks
        if block.type == "list"
    )

    image_block_count = sum(
        1
        for block in blocks
        if block.type == "image"
    )

    return CanonicalDocument(
        title=Path(file_path).stem,
        source_format="pdf",
        blocks=blocks,
        images=images,
        metadata={
            "original_filename": Path(
                file_path
            ).name,

            # IMPORTANT:
            # This is the actual PDF page count.
            "page_count": page_count,

            "image_count": len(
                images
            ),

            "heading_count": heading_count,

            "paragraph_count": paragraph_count,

            "list_count": list_count,

            "image_block_count": image_block_count,
        },
    )
import json
import re 
from pathlib import Path
from turtle import heading

from pydantic import BaseModel, Field

from app.models.page import Page
from app.parser.canonical_document import CanonicalDocument
from app.config.settings import USE_GEMINI
from app.llm.gemini_client import generate_page_index_structure
from app.llm.ollama_client import generate_text as generate_ollama_text
from app.parser.canonical_document import CanonicalDocument, DocumentBlock


# ============================================================
# PAGE INDEX MODEL
# ============================================================

class PageIndexNode(BaseModel):
    node_id: str
    title: str
    number: str = ""
    start_index: int
    end_index: int
    summary: str = ""
    nodes: list["PageIndexNode"] = Field(default_factory=list)


# ============================================================
# BASIC PAGE INDEX
# ============================================================

def create_basic_page_index(
    pages: list[Page],
    document_title: str
) -> PageIndexNode:

    root = PageIndexNode(
        node_id="0001",
        title=document_title,
        start_index=1,
        end_index=len(pages),
        summary=f"Document containing {len(pages)} pages."
    )

    for page in pages:
        page_node = PageIndexNode(
            node_id=f"page-{page.page_number:04d}",
            title=f"Page {page.page_number}",
            start_index=page.page_number,
            end_index=page.page_number,
            summary=page.text[:200].replace("\n", " ")
        )

        root.nodes.append(page_node)

    return root

def create_canonical_page_index(
    document: CanonicalDocument,
    pages: list[Page] | None = None
) -> PageIndexNode:
    """
    Build a PageIndex directly from a CanonicalDocument.

    The canonical document provides the reliable heading hierarchy.

    If pages are provided, heading locations are mapped to the actual
    page numbers used by the existing PageIndex/RAG pipeline.

    This is important for non-PDF documents because their canonical
    blocks are NOT pages. They may be converted into artificial pages
    by markdown_chunker.py.
    """

    blocks = document.blocks

    if not blocks:
        raise ValueError(
            "Canonical document contains no blocks."
        )

        # ---------------------------------------------------------
    # XLSX
    #
    # Excel workbooks do not have document-style headings.
    # The XLSX parser creates artificial Pages containing
    # column-aware records, so each Page becomes a logical
    # PageIndex node.
    # ---------------------------------------------------------

    if document.source_format.lower() == "xlsx":

        if not pages:
            raise ValueError(
                "XLSX PageIndex requires generated pages."
            )

        root = PageIndexNode(
            node_id="0001",
            title=document.title or "Workbook",
            start_index=1,
            end_index=len(pages),
            summary="Root node representing the complete workbook."
        )

        record_start = 1

        for page in pages:

            # Count records contained in this artificial page.
            record_count = page.text.count(
                "Hotel Record"
            )

            # Fallback in case the record marker changes.
            if record_count <= 0:
                record_count = 1

            record_end = (
                record_start
                + record_count
                - 1
            )

            node = PageIndexNode(
                node_id=(
                    f"0001.{page.page_number}"
                ),
                title=(
                    f"Records "
                    f"{record_start}–{record_end}"
                ),
                start_index=page.page_number,
                end_index=page.page_number,
                summary=(
                    f"Spreadsheet records "
                    f"{record_start}–{record_end}."
                ),
            )

            root.nodes.append(node)

            record_start = record_end + 1

        print(
            f"\n[PageIndex] Built XLSX PageIndex "
            f"from {len(pages)} data pages."
        )

        print(
            f"[PageIndex] Spreadsheet records: "
            f"{record_start - 1}"
        )

        print(
            f"[PageIndex] Data sections: "
            f"{len(root.nodes)}"
        )

        return root

    # ---------------------------------------------------------
    # Find explicit headings.
    # ---------------------------------------------------------

    headings = []

    for block in blocks:

        if block.type != "heading":
            continue

        if not block.text or block.level is None:
            continue

        level = max(
            1,
            min(int(block.level), 3)
        )

        headings.append(
            {
                "title": block.text.strip(),
                "level": level,
            }
        )

    if not headings:
        raise ValueError(
            "Canonical document contains no explicit headings."
        )

    # ---------------------------------------------------------
    # Determine page location for each heading.
    #
    # IMPORTANT:
    # Canonical block positions are NOT page numbers.
    #
    # We therefore search the actual Page objects for the heading
    # text. This works for both:
    #
    # - real PDF pages
    # - artificial pages created from Markdown for DOCX/ODT/etc.
    # ---------------------------------------------------------

    if pages:

        for heading in headings:

            title = heading["title"].strip().lower()

            matching_pages = []

            for page in pages:

                page_text = page.text.lower()

                if title in page_text:
                    matching_pages.append(
                        page.page_number
                    )

            if matching_pages:
                heading["page"] = min(
                    matching_pages
                )
            else:
                heading["page"] = None

    else:

        # No page information was supplied.
        # Keep locations unavailable rather than pretending
        # canonical block numbers are page numbers.
        for heading in headings:
            heading["page"] = None

    # ---------------------------------------------------------
    # If some headings could not be located on a page, infer
    # their location from neighbouring headings where possible.
    # ---------------------------------------------------------

    known_positions = [
        index
        for index, heading in enumerate(headings)
        if heading["page"] is not None
    ]

    if known_positions:

        for index, heading in enumerate(headings):

            if heading["page"] is not None:
                continue

            previous_pages = [
                headings[i]["page"]
                for i in known_positions
                if i < index
                and headings[i]["page"] is not None
            ]

            next_pages = [
                headings[i]["page"]
                for i in known_positions
                if i > index
                and headings[i]["page"] is not None
            ]

            if previous_pages:
                heading["page"] = previous_pages[-1]

            elif next_pages:
                heading["page"] = next_pages[0]

    # ---------------------------------------------------------
    # Determine total document pages.
    # ---------------------------------------------------------

    if pages:
        total_pages = len(pages)
    else:
        total_pages = 1

    # ---------------------------------------------------------
    # Build root.
    # ---------------------------------------------------------

    root = PageIndexNode(
        node_id="0001",
        title=document.title or "Document",
        start_index=1,
        end_index=total_pages,
        summary="Root node representing the complete document."
    )

    # ---------------------------------------------------------
    # Build hierarchy.
    # ---------------------------------------------------------

    stack = []
    counter = 0

    for heading_position, heading in enumerate(headings):

        title = heading["title"]
        level = heading["level"]

        start_page = heading["page"]

        # If we could not map the heading to a page, use the
        # closest known page rather than using a block number.
        if start_page is None:
            start_page = 1

        # -----------------------------------------------------
        # Determine end page.
        #
        # A section ends immediately before the next heading
        # at the same or higher level.
        # -----------------------------------------------------

        end_page = total_pages

        for next_heading in headings[
            heading_position + 1:
        ]:

            next_level = next_heading["level"]
            next_page = next_heading["page"]

            if next_level <= level:

                if next_page is not None:

                    end_page = max(
                        start_page,
                        next_page - 1
                    )

                break

        counter += 1

        node = PageIndexNode(
            node_id=f"0001.{counter}",
            title=title,
            start_index=start_page,
            end_index=end_page,
            summary=""
        )

        # -----------------------------------------------------
        # Find parent using heading hierarchy.
        # -----------------------------------------------------

        while stack and stack[-1]["level"] >= level:
            stack.pop()

        if not stack:

            root.nodes.append(node)

        else:

            parent = stack[-1]["node"]

            parent.nodes.append(node)

        stack.append(
            {
                "level": level,
                "node": node
            }
        )

    print(
        f"\n[PageIndex] Built canonical PageIndex "
        f"from {len(headings)} explicit headings."
    )

    print(
        f"[PageIndex] Top-level sections: "
        f"{len(root.nodes)}"
    )

    return root

# ============================================================
# SAVE PAGE INDEX
# ============================================================

def save_page_index(
    page_index: PageIndexNode,
    output_path: str
) -> None:

    output_file = Path(output_path)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            page_index.model_dump(),
            file,
            indent=2,
            ensure_ascii=False
        )

def load_page_index(
    input_path: str
) -> PageIndexNode:

    input_file = Path(input_path)

    with open(
        input_file,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    return PageIndexNode.model_validate(data)

def retrieve_relevant_pages(
    question: str,
    pages: list,
    page_index: PageIndexNode,
    top_k: int = 2
) -> list:
    """
    Retrieve the most relevant pages using simple keyword matching.
    """

    import re

    question_words = set(
        word.lower()
        for word in re.findall(r"\b[a-zA-Z0-9]+\b", question)
        if len(word) > 2
    )

    scored_pages = []

    for page in pages:
        page_words = set(
            word.lower()
            for word in re.findall(r"\b[a-zA-Z0-9]+\b", page.text)
        )

        score = len(question_words & page_words)

        if score > 0:
            scored_pages.append((score, page))

    scored_pages.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return [
        page
        for score, page in scored_pages[:top_k]
    ]

# ============================================================
# GEMINI PROMPT
# ============================================================

def _build_document_prompt(
    pages: list[Page]
) -> str:

    page_contents = []

    for page in pages:

        page_contents.append(
            f"""
PAGE {page.page_number}
--------------------
{page.text}
"""
        )

    document_text = "\n".join(page_contents)

    return f"""
You are a document structure analyzer.

Analyze the following document and identify its hierarchical structure.

IMPORTANT:
- Use ONLY information present in the document.
- Do not invent section names.
- Identify actual sections and subsections.
- Each section must have a start page and end page.
- Page numbers are the PDF page numbers shown below.
- Page numbers are 1-based.
- Keep the hierarchy meaningful.
- Do not create a node for every paragraph.
- Return ONLY valid JSON.
- Do not include markdown or explanations outside the JSON.

Return exactly this structure:

{{
  "title": "Document title",
  "sections": [
    {{
      "title": "Section title",
      "start_index": 1,
      "end_index": 3,
      "summary": "Short summary of this section.",
      "sections": [
        {{
          "title": "Subsection title",
          "start_index": 1,
          "end_index": 2,
          "summary": "Short summary of this subsection.",
          "sections": []
        }}
      ]
    }}
  ]
}}

DOCUMENT:

{document_text}
"""


# ============================================================
# GEMINI RESPONSE → PAGE INDEX
# ============================================================

def _build_page_index_from_response(
    response: str,
    pages: list[Page]
) -> PageIndexNode:

    response = response.strip()

    if response.startswith("```"):
        response = response.replace("```json", "", 1)
        response = response.replace("```", "", 1)
        response = response.strip()

    data = json.loads(response)

    if "sections" not in data:
        raise ValueError(
            "PageIndex response is missing the 'sections' field."
        )

    root = PageIndexNode(
        node_id="0001",
        title=(
            data.get("title")
            or data.get("document_title")
            or "Document"
        ),
        start_index=1,
        end_index=len(pages),
        summary="Root node representing the complete document."
    )

    def build_nodes(
        sections: list,
        parent_id: str
    ) -> list[PageIndexNode]:

        nodes = []

        for index, section in enumerate(
            sections,
            start=1
        ):

            node_id = f"{parent_id}.{index}"

            node = PageIndexNode(
                node_id=node_id,
                title=section["title"],
                start_index=section["start_index"],
                end_index=section["end_index"],
                summary=section.get("summary", "")
            )

            node.nodes = build_nodes(
                section.get("sections", []),
                node_id
            )

            nodes.append(node)

        return nodes

    root.nodes = build_nodes(
        data.get("sections", []),
        "0001"
    )

    return root


# ============================================================
# OLLAMA HEADING EXTRACTION
# ============================================================

OLLAMA_CHUNK_SIZE = 1


def _build_ollama_prompt(
    pages: list[Page]
) -> str:

    page_contents = []

    for page in pages:
        page_contents.append(
            f"""
=== PDF PAGE {page.page_number} ===

{page.text}
"""
        )

    document_text = "\n".join(page_contents)

    return f"""
Read the PDF page below.

Your ONLY task is to identify actual section headings and
subsection headings that visibly appear on this page.

Return ONLY a JSON array.

Each item MUST contain exactly these fields:

- title
- level

Rules:

1. Use ONLY headings that actually appear in the document.
2. Do NOT invent headings.
3. level 1 = main section.
4. level 2 = subsection.
5. level 3 = sub-subsection.
6. Do NOT return summaries.
7. Do NOT return descriptions.
8. Do NOT return analysis.
9. Do NOT return explanations.
10. Do NOT return page numbers.
11. Do NOT return character positions.
12. Do NOT return character offsets.
13. Do NOT include "PAGE X" in titles.
14. Do NOT create a heading for every paragraph.
15. Return an empty array if no actual section headings are present.
16. Preserve the heading wording from the document.
17. Do not infer headings from surrounding context.
18. Only return headings that are explicitly visible on this page.
19. If there are multiple headings, return all of them.
20. If there is only one heading, return one item inside the JSON array.
21. The response MUST be valid JSON.
22. Do not write anything before or after the JSON array.

Example output:

[
  {{
    "title": "1. Introduction",
    "level": 1
  }},
  {{
    "title": "2.1 Previous Research",
    "level": 2
  }}
]

DOCUMENT:

{document_text}
"""


def _extract_ollama_headings(
    pages: list[Page]
) -> list[dict]:

    prompt = _build_ollama_prompt(pages)

    print(
        f"\n[PageIndex] Sending pages "
        f"{pages[0].page_number}-{pages[-1].page_number} "
        f"to Ollama/Qwen..."
    )

    print(
        f"[PageIndex] Prompt characters: {len(prompt)}"
    )

    response = generate_ollama_text(
        prompt,
        json_mode=True
    )

    response = response.strip()

    print(
        "\n========== QWEN HEADING RESPONSE =========="
    )
    print(response)
    print(
        "========== END QWEN RESPONSE ==========\n"
    )

    if response.startswith("```"):
        response = response.replace(
            "```json",
            "",
            1
        )
        response = response.replace(
            "```",
            "",
            1
        )
        response = response.strip()

    try:
        data = json.loads(response)

    except json.JSONDecodeError as e:

        print(
            "========== QWEN JSON ERROR =========="
        )
        print(e)
        print(
            "======================================"
        )

        raise

    # Qwen sometimes returns a single heading as an object
    # instead of wrapping it inside an array.
    if isinstance(data, dict):
        if "title" in data:
            data = [data]
        else:
            raise ValueError(
                "Qwen returned a JSON object without a heading."
        )

    if not isinstance(data, list):
        raise ValueError(
            "Qwen heading response must be a JSON array or heading object."
    )
    headings = []

    for item in data:

        if not isinstance(item, dict):
            continue

        title = item.get("title")
        level = item.get("level")

        if not title:
            continue

        try:
            level = int(level)
        except (TypeError, ValueError):
            level = 1

        if level < 1:
            level = 1

        if level > 3:
            level = 3

        headings.append(
            {
                "title": str(title).strip(),
                "level": level
            }
        )

    return headings


# ============================================================
# BUILD OLLAMA PAGE INDEX
# ============================================================

def _normalize_heading_hierarchy(headings: list[dict]) -> list[dict]:
    """
    Normalize detected headings into a consistent 3-level hierarchy.

    Generic rules:

    L1:
        Unnumbered headings
        Roman-numbered headings such as I., II., III.

    L2:
        Single-number headings such as 1., 2., 3.
        Alphabetic headings such as A., B., C. when directly
        under an L1 section

    L3:
        Alphabetic headings when already inside an L2 section
        Explicit 3-level numbering such as 2.1.1

    Canonical numbering is generated independently of the
    numbering used in the source document.
    """

    normalized = []

    # Canonical counters:
    # [L1, L2, L3]
    counters = [0, 0, 0]

    # Track the current structural context.
    current_level1 = False
    current_level2 = False

    for heading in headings:

        original_title = heading["title"].strip()
        title = original_title

        # ----------------------------------------------------
        # Detect numeric numbering
        #
        # 1. Introduction
        # 2. Destination
        # 2.1 Something
        # 2.1.1 Something
        # ----------------------------------------------------

        numeric_match = re.match(
            r"^\s*(\d+(?:\.\d+)*)\.?\s+(.+)$",
            title
        )

        # ----------------------------------------------------
        # Detect alphabetic numbering
        #
        # A. Something
        # B. Something
        # ----------------------------------------------------

        alpha_match = re.match(
            r"^\s*([A-Z])\.\s+(.+)$",
            title
        )

        # ====================================================
        # 1. Alphabetic heading
        # ====================================================

        if alpha_match:

            title = alpha_match.group(2).strip()

            if current_level2:
                # A/B/C under an L2 section
                level = 3
            else:
                # A/B/C directly under an L1 section
                level = 2

        # ====================================================
        # 2. Numeric heading
        # ====================================================

        elif numeric_match:

            numbering = numeric_match.group(1)
            title = numeric_match.group(2).strip()

            depth = len(numbering.split("."))

            if depth >= 3:
                level = 3

            elif depth == 2:
                level = 2

            else:
                # 1. Something
                # 2. Something
                #
                # These are subsections of the current L1.
                if current_level1:
                    level = 2
                else:
                    level = 1

        # ====================================================
        # 3. Unnumbered heading
        # ====================================================

        else:

            # Unnumbered structural headings are top-level.
            level = 1

        # ====================================================
        # First heading must always be L1
        # ====================================================

        if not normalized:
            level = 1

        # Never allow levels deeper than L3.
        level = min(level, 3)

        # ====================================================
        # Update canonical counters
        # ====================================================

        if level == 1:

            counters[0] += 1
            counters[1] = 0
            counters[2] = 0

            current_level1 = True
            current_level2 = False

        elif level == 2:

            counters[1] += 1
            counters[2] = 0

            current_level1 = True
            current_level2 = True

        else:

            counters[2] += 1

            current_level1 = True
            current_level2 = True

        # ====================================================
        # Generate canonical number
        # ====================================================

        number = ".".join(
            str(counters[i])
            for i in range(level)
        )

        normalized.append(
            {
                **heading,
                "title": title,
                "level": level,
                "number": number,
            }
        )

    return normalized

def create_ollama_page_index(
    pages: list[Page]
) -> PageIndexNode:

    """
    Build PageIndex using local Ollama/Qwen.

    Qwen is responsible ONLY for identifying headings.

    Python is responsible for:
    - assigning PDF page numbers
    - determining section ranges
    - building the hierarchy
    - creating PageIndexNode objects
    """

    print(
        "\n[PageIndex] Using Ollama/Qwen pipeline..."
    )

    all_headings = []

    # --------------------------------------------------------
    # Process the PDF in 2-page chunks.
    # --------------------------------------------------------

    for start in range(
        0,
        len(pages),
        OLLAMA_CHUNK_SIZE
    ):

        chunk = pages[
            start:start + OLLAMA_CHUNK_SIZE
        ]

        headings = _extract_ollama_headings(
            chunk
        )

        print(
            f"[PageIndex] Found {len(headings)} headings "
            f"in pages "
            f"{chunk[0].page_number}-"
            f"{chunk[-1].page_number}"
        )

        for heading in headings:

            all_headings.append(
                {
                    "title": heading["title"],
                    "level": heading["level"],
                    "page": chunk[0].page_number
                }
            )

    # --------------------------------------------------------
    # Remove duplicate headings while preserving order.
    # --------------------------------------------------------

    unique_headings = []

    seen = set()

    for heading in all_headings:

        key = (
            heading["title"].lower(),
            heading["level"],
            heading["page"]
        )

        if key in seen:
            continue

        seen.add(key)
        unique_headings.append(heading)

    # --------------------------------------------------------
    # If Qwen found nothing, fail clearly.
    # --------------------------------------------------------

    if not unique_headings:

        print(
            "\n[PageIndex] Qwen did not identify any headings."
        )

        print(
            "[PageIndex] Falling back to basic page-level index."
        )

        root = PageIndexNode(
            node_id="0001",
            title="Document",
            start_index=1,
            end_index=len(pages),
            summary=(
                "No explicit section headings were identified. "
                "Document indexed at page level."
            )
        )

        for page in pages:

            page_node = PageIndexNode(
                node_id=f"0001.{page.page_number}",
                title=f"Page {page.page_number}",
                start_index=page.page_number,
                end_index=page.page_number,
                summary=page.text[:300].replace("\n", " ")
            )

            root.nodes.append(page_node)

        print(
            f"[PageIndex] Created {len(root.nodes)} page-level nodes."
        )

        return root

    # --------------------------------------------------------
    # Normalize heading hierarchy and numbering.
    # --------------------------------------------------------

    unique_headings = _normalize_heading_hierarchy(
        unique_headings
    )

    print("\n[PageIndex] Normalized hierarchy:")

    for heading in unique_headings:
        print(
            f"  {heading['number']} "
            f"[L{heading['level']}] "
            f"{heading['title']}"
        )

    # --------------------------------------------------------
    # Build root.
    # --------------------------------------------------------

    root = PageIndexNode(
        node_id="0001",
        title="Document",
        start_index=1,
        end_index=len(pages),
        summary="Root node representing the complete document."
    )

    # --------------------------------------------------------
    # Build hierarchy.
    # --------------------------------------------------------

    stack = []

    counter = 0

    for index, heading in enumerate(
        unique_headings
    ):

        title = heading["title"]

        level = heading["level"]

        start_page = heading["page"]

        # ----------------------------------------------------
        # Determine end page.
        #
        # A section ends immediately before the next heading
        # at the same or higher level.
        # ----------------------------------------------------

        end_page = len(pages)

        for next_heading in unique_headings[index + 1:]:

            next_level = next_heading["level"]

            if next_level <= level:

                end_page = max(
                    start_page,
                    next_heading["page"] - 1
                )

                break

        counter += 1

        node = PageIndexNode(
            node_id=f"0001.{counter}",
            title=title,
            number=heading["number"],
            start_index=start_page,
            end_index=end_page,
            summary=""
        )

        # ----------------------------------------------------
        # Find the parent.
        # ----------------------------------------------------

        while stack and stack[-1]["level"] >= level:
            stack.pop()

        if not stack:

            root.nodes.append(node)

        else:

            parent = stack[-1]["node"]

            parent.nodes.append(node)

        stack.append(
            {
                "level": level,
                "node": node
            }
        )

    print(
        f"\n[PageIndex] Total headings found: "
        f"{len(unique_headings)}"
    )

    print(
        f"[PageIndex] Top-level sections: "
        f"{len(root.nodes)}"
    )

    return root


# ============================================================
# CONFIGURED PAGEINDEX PIPELINE
# ============================================================

def create_llm_page_index(
    pages: list[Page]
) -> PageIndexNode:

    """
    Create PageIndex using the configured pipeline.

    USE_GEMINI = True
        -> Gemini

    USE_GEMINI = False
        -> Ollama / local Qwen
    """

    if USE_GEMINI:

        print(
            "\n[PageIndex] Using Gemini pipeline..."
        )

        prompt = _build_document_prompt(
            pages
        )

        response = generate_page_index_structure(
            prompt
        )

        return _build_page_index_from_response(
            response,
            pages
        )

    else:

        print(
            "\n[PageIndex] Using Ollama/Qwen pipeline..."
        )

        return create_ollama_page_index(
            pages
        )
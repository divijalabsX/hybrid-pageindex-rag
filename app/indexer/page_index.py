from pydantic import BaseModel, Field
from app.models.page import Page


class PageIndexNode(BaseModel):
    node_id: str
    title: str
    start_index: int
    end_index: int
    summary: str = ""
    nodes: list["PageIndexNode"] = Field(default_factory=list)


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

import json
from pathlib import Path

from pydantic import BaseModel, Field
from app.models.page import Page

def save_page_index(page_index: PageIndexNode, output_path: str) -> None:
    output_file = Path(output_path)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(
            page_index.model_dump(),
            file,
            indent=2,
            ensure_ascii=False
        )
    

from app.llm.gemini_client import generate_page_index_structure


def create_llm_page_index(pages: list[Page]) -> PageIndexNode:
    """
    Use Gemini to identify the hierarchical structure of the document.
    """

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

    prompt = f"""
You are a document structure analyzer.

Analyze the following research paper and identify its hierarchical structure.

IMPORTANT:
- Use ONLY information present in the document.
- Do not invent section names.
- Identify the actual sections and subsections.
- Each section must have a start page and end page.
- Page numbers are 1-based.
- Keep the hierarchy meaningful. Do not create a node for every paragraph.
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

    response = generate_page_index_structure(prompt)

    data = json.loads(response)

    root = PageIndexNode(
        node_id="0001",
        title=data["title"],
        start_index=1,
        end_index=len(pages),
        summary="Root node representing the complete document."
    )

    def build_nodes(
        sections: list,
        parent_id: str
    ) -> list[PageIndexNode]:

        nodes = []

        for index, section in enumerate(sections, start=1):

            node_id = f"{parent_id}.{index}"

            node = PageIndexNode(
                node_id=node_id,
                title=section["title"],
                start_index=section["start_index"],
                end_index=section["end_index"],
                summary=section.get("summary", "")
            )

            child_sections = section.get("sections", [])

            node.nodes = build_nodes(
                child_sections,
                node_id
            )

            nodes.append(node)

        return nodes

    root.nodes = build_nodes(
        data.get("sections", []),
        "0001"
    )

    return root
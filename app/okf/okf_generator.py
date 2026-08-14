import json
from pathlib import Path

from app.okf.okf_model import OKFKnowledgeItem


def load_page_index(file_path: str) -> dict:
    """Load the PageIndex JSON file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def slugify(title: str) -> str:
    """Convert a title into a safe filename."""
    return (
        title.lower()
        .replace(" ", "-")
        .replace("/", "-")
        .replace(":", "")
    )


def node_to_okf(node: dict, source: str) -> OKFKnowledgeItem:
    """Convert a PageIndex node into an OKF knowledge item."""

    item = OKFKnowledgeItem(
        title=node["title"],
        type="Section",
        description=node.get("summary", ""),
        source=source,
        start_page=node.get("start_index", 0),
        end_page=node.get("end_index", 0),
        content=node.get("summary", "")
    )

    for child in node.get("nodes", []):
        item.children.append(
            node_to_okf(child, source)
        )

    return item

def markdown_frontmatter(item: OKFKnowledgeItem) -> str:
    """Create YAML frontmatter for an OKF knowledge item."""

    title = item.title.replace('"', '\\"')
    description = item.description.replace('"', '\\"')
    source = item.source.replace('"', '\\"')

    return f"""---
title: "{title}"
type: "{item.type}"
description: "{description}"
source: "{source}"
start_page: {item.start_page}
end_page: {item.end_page}
---

"""


def write_okf_item(
    item: OKFKnowledgeItem,
    output_dir: str,
    is_root: bool = False
) -> str:
    """Write one OKF knowledge item as a Markdown file."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filename = "index.md" if is_root else f"{slugify(item.title)}.md"

    file_path = output_path / filename

    content = markdown_frontmatter(item)

    content += f"# {item.title}\n\n"

    if item.content:
        content += f"{item.content}\n\n"

    if item.children:
        content += "## Subsections\n\n"

        for child in item.children:
            child_filename = f"{slugify(child.title)}.md"
            content += f"- [{child.title}]({child_filename})\n"

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

    return str(file_path)

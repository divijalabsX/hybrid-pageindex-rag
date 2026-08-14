from pathlib import Path

from app.okf.okf_generator import load_page_index, node_to_okf


def test_okf_generator():
    pageindex_path = Path("data/pageindex/pageindex.json")

    assert pageindex_path.exists(), "PageIndex JSON file does not exist"

    page_index = load_page_index(str(pageindex_path))

    assert isinstance(page_index, dict)

    okf_root = node_to_okf(
        page_index,
        source=page_index.get("title", "Unknown Document")
    )

    assert okf_root is not None
    assert okf_root.title
    assert okf_root.type == "Section"
from pathlib import Path

import anydoc


def parse_document(file_path: str) -> str:
    """
    Convert a supported document into GitHub-Flavored Markdown
    using the locally built anydoc integration.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")

    with open(path, "rb") as file:
        data = file.read()

    # CSV does not have enough information in its bytes
    # for reliable format detection, so provide the format explicitly.
    if path.suffix.lower() == ".csv":
        return anydoc.to_markdown_bytes(data, "csv")

    return anydoc.to_markdown_bytes(data)
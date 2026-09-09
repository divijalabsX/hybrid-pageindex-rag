from dataclasses import dataclass, field
from typing import Any


@dataclass
class DocumentImage:
    """
    Represents an image or other visual asset extracted from a document.
    """

    image_id: str
    path: str = ""
    filename: str = ""
    source_page: int | None = None
    source_block: int | None = None

    width: int | None = None
    height: int | None = None

    # Text extracted from the image, if available.
    extracted_text: str = ""

    # Human-readable description generated later by a vision model.
    description: str = ""

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentBlock:
    type: str
    text: str = ""
    level: int | None = None

    location: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    # References to visual assets associated with this block.
    image_ids: list[str] = field(default_factory=list)


@dataclass
class CanonicalDocument:
    title: str
    source_format: str

    blocks: list[DocumentBlock] = field(default_factory=list)

    # All extracted images/visual assets.
    images: list[DocumentImage] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)
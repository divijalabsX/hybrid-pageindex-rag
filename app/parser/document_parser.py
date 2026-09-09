from pathlib import Path

import anydoc

from app.parser.canonical_document import (
    CanonicalDocument,
    DocumentBlock,
    DocumentImage,
)

from app.parser.media_extractor import (
    extract_zip_images,
)

from app.parser.pptx_parser import (
    _get_shape_image_bytes,
)


def parse_document(
    file_path: str
) -> str:
    """
    Convert a supported document into GitHub-Flavored Markdown
    using the locally built AnyDoc integration.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Document not found: {file_path}"
        )

    with open(
        path,
        "rb"
    ) as file:

        data = file.read()

    # CSV requires explicit format detection.
    if path.suffix.lower() == ".csv":

        return anydoc.to_markdown_bytes(
            data,
            "csv"
        )

    return anydoc.to_markdown_bytes(
        data
    )


def parse_document_to_canonical(
    file_path: str
) -> CanonicalDocument:
    """
    Convert a supported document into the canonical representation.

    Textual structure comes from AnyDoc.

    For PPTX files:
        - text is represented as DocumentBlocks
        - every picture is extracted
        - every picture is associated with its slide
        - image IDs are stored on the corresponding block

    Other ZIP-based formats continue using the existing
    media extraction path for now.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Document not found: {file_path}"
        )

    with open(
        path,
        "rb"
    ) as file:

        data = file.read()

    # ---------------------------------------------------------
    # PDF
    # ---------------------------------------------------------

    if path.suffix.lower() == ".pdf":
        from app.parser.pdf_parser import parse_pdf_to_canonical

        return parse_pdf_to_canonical(
            file_path
        )
    
    document = anydoc.to_document(
        data
    )

    blocks: list[DocumentBlock] = []

    for block_index, block in enumerate(
        document.blocks
    ):

        text_parts = []

        for inline in block.content or []:

            if (
                inline.kind == "text"
                and inline.text
            ):

                text_parts.append(
                    inline.text
                )

        text = "".join(
            text_parts
        ).strip()

        block_type = (
            block.kind
            or "unknown"
        )

        if block_type == "heading":

            canonical_type = "heading"

        elif block_type == "paragraph":

            canonical_type = "paragraph"

        elif block_type == "table":

            canonical_type = "table"

        elif block_type == "list":

            canonical_type = "list"

        else:

            canonical_type = block_type

        metadata = {
            "source": "anydoc",
            "source_block_index": block_index,
        }

        blocks.append(
            DocumentBlock(
                type=canonical_type,
                text=text,
                level=block.level,
                location={
                    "block_index": block_index
                },
                metadata=metadata,
            )
        )

    # ---------------------------------------------------------
    # XLSX
    # ---------------------------------------------------------

    if path.suffix.lower() == ".xlsx":
        from app.parser.xlsx_parser import parse_xlsx_to_canonical

        return parse_xlsx_to_canonical(
            file_path
        )

    # =========================================================
    # IMAGE EXTRACTION
    # =========================================================

    images: list[DocumentImage] = []

    # ---------------------------------------------------------
    # PPTX
    # ---------------------------------------------------------

    if path.suffix.lower() == ".pptx":

        from pptx import Presentation
        from pptx.enum.shapes import MSO_SHAPE_TYPE

        presentation = Presentation(
            str(path)
        )

        image_output_dir = (
            Path("data/images")
            / path.stem
        )

        image_output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        image_counter = 0

        # -----------------------------------------------------
        # AnyDoc blocks don't necessarily expose PPTX slide
        # information in a way we can reliably use here.
        #
        # Therefore we associate images with blocks using
        # slide numbers and preserve that relationship in
        # metadata.
        # -----------------------------------------------------

        for slide_number, slide in enumerate(
            presentation.slides,
            start=1
        ):

            slide_image_ids = []

            for shape in slide.shapes:

                if shape.shape_type != MSO_SHAPE_TYPE.PICTURE:
                    continue

                blob, extension = _get_shape_image_bytes(
                    shape
                )

                if not blob:
                    continue

                image_counter += 1

                image_id = (
                    f"pptx-image-{image_counter:04d}"
                )

                output_filename = (
                    f"{image_id}{extension}"
                )

                output_path = (
                    image_output_dir
                    / output_filename
                )

                with open(
                    output_path,
                    "wb"
                ) as image_file:

                    image_file.write(
                        blob
                    )

                image = DocumentImage(
                    image_id=image_id,
                    path=str(output_path),
                    filename=output_filename,
                    source_page=slide_number,
                    width=shape.width,
                    height=shape.height,
                    metadata={
                        "source_type": "pptx",
                        "slide": slide_number,
                        "shape_name": shape.name,
                    },
                )

                images.append(
                    image
                )

                slide_image_ids.append(
                    image_id
                )

            # -------------------------------------------------
            # Associate slide images with canonical blocks.
            #
            # AnyDoc's PPTX blocks contain source block indexes,
            # but the safest short-term representation is to
            # store slide information in metadata as well.
            # -------------------------------------------------

            for block in blocks:

                block_slide = block.metadata.get(
                    "slide"
                )

                if block_slide == slide_number:

                    block.image_ids.extend(
                        slide_image_ids
                    )

        # -----------------------------------------------------
        # If AnyDoc did not preserve slide metadata on blocks,
        # create a lightweight slide block for image-only slides.
        # -----------------------------------------------------

        existing_slides = {
            block.metadata.get("slide")
            for block in blocks
            if block.metadata.get("slide") is not None
        }

        for slide_number, slide in enumerate(
            presentation.slides,
            start=1
        ):

            slide_image_ids = [
                image.image_id
                for image in images
                if image.source_page == slide_number
            ]

            if not slide_image_ids:
                continue

            if slide_number in existing_slides:
                continue

            # Only create an image block when AnyDoc did not
            # give us a block for that slide.
            blocks.append(
                DocumentBlock(
                    type="slide",
                    text="",
                    level=None,
                    location={
                        "slide": slide_number
                    },
                    metadata={
                        "source": "pptx",
                        "slide": slide_number,
                        "image_only": True,
                    },
                    image_ids=slide_image_ids,
                )
            )

    # ---------------------------------------------------------
    # Other ZIP-based formats
    # ---------------------------------------------------------

    else:

        zip_based_formats = {
            ".docx": "docx",
            ".xlsx": "xlsx",
            ".odt": "odt",
        }

        source_type = zip_based_formats.get(
            path.suffix.lower()
        )

        if source_type:

            image_output_dir = (
                Path("data/images")
                / path.stem
            )

            try:

                images = extract_zip_images(
                    str(path),
                    str(image_output_dir),
                    source_type,
                )

            except Exception as e:

                print(
                    f"Warning: image extraction failed "
                    f"for {path.name}: {e}"
                )

    return CanonicalDocument(
        title=path.stem,
        source_format=path.suffix.lower().lstrip("."),
        blocks=blocks,
        images=images,
        metadata={
            "original_filename": path.name,
            "block_count": len(blocks),
            "image_count": len(images),
        },
    )
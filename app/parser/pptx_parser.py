from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from app.models.page import Page


def _get_shape_image_bytes(shape):
    """
    Resolve image bytes from a PowerPoint picture shape.

    Handles both:

    1. Normal embedded images:
       <a:blip r:embed="rId3"/>

    2. SVG images where the relationship is stored inside:
       <asvg:svgBlip r:embed="rId3"/>
    """

    # ---------------------------------------------------------
    # First try python-pptx's normal image interface.
    # ---------------------------------------------------------

    try:
        image = shape.image

        return image.blob, image.ext

    except (ValueError, AttributeError):
        pass

    # ---------------------------------------------------------
    # Some PPTX files store SVG images inside an extension:
    #
    # <a:blip>
    #     <a:extLst>
    #         <a:ext>
    #             <asvg:svgBlip r:embed="rId3"/>
    #
    # So inspect the complete XML element for r:embed.
    # ---------------------------------------------------------

    try:
        element = shape._element

        embed_attribute = (
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
        )

        # Search the picture XML tree for ANY element containing
        # the relationship ID.
        embed = None

        for child in element.iter():

            value = child.get(embed_attribute)

            if value:
                embed = value
                break

        if not embed:
            return None, None

        # Resolve the relationship through the slide part.
        relationship = shape.part.rels.get(embed)

        if relationship is None:
            return None, None

        target_part = relationship.target_part

        blob = target_part.blob

        # Determine the actual file extension.
        target_ref = str(
            relationship.target_ref
        )

        target_name = Path(target_ref).name

        extension = Path(
            target_name
        ).suffix.lower()

        if extension == ".jpeg":
            extension = ".jpg"

        if not extension:
            extension = ".png"

        return blob, extension

    except Exception as e:

        print(
            f"Warning: could not resolve PPTX image "
            f"on slide: {e}"
        )

        return None, None


def parse_pptx(file_path: str) -> list[Page]:
    """
    Parse a PowerPoint presentation into one Page per slide.

    Text is extracted from every text-bearing shape.

    Images are resolved from every picture shape and represented
    using image IDs associated with the corresponding Page.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"PowerPoint file not found: {file_path}"
        )

    presentation = Presentation(str(path))

    pages: list[Page] = []

    image_counter = 0

    for slide_number, slide in enumerate(
        presentation.slides,
        start=1
    ):

        text_parts: list[str] = []
        image_ids: list[str] = []

        for shape in slide.shapes:

            # -------------------------------------------------
            # TEXT
            # -------------------------------------------------

            if hasattr(shape, "text"):

                text = shape.text.strip()

                if text:
                    text_parts.append(text)

            # -------------------------------------------------
            # IMAGE
            # -------------------------------------------------

            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:

                blob, extension = _get_shape_image_bytes(
                    shape
                )

                if blob:

                    image_counter += 1

                    image_id = (
                        f"pptx-image-{image_counter:04d}"
                    )

                    image_ids.append(image_id)

        slide_text = "\n\n".join(
            text_parts
        ).strip()

        pages.append(
            Page(
                page_number=slide_number,
                text=slide_text,
                word_count=len(slide_text.split()),
                char_count=len(slide_text),
                image_ids=image_ids,
            )
        )

    return pages
from pathlib import Path
from zipfile import ZipFile

from app.parser.canonical_document import DocumentImage


IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp",
    ".svg",
}


def _safe_image_extension(filename: str) -> str:
    """
    Return a normalized image extension.
    """

    suffix = Path(filename).suffix.lower()

    if suffix in IMAGE_EXTENSIONS:
        return suffix

    return ".bin"


def _extract_generic_zip_images(
    file_path: str,
    output_dir: str,
    source_type: str,
) -> list[DocumentImage]:

    path = Path(file_path)

    output_path = Path(output_dir)
    output_path.mkdir(
        parents=True,
        exist_ok=True
    )

    images: list[DocumentImage] = []

    with ZipFile(path, "r") as archive:

        members = archive.namelist()

        image_members = [
            member
            for member in members
            if Path(member).suffix.lower()
            in IMAGE_EXTENSIONS
        ]

        for index, member in enumerate(
            image_members,
            start=1
        ):

            original_name = Path(member).name

            extension = _safe_image_extension(
                original_name
            )

            image_id = (
                f"{source_type}-image-{index:04d}"
            )

            output_filename = (
                f"{image_id}{extension}"
            )

            output_file = (
                output_path / output_filename
            )

            with archive.open(member) as source:

                with open(
                    output_file,
                    "wb"
                ) as destination:

                    destination.write(
                        source.read()
                    )

            images.append(
                DocumentImage(
                    image_id=image_id,
                    path=str(output_file),
                    filename=original_name,
                    metadata={
                        "source_member": member,
                        "source_type": source_type,
                    },
                )
            )

    return images


def _extract_pptx_images(
    file_path: str,
    output_dir: str,
) -> list[DocumentImage]:
    """
    Extract PPTX images while preserving their slide number.

    Uses the underlying PPTX XML relationship (r:embed)
    instead of relying on python-pptx's shape.image property.

    This handles picture shapes that python-pptx recognizes but
    does not expose through shape.image.
    """

    try:
        from pptx import Presentation
    except ImportError as e:
        raise ValueError(
            "python-pptx is required for PPTX image extraction."
        ) from e

    path = Path(file_path)

    output_path = Path(output_dir)
    output_path.mkdir(
        parents=True,
        exist_ok=True
    )

    presentation = Presentation(str(path))

    images: list[DocumentImage] = []

    image_counter = 0

    # ---------------------------------------------------------
    # Process every slide.
    # ---------------------------------------------------------

    for slide_number, slide in enumerate(
        presentation.slides,
        start=1
    ):

        # -----------------------------------------------------
        # Process every picture shape.
        # -----------------------------------------------------

        for shape in slide.shapes:

            if shape.shape_type != 13:
                continue

            try:

                # -------------------------------------------------
                # Get the <a:blip> element.
                # -------------------------------------------------

                blip = shape._element.blipFill.blip

                # -------------------------------------------------
                # Read the actual XML relationship attribute:
                #
                # r:embed="rIdX"
                # -------------------------------------------------

                relationship_id = blip.get(
                    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
                )

                if not relationship_id:
                    raise ValueError(
                        "Picture has no r:embed relationship."
                    )

                # -------------------------------------------------
                # Resolve relationship to actual image part.
                # -------------------------------------------------

                relationship = slide.part.rels[
                    relationship_id
                ]

                image_part = relationship.target_part

                # -------------------------------------------------
                # Original image filename.
                # -------------------------------------------------

                original_name = Path(
                    str(image_part.partname)
                ).name

                extension = _safe_image_extension(
                    original_name
                )

                image_counter += 1

                image_id = (
                    f"pptx-image-{image_counter:04d}"
                )

                output_filename = (
                    f"{image_id}{extension}"
                )

                output_file = (
                    output_path / output_filename
                )

                # -------------------------------------------------
                # Write image bytes.
                # -------------------------------------------------

                with open(
                    output_file,
                    "wb"
                ) as destination:

                    destination.write(
                        image_part.blob
                    )

                images.append(
                    DocumentImage(
                        image_id=image_id,
                        path=str(output_file),
                        filename=original_name,
                        source_page=slide_number,
                        source_block=None,
                        width=shape.width,
                        height=shape.height,
                        metadata={
                            "source_type": "pptx",
                            "slide_number": slide_number,
                            "relationship_id": relationship_id,
                            "shape_name": shape.name,
                            "shape_type": int(
                                shape.shape_type
                            ),
                            "left": shape.left,
                            "top": shape.top,
                        },
                    )
                )

            except Exception as e:

                print(
                    f"Warning: could not resolve "
                    f"PPTX image on slide "
                    f"{slide_number}: {e}"
                )

    return images


def extract_zip_images(
    file_path: str,
    output_dir: str,
    source_type: str,
) -> list[DocumentImage]:
    """
    Extract embedded images from supported document formats.

    PPTX uses slide-aware relationship extraction.

    Other ZIP-based formats use generic extraction.
    """

    path = Path(file_path)

    if not path.exists():

        raise FileNotFoundError(
            f"Document not found: {file_path}"
        )

    try:

        if source_type.lower() == "pptx":

            return _extract_pptx_images(
                str(path),
                output_dir,
            )

        return _extract_generic_zip_images(
            str(path),
            output_dir,
            source_type,
        )

    except Exception as e:

        raise ValueError(
            f"Unable to extract images from "
            f"{file_path}: {e}"
        ) from e
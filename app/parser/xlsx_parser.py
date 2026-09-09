from pathlib import Path
from typing import Any

from openpyxl import load_workbook
from app.models.page import Page

from app.parser.canonical_document import (
    CanonicalDocument,
    DocumentBlock,
    DocumentImage,
)


def _cell_to_text(value: Any) -> str:
    """
    Convert an Excel cell value into clean text.
    """

    if value is None:
        return ""

    return str(value).strip()


def _row_to_text(values: tuple[Any, ...]) -> str:
    """
    Convert one Excel row into a tab-separated text representation.
    """

    cells = [
        _cell_to_text(value)
        for value in values
    ]

    # Remove trailing empty cells.
    while cells and not cells[-1]:
        cells.pop()

    return " | ".join(cells)


def parse_xlsx_to_canonical(
    file_path: str
) -> CanonicalDocument:
    """
    Parse an XLSX workbook into the canonical document format.

    Structure:

        Workbook
            -> Sheet heading
                -> Table blocks

    Each worksheet becomes a level-1 heading.

    Rows are grouped into reasonably sized table blocks rather
    than creating one canonical block per row.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Document not found: {file_path}"
        )

    if path.suffix.lower() != ".xlsx":
        raise ValueError(
            f"Expected an XLSX file, got: {path.suffix}"
        )

    workbook = load_workbook(
        filename=str(path),
        read_only=True,
        data_only=True,
    )

    blocks: list[DocumentBlock] = []
    images: list[DocumentImage] = []

    block_index = 0

    # Number of rows grouped into one table block.
    ROWS_PER_BLOCK = 50

    for sheet_index, worksheet in enumerate(
        workbook.worksheets,
        start=1
    ):

        # ----------------------------------------------------
        # Sheet heading
        # ----------------------------------------------------

        sheet_title = worksheet.title.strip()

        blocks.append(
            DocumentBlock(
                type="heading",
                text=sheet_title,
                level=1,
                location={
                    "sheet": sheet_index,
                    "sheet_name": sheet_title,
                },
                metadata={
                    "source": "openpyxl",
                    "source_type": "xlsx",
                    "sheet_index": sheet_index,
                    "sheet_name": sheet_title,
                },
            )
        )

        block_index += 1

        rows_buffer: list[str] = []
        first_row_number: int | None = None
        last_row_number: int | None = None

        # ----------------------------------------------------
        # Read worksheet rows
        # ----------------------------------------------------

        for row_number, row in enumerate(
            worksheet.iter_rows(
                values_only=True
            ),
            start=1
        ):

            row_text = _row_to_text(row)

            # Ignore completely empty rows.
            if not row_text:
                continue

            if first_row_number is None:
                first_row_number = row_number

            last_row_number = row_number

            rows_buffer.append(
                row_text
            )

            # ------------------------------------------------
            # Flush a table block every 50 non-empty rows.
            # ------------------------------------------------

            if len(rows_buffer) >= ROWS_PER_BLOCK:

                table_text = "\n".join(
                    rows_buffer
                )

                blocks.append(
                    DocumentBlock(
                        type="table",
                        text=table_text,
                        level=None,
                        location={
                            "sheet": sheet_index,
                            "sheet_name": sheet_title,
                            "start_row": first_row_number,
                            "end_row": last_row_number,
                        },
                        metadata={
                            "source": "openpyxl",
                            "source_type": "xlsx",
                            "sheet_index": sheet_index,
                            "sheet_name": sheet_title,
                            "start_row": first_row_number,
                            "end_row": last_row_number,
                            "row_count": len(rows_buffer),
                        },
                    )
                )

                block_index += 1

                rows_buffer = []
                first_row_number = None
                last_row_number = None

        # ----------------------------------------------------
        # Flush remaining rows.
        # ----------------------------------------------------

        if rows_buffer:

            table_text = "\n".join(
                rows_buffer
            )

            blocks.append(
                DocumentBlock(
                    type="table",
                    text=table_text,
                    level=None,
                    location={
                        "sheet": sheet_index,
                        "sheet_name": sheet_title,
                        "start_row": first_row_number,
                        "end_row": last_row_number,
                    },
                    metadata={
                        "source": "openpyxl",
                        "source_type": "xlsx",
                        "sheet_index": sheet_index,
                        "sheet_name": sheet_title,
                        "start_row": first_row_number,
                        "end_row": last_row_number,
                        "row_count": len(rows_buffer),
                    },
                )
            )

            block_index += 1

    sheet_count = len(workbook.worksheets)

    workbook.close()

    return CanonicalDocument(
        title=path.stem,
        source_format="xlsx",
        blocks=blocks,
        images=images,
        metadata={
            "original_filename": path.name,
            "sheet_count": sheet_count,
            "block_count": len(blocks),
            "image_count": len(images),
        },
    )

def parse_xlsx_to_pages(
    file_path: str,
    rows_per_page: int = 50,
) -> list[Page]:
    """
    Convert an XLSX workbook into Page objects while preserving
    column names for every record.

    Each worksheet becomes a sequence of artificial pages.

    Every row is represented as a key-value record:

        Column A: value
        Column B: value
        ...

    Column headers are repeated on every page so that each
    chunk remains self-contained for retrieval and LLM processing.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Document not found: {file_path}"
        )

    workbook = load_workbook(
        filename=str(path),
        read_only=True,
        data_only=True,
    )

    pages: list[Page] = []
    page_number = 1

    for worksheet in workbook.worksheets:

        rows = worksheet.iter_rows(
            values_only=True
        )

        # ----------------------------------------------------
        # Read the first non-empty row as the header row.
        # ----------------------------------------------------

        headers = None

        for row in rows:

            values = [
                _cell_to_text(value)
                for value in row
            ]

            if any(values):
                headers = values
                break

        if not headers:
            continue

        # ----------------------------------------------------
        # Read data rows.
        # ----------------------------------------------------

        current_records: list[str] = []
        first_row_number = None
        last_row_number = None

        for row_number, row in enumerate(
            rows,
            start=2
        ):

            values = [
                _cell_to_text(value)
                for value in row
            ]

            # Skip completely empty rows.
            if not any(values):
                continue

            if first_row_number is None:
                first_row_number = row_number

            last_row_number = row_number

            # ------------------------------------------------
            # Convert row to explicit column → value mapping.
            # ------------------------------------------------

            record_lines = [
                "Hotel Record"
            ]

            for column_index, header in enumerate(headers):

                value = (
                    values[column_index]
                    if column_index < len(values)
                    else ""
                )

                # Keep empty values explicit.
                if not value:
                    value = "(empty)"

                record_lines.append(
                    f"{header}: {value}"
                )

            current_records.append(
                "\n".join(record_lines)
            )

            # ------------------------------------------------
            # Create a page after N records.
            # ------------------------------------------------

            if len(current_records) >= rows_per_page:

                page_text = (
                    f"Sheet: {worksheet.title}\n\n"
                    "Columns: "
                    + " | ".join(headers)
                    + "\n\n"
                    + "\n\n".join(current_records)
                )

                pages.append(
                    Page(
                        page_number=page_number,
                        text=page_text,
                        word_count=len(
                            page_text.split()
                        ),
                        char_count=len(page_text),
                    )
                )

                page_number += 1

                current_records = []
                first_row_number = None
                last_row_number = None

        # ----------------------------------------------------
        # Remaining records.
        # ----------------------------------------------------

        if current_records:

            page_text = (
                f"Sheet: {worksheet.title}\n\n"
                "Columns: "
                + " | ".join(headers)
                + "\n\n"
                + "\n\n".join(current_records)
            )

            pages.append(
                Page(
                    page_number=page_number,
                    text=page_text,
                    word_count=len(
                        page_text.split()
                    ),
                    char_count=len(page_text),
                )
            )

            page_number += 1

    workbook.close()

    return pages
from pydantic import BaseModel, Field


class Page(BaseModel):
    page_number: int
    text: str
    word_count: int
    char_count: int

    # Images/visual assets belonging to this page.
    image_ids: list[str] = Field(default_factory=list)
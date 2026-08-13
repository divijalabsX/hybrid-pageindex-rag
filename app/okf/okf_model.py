from pydantic import BaseModel, Field
from typing import List


class OKFKnowledgeItem(BaseModel):
    title: str
    type: str = "Section"
    description: str = ""
    source: str = ""
    start_page: int = 0
    end_page: int = 0
    content: str = ""
    children: List["OKFKnowledgeItem"] = Field(default_factory=list)
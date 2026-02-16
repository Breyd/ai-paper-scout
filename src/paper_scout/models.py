from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Paper(BaseModel):
    id: str
    title: str
    authors: List[str] = Field(default_factory=list)
    abstract: str = ""
    url: str
    published_at: datetime
    source: str = "arxiv"
    categories: List[str] = Field(default_factory=list)
    doi: Optional[str] = None

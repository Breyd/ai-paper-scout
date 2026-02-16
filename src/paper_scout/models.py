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

    # SPOJ fit enrichment (added by pipeline)
    spoj_fit_score: Optional[int] = None
    spoj_fit_tags: List[str] = Field(default_factory=list)
    spoj_fit_reasons: List[str] = Field(default_factory=list)

    # Extracted benchmarks (e.g., SWE-bench, HumanEval)
    spoj_benchmarks: List[str] = Field(default_factory=list)

    primary_contact_name: str = ""
    primary_contact_hint: str = ""

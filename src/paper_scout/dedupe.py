from __future__ import annotations

import hashlib
from typing import Iterable, List, Set

from paper_scout.models import Paper


def stable_paper_key(p: Paper) -> str:
    # Prefer arXiv ID if present
    if p.id and p.id.startswith("arxiv:"):
        return p.id

    # Fallback: hash(title + first author + year)
    first_author = p.authors[0] if p.authors else ""
    year = p.published_at.year if p.published_at else ""
    raw = f"{p.title}|{first_author}|{year}".lower().strip()
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"hash:{h}"


def dedupe_papers(papers: Iterable[Paper]) -> List[Paper]:
    seen: Set[str] = set()
    out: List[Paper] = []
    for p in papers:
        k = stable_paper_key(p)
        if k in seen:
            continue
        seen.add(k)
        p.id = k
        out.append(p)
    return out

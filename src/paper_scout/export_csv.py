from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from paper_scout.models import Paper


CSV_FIELDS = [
    "id",
    "published_at",
    "title",
    "authors",
    "url",
    "source",
    "categories",
    "abstract",
]


def write_csv(path: Path, papers: Iterable[Paper]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for p in papers:
            w.writerow(
                {
                    "id": p.id,
                    "published_at": p.published_at.isoformat(),
                    "title": p.title,
                    "authors": "; ".join(p.authors),
                    "url": p.url,
                    "source": p.source,
                    "categories": "; ".join(p.categories),
                    "abstract": p.abstract,
                }
            )

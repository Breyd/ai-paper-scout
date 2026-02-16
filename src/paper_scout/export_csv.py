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
    "spoj_fit_score",
    "spoj_fit_tags",
    "spoj_fit_reasons",
    "primary_contact_name",
    "primary_contact_hint",
    "linkedin_search_url",
    "linkedin_search_disclaimer",
    "spoj_benchmarks",
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
                    "spoj_fit_score": p.spoj_fit_score if p.spoj_fit_score is not None else "",
                    "spoj_fit_tags": "; ".join(p.spoj_fit_tags),
                    "spoj_fit_reasons": " | ".join(p.spoj_fit_reasons),
                    "primary_contact_name": getattr(p, "primary_contact_name", ""),
                    "primary_contact_hint": getattr(p, "primary_contact_hint", ""),
                    "linkedin_search_url": getattr(p, "linkedin_search_url", ""),
                    "linkedin_search_disclaimer": getattr(p, "linkedin_search_disclaimer", ""),
                    "spoj_benchmarks": "; ".join(getattr(p, "spoj_benchmarks", []) or []),
                    "abstract": p.abstract,
                }
            )

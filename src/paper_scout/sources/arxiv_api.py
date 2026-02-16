from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import feedparser
import requests

from paper_scout.models import Paper

ARXIV_API_URL = "http://export.arxiv.org/api/query"


def _build_search_query(categories: List[str]) -> str:
    return " OR ".join([f"cat:{c}" for c in categories])


def fetch_arxiv_api(
    categories: List[str],
    months: int = 6,
    page_size: int = 200,
    max_total: int = 5000,
    polite_sleep_seconds: float = 3.0,
) -> List[Paper]:
    """
    Pull papers from arXiv API sorted by submittedDate desc, page through results,
    stop when we reach cutoff (now - months).
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=int(months * 30.5))

    search_query = _build_search_query(categories)

    out: List[Paper] = []
    start = 0

    while len(out) < max_total:
        params = {
            "search_query": search_query,
            "start": start,
            "max_results": page_size,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        r = requests.get(ARXIV_API_URL, params=params, timeout=30)
        r.raise_for_status()

        feed = feedparser.parse(r.text)
        entries = getattr(feed, "entries", []) or []
        if not entries:
            break

        reached_cutoff = False

        for e in entries:
            if getattr(e, "published_parsed", None):
                published = datetime(*e.published_parsed[:6], tzinfo=timezone.utc)
            else:
                published = now

            if published < cutoff:
                reached_cutoff = True
                break

            url = e.link
            raw_id = getattr(e, "id", "") or url
            arxiv_id = raw_id.rstrip("/").split("/")[-1]

            title = (getattr(e, "title", "") or "").replace("\n", " ").strip()
            abstract = (getattr(e, "summary", "") or "").replace("\n", " ").strip()

            authors: List[str] = []
            if getattr(e, "authors", None):
                authors = [a.get("name", "").strip() for a in e.authors if a.get("name")]
            else:
                raw_author = getattr(e, "author", "") or ""
                authors = [a.strip() for a in raw_author.split(",") if a.strip()]

            tags: List[str] = []
            if getattr(e, "tags", None):
                tags = [t.get("term", "").strip() for t in e.tags if t.get("term")]

            doi: Optional[str] = None
            if getattr(e, "arxiv_doi", None):
                doi = str(e.arxiv_doi).strip() or None

            out.append(
                Paper(
                    id=f"arxiv:{arxiv_id}",
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    url=url,
                    published_at=published,
                    source="arxiv",
                    categories=tags,
                    doi=doi,
                )
            )

            if len(out) >= max_total:
                break

        if reached_cutoff:
            break

        start += page_size
        time.sleep(polite_sleep_seconds)

    return out

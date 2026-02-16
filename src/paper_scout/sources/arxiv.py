from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

import feedparser

from paper_scout.models import Paper


def _arxiv_rss_url(category: str) -> str:
    return f"http://export.arxiv.org/rss/{category}"


def fetch_arxiv_rss(categories: List[str], days: int = 1, max_results_per_cat: int = 50) -> List[Paper]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)

    papers: List[Paper] = []

    for cat in categories:
        feed = feedparser.parse(_arxiv_rss_url(cat))

        count = 0
        for e in feed.entries:
            if count >= max_results_per_cat:
                break

            if getattr(e, "published_parsed", None):
                published = datetime(*e.published_parsed[:6], tzinfo=timezone.utc)
            else:
                published = now

            if published < cutoff:
                continue

            url = e.link
            arxiv_id = url.rstrip("/").split("/")[-1]

            title = (e.title or "").replace("\n", " ").strip()
            abstract = (getattr(e, "summary", "") or "").replace("\n", " ").strip()

            raw_author = getattr(e, "author", "") or ""
            authors = [a.strip() for a in raw_author.split(",") if a.strip()]

            tags = []
            if getattr(e, "tags", None):
                tags = [t.get("term", "").strip() for t in e.tags if t.get("term")]

            papers.append(
                Paper(
                    id=f"arxiv:{arxiv_id}",
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    url=url,
                    published_at=published,
                    source="arxiv",
                    categories=tags or [cat],
                )
            )
            count += 1

    return papers

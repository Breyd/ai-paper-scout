from __future__ import annotations

from typing import List, Tuple

from paper_scout.models import Paper


def pick_primary_contact(p: Paper) -> Tuple[str, str]:
    """
    Returns (name, hint).
    Heuristic:
      - if 1 author -> that one
      - if 2 authors -> first author (often primary)
      - if 3+ -> last author (often PI) + hint; and first author as alternate in hint
    """
    authors: List[str] = list(p.authors or [])
    authors = [a.strip() for a in authors if a and a.strip()]

    if not authors:
        return ("", "no authors listed")

    if len(authors) == 1:
        return (authors[0], "single-author paper")

    if len(authors) == 2:
        return (authors[0], "2 authors: using first author as primary")

    # 3+ authors
    first = authors[0]
    last = authors[-1]
    hint = f"3+ authors: using last author (often PI). Alternate: first author = {first}"
    return (last, hint)

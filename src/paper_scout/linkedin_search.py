from __future__ import annotations

from urllib.parse import quote_plus

from paper_scout.models import Paper


DISCLAIMER = "Auto-generated search link (not verified). Please confirm the correct profile manually."


def build_linkedin_search_query(p: Paper) -> str:
    name = (getattr(p, "primary_contact_name", "") or "").strip()
    if not name:
        return ""

    # Optional signals (if you later enrich affiliations/homepage etc.)
    aff = (getattr(p, "primary_contact_affiliation", "") or "").strip()

    # Prefer linkedin public profile paths
    base = f'"{name}" site:linkedin.com/in'
    if aff:
        base = f'"{name}" "{aff}" site:linkedin.com/in'

    return base


def build_google_search_url(query: str) -> str:
    if not query:
        return ""
    return "https://www.google.com/search?q=" + quote_plus(query)


def build_duckduckgo_search_url(query: str) -> str:
    if not query:
        return ""
    return "https://duckduckgo.com/?q=" + quote_plus(query)


def add_linkedin_search_fields(p: Paper) -> None:
    q = build_linkedin_search_query(p)
    p.linkedin_search_query = q
    p.linkedin_search_url = build_google_search_url(q)  # default
    p.linkedin_search_disclaimer = DISCLAIMER

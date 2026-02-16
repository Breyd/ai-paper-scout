from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional, Tuple

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas

from paper_scout.models import Paper


@dataclass
class ReportMeta:
    generated_at: datetime
    window_label: str
    categories: str
    total_papers: int
    top_n: int


# Fonts
TITLE = ("Helvetica-Bold", 18)
H2 = ("Helvetica-Bold", 12)
H3 = ("Helvetica-Bold", 10)
BODY = ("Helvetica", 9)
SMALL = ("Helvetica", 8)


def _draw_wrapped_text(
    c: Canvas,
    text: str,
    x: float,
    y: float,
    max_w: float,
    font_name: str,
    font_size: int,
    leading: float = 12.0,
    max_lines: Optional[int] = None,
) -> float:
    """Draw wrapped text; returns new y (after drawing)."""
    if not text:
        return y
    c.setFont(font_name, font_size)

    words = text.replace("\n", " ").split()
    if not words:
        return y

    line = ""
    lines: List[str] = []
    for w in words:
        test = (line + " " + w).strip()
        if c.stringWidth(test, font_name, font_size) <= max_w:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)

    if max_lines is not None:
        lines = lines[:max_lines]

    for ln in lines:
        c.drawString(x, y, ln)
        y -= (leading / 72.0) * 72.0  # keep numeric stable; effectively y -= leading
        # (reportlab uses points; but we pass leading in points; y is in points)
    return y


def generate_pdf(out_path, papers_sorted: List[Paper], meta: ReportMeta):
    page_w, page_h = A4
    margin_x = 1.7 * cm
    margin_y = 1.5 * cm
    max_w = page_w - 2 * margin_x

    c = Canvas(str(out_path), pagesize=A4)

    def new_page():
        c.showPage()

    def linkify(url: str, x: float, y: float):
        if not url:
            return
        try:
            c.linkURL(url, (x, y - 2, x + max_w, y + 10), relative=0)
        except Exception:
            pass

    # ---------- Cover ----------
    y = page_h - margin_y
    c.setFont(*TITLE)
    c.drawString(margin_x, y, "AI Paper Scout Report")
    y -= 1.0 * cm

    c.setFont(*BODY)
    c.drawString(margin_x, y, f"Window: {meta.window_label}")
    y -= 0.55 * cm
    c.drawString(margin_x, y, f"Categories: {meta.categories}")
    y -= 0.55 * cm
    c.drawString(margin_x, y, f"Total papers fetched: {meta.total_papers}")
    y -= 0.55 * cm
    c.drawString(margin_x, y, f"Top N in PDF: {meta.top_n}")
    y -= 0.55 * cm
    c.drawString(margin_x, y, f"Generated (UTC): {meta.generated_at.isoformat(timespec='minutes')}")
    y -= 0.7 * cm

    c.setFont(*SMALL)
    c.drawString(
        margin_x,
        y,
        "LinkedIn search links are auto-generated (not verified). Please confirm manually.",
    )
    y -= 0.7 * cm

    c.setFont(*SMALL)
    c.drawString(margin_x, y, "Scoring: heuristic fit for SPOJ-like code+verdict datasets.")
    y -= 0.7 * cm

    # ---------- TOC ----------
    new_page()
    y = page_h - margin_y
    c.setFont(*H2)
    c.drawString(margin_x, y, "Top papers (quick list)")
    y -= 0.8 * cm

    c.setFont(*SMALL)
    for idx, p in enumerate(papers_sorted[: meta.top_n], start=1):
        if y < (margin_y + 2.5 * cm):
            new_page()
            y = page_h - margin_y
            c.setFont(*SMALL)
        score = getattr(p, "spoj_fit_score", 0) or 0
        title = (p.title or "").strip()
        line = f"{idx:02d}. [{score:3d}] {title}"
        y = _draw_wrapped_text(c, line, margin_x, y, max_w, SMALL[0], SMALL[1], leading=11, max_lines=2)
        y -= 0.2 * cm

    # ---------- Details ----------
    new_page()
    y = page_h - margin_y

    for idx, p in enumerate(papers_sorted[: meta.top_n], start=1):
        if y < (margin_y + 6.0 * cm):
            new_page()
            y = page_h - margin_y

        score = getattr(p, "spoj_fit_score", 0) or 0
        tags = getattr(p, "spoj_fit_tags", []) or []
        reasons = getattr(p, "spoj_fit_reasons", []) or []
        benches = getattr(p, "spoj_benchmarks", []) or []

        c.setFont(*H2)
        c.drawString(margin_x, y, f"{idx:02d}. [{score}] {p.title or ''}")
        y -= 0.6 * cm

        c.setFont(*SMALL)
        pub = getattr(p, "published_at", None)
        c.drawString(margin_x, y, f"Published: {pub.isoformat(timespec='minutes') if pub else ''}")
        y -= 0.45 * cm

        authors = "; ".join(p.authors or [])
        if authors:
            y = _draw_wrapped_text(c, f"Authors: {authors}", margin_x, y, max_w, SMALL[0], SMALL[1], leading=11, max_lines=3)
            y -= 0.15 * cm

        cat = "; ".join(p.categories or [])
        if cat:
            y = _draw_wrapped_text(c, f"Categories: {cat}", margin_x, y, max_w, SMALL[0], SMALL[1], leading=11, max_lines=2)
            y -= 0.15 * cm

        if benches:
            y = _draw_wrapped_text(c, f"Benchmarks: {', '.join(benches)}", margin_x, y, max_w, SMALL[0], SMALL[1], leading=11, max_lines=2)
            y -= 0.15 * cm

        if tags:
            y = _draw_wrapped_text(c, f"Tags: {', '.join(tags)}", margin_x, y, max_w, SMALL[0], SMALL[1], leading=11, max_lines=2)
            y -= 0.15 * cm

        # Primary contact
        primary = (getattr(p, "primary_contact_name", "") or "").strip()
        hint = (getattr(p, "primary_contact_hint", "") or "").strip()
        if primary:
            line = f"Primary contact: {primary}"
            if hint:
                line += f" ({hint})"
            y = _draw_wrapped_text(c, line, margin_x, y, max_w, SMALL[0], SMALL[1], leading=11, max_lines=2)
            y -= 0.15 * cm

        # LinkedIn search (primary contact)
        li = (getattr(p, "linkedin_search_url", "") or "").strip()
        if li:
            c.setFont(*SMALL)
            c.drawString(margin_x, y, "LinkedIn search:")
            link_x = margin_x + 2.6 * cm
            c.drawString(link_x, y, li)
            linkify(li, link_x, y)
            y -= 0.55 * cm

        # SPOJ pitch angle (optional)
        try:
            from paper_scout.pitch import build_spoj_pitch  # type: ignore
            pitch_one, pitch_bullets = build_spoj_pitch(p)
            y = _draw_wrapped_text(c, "SPOJ angle:", margin_x, y, max_w, SMALL[0], SMALL[1], leading=11, max_lines=1)
            y = _draw_wrapped_text(c, pitch_one, margin_x + 0.4 * cm, y, max_w - 0.4 * cm, SMALL[0], SMALL[1], leading=11, max_lines=3)
            for b in (pitch_bullets or [])[:3]:
                y = _draw_wrapped_text(c, f"- {b}", margin_x + 0.8 * cm, y, max_w - 0.8 * cm, SMALL[0], SMALL[1], leading=11, max_lines=2)
            y -= 0.15 * cm
        except Exception:
            pass

        # Reasons (trim)
        if reasons:
            y = _draw_wrapped_text(c, "Reasons:", margin_x, y, max_w, SMALL[0], SMALL[1], leading=11, max_lines=1)
            for r in reasons[:4]:
                y = _draw_wrapped_text(c, f"- {r}", margin_x + 0.4 * cm, y, max_w - 0.4 * cm, SMALL[0], SMALL[1], leading=11, max_lines=2)
            y -= 0.15 * cm

        # Abstract (trim)
        abstract = (p.abstract or "").strip()
        if abstract:
            if len(abstract) > 900:
                abstract = abstract[:900] + "…"
            y = _draw_wrapped_text(c, "Abstract:", margin_x, y, max_w, SMALL[0], SMALL[1], leading=11, max_lines=1)
            y = _draw_wrapped_text(c, abstract, margin_x + 0.4 * cm, y, max_w - 0.4 * cm, SMALL[0], SMALL[1], leading=11, max_lines=10)
            y -= 0.15 * cm

        # Paper URL
        url = (p.url or "").strip()
        if url:
            c.setFont(*SMALL)
            c.drawString(margin_x, y, "Paper:")
            link_x = margin_x + 1.3 * cm
            c.drawString(link_x, y, url)
            linkify(url, link_x, y)
            y -= 0.7 * cm

        # Divider
        c.setLineWidth(0.5)
        c.line(margin_x, y, margin_x + max_w, y)
        y -= 0.6 * cm

    # ---------- Authors index ----------
    new_page()
    y = page_h - margin_y
    c.setFont(*H2)
    c.drawString(margin_x, y, "Authors index")
    y -= 0.8 * cm
    c.setFont(*SMALL)
    c.drawString(margin_x, y, "Author → top papers (score + title + link) + LinkedIn search link")
    y -= 0.8 * cm

    # Build author map from top-N papers included in report
    author_map = {}
    for pp in papers_sorted[: meta.top_n]:
        s = getattr(pp, "spoj_fit_score", 0) or 0
        t = (pp.title or "").strip()
        u = (pp.url or "").strip()
        for a in (pp.authors or []):
            a = (a or "").strip()
            if not a:
                continue
            author_map.setdefault(a, []).append((s, t, u))

    # Import helper (if available)
    try:
        from paper_scout.linkedin_search import build_google_linkedin_search_for_author  # type: ignore
    except Exception:
        build_google_linkedin_search_for_author = None

    for author in sorted(author_map.keys(), key=lambda x: x.lower()):
        if y < (margin_y + 3.0 * cm):
            new_page()
            y = page_h - margin_y
            c.setFont(*SMALL)

        # Author name
        y = _draw_wrapped_text(
            c,
            author,
            margin_x,
            y,
            max_w,
            SMALL[0],
            SMALL[1],
            leading=11,
            max_lines=1,
        )

        # LinkedIn search (author)
        if build_google_linkedin_search_for_author is not None:
            li_author = (build_google_linkedin_search_for_author(author) or "").strip()
            if li_author:
                c.setFont(*SMALL)
                c.drawString(margin_x + 0.4 * cm, y, "LinkedIn search (author):")
                link_x = margin_x + 4.0 * cm
                c.drawString(link_x, y, li_author)
                linkify(li_author, link_x, y)
                y -= 0.55 * cm

        # Top 5 papers per author
        items = sorted(author_map[author], key=lambda t: t[0], reverse=True)[:5]
        for s, title, url in items:
            if y < (margin_y + 2.5 * cm):
                new_page()
                y = page_h - margin_y
                c.setFont(*SMALL)

            t = (title[:90] + "…") if len(title) > 90 else title
            y = _draw_wrapped_text(
                c,
                f"- [{s:3d}] {t}",
                margin_x + 0.4 * cm,
                y,
                max_w - 0.4 * cm,
                SMALL[0],
                SMALL[1],
                leading=11,
                max_lines=2,
            )

            if url:
                c.setFont(*SMALL)
                c.drawString(margin_x + 0.8 * cm, y, url)
                linkify(url, margin_x + 0.8 * cm, y)
                y -= 0.55 * cm

        y -= 0.4 * cm

    c.save()
    return out_path

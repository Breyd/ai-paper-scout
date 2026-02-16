from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from reportlab.lib import pagesizes
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from paper_scout.models import Paper
from paper_scout.pitch import build_spoj_pitch


@dataclass
class ReportMeta:
    generated_at: datetime
    window_label: str
    categories: str
    total_papers: int
    top_n: int


def _draw_wrapped_text(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    font_name: str,
    font_size: int,
    leading: float,
    max_lines: Optional[int] = None,
) -> float:
    c.setFont(font_name, font_size)
    words = (text or "").split()
    lines: List[str] = []
    cur: List[str] = []

    for w in words:
        trial = (" ".join(cur + [w])).strip()
        if stringWidth(trial, font_name, font_size) <= max_width:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))

    if max_lines is not None:
        lines = lines[:max_lines]

    for line in lines:
        c.drawString(x, y, line)
        y -= leading

    return y


def generate_pdf(
    out_path: Path,
    papers_sorted: List[Paper],
    meta: ReportMeta,
    page_size=pagesizes.A4,
) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_path), pagesize=page_size)
    width, height = page_size

    margin_x = 2.0 * cm
    margin_y = 2.0 * cm
    max_w = width - 2 * margin_x

    H1 = ("Helvetica-Bold", 16)
    H2 = ("Helvetica-Bold", 12)
    P = ("Helvetica", 10)
    SMALL = ("Helvetica", 9)

    def new_page():
        c.showPage()

    # First page header
    y = height - margin_y
    c.setFont(*H1)
    c.drawString(margin_x, y, "AI Paper Scout — Report")
    y -= 1.0 * cm

    c.setFont(*P)
    c.drawString(margin_x, y, f"Generated: {meta.generated_at.isoformat(timespec='minutes')}")
    y -= 0.6 * cm
    c.drawString(margin_x, y, f"Window: {meta.window_label}")
    y -= 0.6 * cm
    c.drawString(margin_x, y, f"Categories: {meta.categories or '(all)'}")
    y -= 0.6 * cm
    c.drawString(margin_x, y, f"Fetched papers: {meta.total_papers}")
    y -= 0.6 * cm
    c.drawString(margin_x, y, f"Top N in this report: {meta.top_n}")
    y -= 1.0 * cm

    c.setFont(*SMALL)
    c.drawString(margin_x, y, "Scoring: heuristic fit for SPOJ-like code+verdict datasets.")
    y -= 0.6 * cm
    c.drawString(margin_x, y, "LinkedIn search links are auto-generated (not verified). Please confirm manually.")
    y -= 1.0 * cm

    new_page()
    y = height - margin_y

    # --- TOC (Top titles) ---
    c.setFont(*H2)
    c.drawString(margin_x, y, "Top papers (quick list)")
    y -= 0.8 * cm

    c.setFont(*SMALL)
    for idx, p in enumerate(papers_sorted[: meta.top_n], start=1):
        if y < (margin_y + 2.5 * cm):
            new_page()
            y = height - margin_y
            c.setFont(*SMALL)
        score = getattr(p, "spoj_fit_score", 0) or 0
        title = (p.title or "").strip()
        line = f"{idx:02d}. [{score:3d}] {title}"
        # wrap a bit (two lines max)
        y = _draw_wrapped_text(c, line, margin_x, y, max_w, SMALL[0], SMALL[1], leading=12, max_lines=2)
        y -= 0.2 * cm

    new_page()
    y = height - margin_y

    # --- TOC (Top titles) ---
    c.setFont(*H2)
    c.drawString(margin_x, y, "Top papers (quick list)")
    y -= 0.8 * cm

    c.setFont(*SMALL)
    for idx, p in enumerate(papers_sorted[: meta.top_n], start=1):
        if y < (margin_y + 2.5 * cm):
            new_page()
            y = height - margin_y
            c.setFont(*SMALL)
        score = getattr(p, "spoj_fit_score", 0) or 0
        title = (p.title or "").strip()
        line = f"{idx:02d}. [{score:3d}] {title}"
        y = _draw_wrapped_text(c, line, margin_x, y, max_w, SMALL[0], SMALL[1], leading=12, max_lines=2)
        y -= 0.2 * cm

    new_page()
    y = height - margin_y

    for idx, p in enumerate(papers_sorted[: meta.top_n], start=1):


        if y < (margin_y + 6 * cm):
            new_page()
            y = height - margin_y

        c.setFont(*H2)
        y = _draw_wrapped_text(c, f"{idx}. {p.title}", margin_x, y, max_w, H2[0], H2[1], leading=14)

        score = getattr(p, "spoj_fit_score", 0) or 0
        tags = "; ".join(getattr(p, "spoj_fit_tags", []) or [])
        benches = "; ".join(getattr(p, "spoj_benchmarks", []) or [])
        y = _draw_wrapped_text(
            c,
            f"Score: {score}    Tags: {tags or '-'}    Benchmarks: {benches or '-'}",
            margin_x,
            y,
            max_w,
            SMALL[0],
            SMALL[1],
            leading=12,
        )

        authors = "; ".join(p.authors or [])
        cats = "; ".join(p.categories or [])
        published = p.published_at.isoformat(timespec="minutes") if getattr(p, "published_at", None) else ""
        y = _draw_wrapped_text(c, f"Published: {published}    Authors: {authors or '-'}", margin_x, y, max_w, SMALL[0], SMALL[1], leading=12)
        y = _draw_wrapped_text(c, f"Categories: {cats or '-'}", margin_x, y, max_w, SMALL[0], SMALL[1], leading=12)

        reasons = getattr(p, "spoj_fit_reasons", []) or []
        if reasons:
            y = _draw_wrapped_text(c, "Reasons:", margin_x, y, max_w, SMALL[0], SMALL[1], leading=12)
            for r in reasons[:3]:
                y = _draw_wrapped_text(c, f"- {r}", margin_x + 0.4 * cm, y, max_w - 0.4 * cm, SMALL[0], SMALL[1], leading=12)

        # SPOJ pitch angle (deterministic)
        pitch_one, pitch_bullets = build_spoj_pitch(p)
        y = _draw_wrapped_text(c, "SPOJ angle:", margin_x, y, max_w, SMALL[0], SMALL[1], leading=12)
        y = _draw_wrapped_text(c, pitch_one, margin_x + 0.4 * cm, y, max_w - 0.4 * cm, SMALL[0], SMALL[1], leading=12, max_lines=3)
        for b in pitch_bullets:
            y = _draw_wrapped_text(c, f"- {b}", margin_x + 0.8 * cm, y, max_w - 0.8 * cm, SMALL[0], SMALL[1], leading=12, max_lines=2)
        y -= 0.2 * cm

        # LinkedIn search (auto)
        li = getattr(p, "linkedin_search_url", "") or ""
        if li:
            c.setFont(*SMALL)
            c.drawString(margin_x, y, "LinkedIn search:")
            link_x = margin_x + 2.6 * cm
            c.drawString(link_x, y, li)
            try:
                c.linkURL(li, (link_x, y - 2, link_x + max_w, y + 10), relative=0)
            except Exception:
                pass
            y -= 0.6 * cm

        url = p.url or ""
        if url:
            c.setFont(*SMALL)
            c.drawString(margin_x, y, "Link:")
            link_x = margin_x + 1.0 * cm
            c.drawString(link_x, y, url)
            try:
                c.linkURL(url, (link_x, y - 2, link_x + max_w, y + 10), relative=0)
            except Exception:
                pass
            y -= 0.6 * cm

        abstract = (p.abstract or "").strip()
        if abstract:
            abstract_trim = abstract[:700] + ("…" if len(abstract) > 700 else "")
            y = _draw_wrapped_text(c, abstract_trim, margin_x, y, max_w, P[0], P[1], leading=12, max_lines=8)

        y -= 0.8 * cm

    c.save()
    return out_path

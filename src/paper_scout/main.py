from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from paper_scout.dedupe import dedupe_papers
from paper_scout.export_csv import write_csv
from paper_scout.scoring import score_spoj_fit
from paper_scout.sources.arxiv_api import fetch_arxiv_api


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="AI paper scout (MVP)")
    p.add_argument("--months", type=int, default=6, help="How many months back to include (default: 6)")
    p.add_argument("--page-size", type=int, default=200, help="arXiv API page size (default: 200)")
    p.add_argument("--max-total", type=int, default=5000, help="Hard cap on total papers fetched (default: 5000)")
    p.add_argument(
        "--categories",
        type=str,
        default="cs.CL,cs.AI,cs.LG",
        help="Comma-separated arXiv categories",
    )
    p.add_argument("--polite-sleep", type=float, default=3.0, help="Sleep between API pages (default: 3.0s)")
    p.add_argument("--pdf", action="store_true", help="Generate PDF report (top N).")
    p.add_argument("--top-n", type=int, default=30, help="Number of top papers to include in PDF.")
    return p.parse_args()


def ensure_out_dir() -> Path:
    out_dir = Path("out")
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def main() -> int:
    args = parse_args()
    categories: List[str] = [c.strip() for c in args.categories.split(",") if c.strip()]

    papers = fetch_arxiv_api(
        categories=categories,
        months=args.months,
        page_size=args.page_size,
        max_total=args.max_total,
        polite_sleep_seconds=args.polite_sleep,
    )
    papers = dedupe_papers(papers)

    # SPOJ fit scoring
    for p in papers:
        fr = score_spoj_fit(p)
        p.spoj_fit_score = fr.score
        p.spoj_fit_tags = fr.tags
        p.spoj_fit_reasons = fr.reasons
        p.spoj_benchmarks = fr.benchmarks

    out_dir = ensure_out_dir()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    json_path = out_dir / f"raw_papers_{today}.json"
    csv_path = out_dir / f"raw_papers_{today}.csv"

    json_path.write_text(
        json.dumps([p.model_dump(mode="json") for p in papers], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_csv(csv_path, papers)

    if args.pdf:
        from paper_scout.pdf_report import generate_pdf, ReportMeta

        papers_sorted = sorted(papers, key=lambda x: (getattr(x, "spoj_fit_score", 0) or 0), reverse=True)
        meta = ReportMeta(
            generated_at=datetime.now(timezone.utc),
            window_label=f"last {args.months} months",
            categories=args.categories,
            total_papers=len(papers),
            top_n=args.top_n,
        )
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
        pdf_path = out_dir / f"report_{stamp}.pdf"
        generate_pdf(pdf_path, papers_sorted, meta)
        print(f"Saved PDF report: {pdf_path}")

    print(f"Fetched {len(papers)} unique papers (last {args.months} months). Saved: {json_path} and {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

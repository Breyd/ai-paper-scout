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

    out_dir = ensure_out_dir()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    json_path = out_dir / f"raw_papers_{today}.json"
    csv_path = out_dir / f"raw_papers_{today}.csv"

    json_path.write_text(
        json.dumps([p.model_dump(mode="json") for p in papers], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_csv(csv_path, papers)

    print(f"Fetched {len(papers)} unique papers (last {args.months} months). Saved: {json_path} and {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

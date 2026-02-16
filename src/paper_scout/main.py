from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from paper_scout.dedupe import dedupe_papers
from paper_scout.export_csv import write_csv
from paper_scout.sources.arxiv import fetch_arxiv_rss


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Daily AI paper scout (MVP)")
    p.add_argument("--days", type=int, default=1)
    p.add_argument("--max-results", type=int, default=50)
    p.add_argument(
        "--categories",
        type=str,
        default="cs.CL,cs.AI,cs.LG",
        help="Comma-separated arXiv categories",
    )
    return p.parse_args()


def ensure_out_dir() -> Path:
    out_dir = Path("out")
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def main() -> int:
    args = parse_args()
    categories: List[str] = [c.strip() for c in args.categories.split(",") if c.strip()]

    papers = fetch_arxiv_rss(categories=categories, days=args.days, max_results_per_cat=args.max_results)
    papers = dedupe_papers(papers)

    out_dir = ensure_out_dir()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    json_path = out_dir / f"raw_papers_{today}.json"
    csv_path = out_dir / f"raw_papers_{today}.csv"

    json_path.write_text(
        json.dumps([p.model_dump(mode="json") for p in papers], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_csv(csv_path, papers)

    print(f"Fetched {len(papers)} unique papers. Saved: {json_path} and {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

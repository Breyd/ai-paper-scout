from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple

from paper_scout.models import Paper


@dataclass
class FitResult:
    score: int
    tags: List[str]
    reasons: List[str]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).lower().strip()


def score_spoj_fit(p: Paper) -> FitResult:
    """
    Heuristic scoring based on title+abstract. 0-100.
    Output is stable/deterministic (good for pipeline).
    """
    text = _norm(p.title + " " + (p.abstract or ""))

    # Buckets: tags -> (regex patterns, points, reason)
    rules: List[Tuple[str, List[str], int, str]] = [
        ("codegen", [r"\bcode generation\b", r"\bcodegen\b", r"\bprogram synthesis\b", r"\btext-to-code\b"], 25,
         "Focuses on code generation / program synthesis."),
        ("reasoning", [r"\breasoning\b", r"\bchain[- ]of[- ]thought\b", r"\bplanning\b", r"\bself[- ]consistency\b"], 15,
         "Emphasizes reasoning/planning abilities."),
        ("execution_feedback", [r"\bexecution\b", r"\bruntime\b", r"\bcompiler\b", r"\bjudge\b", r"\btest case\b", r"\bunit test\b"], 25,
         "Uses execution/test feedback signals (fits submission+verdict data)."),
        ("verification", [r"\bverification\b", r"\bformal\b", r"\bcorrectness\b", r"\bprove\b", r"\bstatic analysis\b"], 15,
         "Relates to correctness/verification (aligns with accepted vs wrong-answer traces)."),
        ("rl", [r"\breinforcement learning\b", r"\brl\b", r"\bpolicy\b", r"\breward\b"], 10,
         "Includes RL-style optimization (can benefit from high-signal verdict labels)."),
        ("benchmark_eval", [r"\bbenchmark\b", r"\bevaluation\b", r"\bmetrics\b", r"\bleaderboard\b"], 10,
         "Contains benchmarking/evaluation framing (SPOJ can be a training/eval source)."),
        ("multilingual_code", [r"\bmultiple languages\b", r"\bmultilingual\b", r"\bpython\b|\bc\+\+\b|\bjava\b|\brust\b|\bgo\b"], 5,
         "Touches multiple programming languages (SPOJ is multi-language)."),
        ("algorithms", [r"\bdynamic programming\b", r"\bgraph\b", r"\bshortest path\b", r"\bcombinatorics\b", r"\bdata structures\b"], 15,
         "Mentions classical algorithms topics (core SPOJ coverage)."),
    ]

    score = 0
    tags: List[str] = []
    reasons: List[str] = []

    for tag, patterns, pts, reason in rules:
        if any(re.search(pat, text) for pat in patterns):
            score += pts
            tags.append(tag)
            # keep reason list short & unique
            if reason not in reasons:
                reasons.append(reason)

    # Mild calibration / caps
    if score > 100:
        score = 100

    # Ensure we always return 1-3 reasons (sales-friendly)
    if not reasons:
        reasons = ["Potential relevance to code/reasoning improvements; needs manual review."]
    else:
        reasons = reasons[:3]

    return FitResult(score=score, tags=tags[:6], reasons=reasons)

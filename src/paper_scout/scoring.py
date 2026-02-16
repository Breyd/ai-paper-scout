from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from paper_scout.benchmarks import extract_benchmarks
from paper_scout.models import Paper


@dataclass
class FitResult:
    score: int
    tags: List[str]
    reasons: List[str]
    benchmarks: List[str]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).lower().strip()


def _hit(text: str, patterns: List[str]) -> bool:
    return any(re.search(p, text) for p in patterns)


CORE_CODE_PATTERNS = [
    r"\bprogram synthesis\b",
    r"\bcode generation\b",
    r"\bcode repair\b",
    r"\bprogram repair\b",
    r"\bbug[- ]fix(ing)?\b",
    r"\bpatch\b",
    r"\bdiff\b",
    r"\bsource code\b",
    r"\bcompiler\b",
    r"\bcompile(r|d|s)?\b",
    r"\bruntime\b",
    r"\bexecution trace(s)?\b",
    r"\bunit test(s)?\b",
    r"\btest case(s)?\b",
    r"\bfailing test(s)?\b",
    r"\bwrong answer\b",
    r"\bruntime error\b",
    r"\btime limit\b",
    r"\bmemory limit\b",
    r"\bonline judge\b",
    r"\bcompetitive programming\b",
]

REPO_SE_PATTERNS = [
    r"\bgit(hub)?\b",
    r"\brepository\b",
    r"\brepo[- ]level\b",
    r"\bpull request(s)?\b",
    r"\bissue(s)?\b",
    r"\bcommit(s)?\b",
    r"\bci\b",
    r"\bcontinuous integration\b",
    r"\bbuild\b",
    r"\btest suite\b",
    r"\bregression\b",
    r"\bstatic analysis\b",
    r"\blint(ing)?\b",
]

TOOL_AGENT_PATTERNS = [
    r"\btool use\b",
    r"\bfunction calling\b",
    r"\bagents?\b",
    r"\bweb browsing\b",
    r"\bcode interpreter\b",
]

VERIFICATION_PATTERNS = [
    r"\bverification\b",
    r"\bformal\b",
    r"\bcorrectness\b",
    r"\btype system\b",
    r"\bsoundness\b",
]

MULTILANG_PATTERNS = [r"\bpython\b|\bc\+\+\b|\bjava\b|\brust\b|\bgo\b|\bjavascript\b|\bc#\b"]


def score_spoj_fit(p: Paper) -> FitResult:
    text = _norm(p.title + " " + (p.abstract or ""))

    bench_hits = extract_benchmarks(text)
    bench_names = [h.name for h in bench_hits]
    bench_score = sum(h.weight for h in bench_hits[:3])  # cap to top-3

    core_code = _hit(text, CORE_CODE_PATTERNS)
    repo_se = _hit(text, REPO_SE_PATTERNS)
    tool_agent = _hit(text, TOOL_AGENT_PATTERNS)
    verification = _hit(text, VERIFICATION_PATTERNS)
    multilang = _hit(text, MULTILANG_PATTERNS)

    score = 0
    tags: List[str] = []
    reasons: List[str] = []

    # 1) Benchmarks (dominant if present)
    if bench_hits:
        score += min(60, bench_score)
        tags.append("benchmarks")
        reasons.append(f"Mentions benchmarks: {', '.join(bench_names[:3])}.")

    # 2) Core code/execution/verdict signals
    if core_code:
        score += 35
        tags.append("core_code")
        reasons.append("Contains code/execution/test/verdict-like signals (compile/runtime/tests/errors).")

    # 3) Repo / software engineering signals
    if repo_se:
        score += 25
        tags.append("repo_se")
        reasons.append("Mentions repository/PR/CI/tests signals (similar to repo-level coding tasks).")

    # 4) Verification/correctness (bonus)
    if verification:
        score += 10
        tags.append("verification")

    # 5) Tool/agent use (bonus)
    if tool_agent:
        score += 8
        tags.append("agents_tools")

    # 6) Multilanguage (minor bonus)
    if multilang:
        score += 5
        tags.append("multilang")

    # Offdomain penalties
    if _hit(text, [r"\becg\b", r"\beeg\b", r"\bppg\b", r"\bclinical\b", r"\bclimate\b", r"\bprecipitation\b"]):
        score -= 25
        tags.append("offdomain")
    if _hit(text, [r"\buav\b", r"\bairspace\b", r"\bpreflight\b", r"\bgrasp(ing)?\b", r"\bmanipulation\b"]):
        score -= 15
        tags.append("offdomain")

    # Gate: if none of {bench, core_code, repo_se} then hard cap
    if (not bench_hits) and (not core_code) and (not repo_se):
        score = min(score, 20)

    score = max(0, min(100, score))

    # Reasons: max 3, but make sure at least 1
    reasons = reasons[:3] if reasons else ["Low direct relevance signals found; needs manual review."]

    # unique tags
    tags_u: List[str] = []
    for t in tags:
        if t not in tags_u:
            tags_u.append(t)

    return FitResult(score=score, tags=tags_u[:8], reasons=reasons, benchmarks=bench_names[:10])

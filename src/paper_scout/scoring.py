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


def _hit(text: str, patterns: List[str]) -> bool:
    return any(re.search(p, text) for p in patterns)


# Strong signals that SPOJ-like submission+verdict+code data is directly useful
CORE_CODE_PATTERNS = [
    r"\bcode generation\b",
    r"\bprogram synthesis\b",
    r"\btext-to-code\b",
    r"\bsource code\b",
    r"\bcompiler\b",
    r"\bcompile(r|d|s)?\b",
    r"\bruntime\b",
    r"\btime limit\b",
    r"\bmemory limit\b",
    r"\bwrong answer\b",
    r"\bruntime error\b",
    r"\bunit test(s)?\b",
    r"\btest case(s)?\b",
    r"\bonline judge\b",
    r"\bcompetitive programming\b",
    r"\bhumaneval\b",
    r"\bmbpp\b",
    r"\bswe-bench\b",
    r"\bcodeforces\b",
    r"\bleetcode\b",
    r"\bkernel optimization\b",
    r"\bcuda\b",
]

# Medium signals: could be relevant but often creates false positives alone
SOFT_REASONING_PATTERNS = [
    r"\breasoning\b",
    r"\bplanning\b",
    r"\bself[- ]consistency\b",
    r"\breflection\b",
    r"\bverifier\b",
]

ALGO_PATTERNS = [
    r"\bdynamic programming\b",
    r"\bgraph(s)?\b",
    r"\bshortest path\b",
    r"\bminimum spanning tree\b",
    r"\bflow\b",
    r"\bmatching\b",
    r"\bcombinatorics\b",
    r"\bdata structure(s)?\b",
    r"\bsegment tree\b",
    r"\bfenwick\b",
]


def score_spoj_fit(p: Paper) -> FitResult:
    text = _norm(p.title + " " + (p.abstract or ""))

    core_code_signal = _hit(text, CORE_CODE_PATTERNS)

    positive_rules: List[Tuple[str, List[str], int, str]] = [
        ("code_benchmarks", [r"\bhumaneval\b", r"\bmbpp\b", r"\bswe-bench\b", r"\bcodeforces\b", r"\bleetcode\b",
                             r"\bcompetitive programming\b", r"\bonline judge\b"], 35,
         "References code benchmarks / online-judge evaluation."),
        ("execution_feedback", [r"\bruntime\b", r"\bcompiler\b", r"\bcompile(r|d|s)?\b", r"\bjudge\b",
                               r"\bunit test(s)?\b", r"\btest case(s)?\b",
                               r"\bwrong answer\b", r"\bruntime error\b", r"\btime limit\b", r"\bmemory limit\b"], 40,
         "Uses execution/test feedback signals (matches submissions + verdicts)."),
        ("codegen", [r"\bcode generation\b", r"\bcodegen\b", r"\bprogram synthesis\b", r"\btext-to-code\b"], 35,
         "Focuses on code generation / program synthesis."),
        ("verification", [r"\bformal\b", r"\bverification\b", r"\bcorrectness\b", r"\bprove\b",
                          r"\bstatic analysis\b", r"\btype system\b", r"\bsoundness\b"], 20,
         "Centered on correctness/verification (fits accepted vs failing traces)."),
        ("algorithms", ALGO_PATTERNS + [r"\balgorithm(s)?\b"], 20,
         "Mentions classical algorithms/data structures (core SPOJ coverage)."),
        ("code_tasks", [r"\bprogram(ming)?\b", r"\bsource code\b", r"\bdebug(ging)?\b", r"\bpatch\b", r"\bbug\b",
                        r"\bcuda\b", r"\bkernel\b"], 15,
         "Explicitly about programming/code tasks."),
        ("reasoning", SOFT_REASONING_PATTERNS, 10,
         "Emphasizes reasoning/planning (secondary but useful for SPOJ)."),
        ("multilang", [r"\bpython\b|\bc\+\+\b|\bjava\b|\brust\b|\bgo\b|\bjavascript\b"], 5,
         "Touches multiple programming languages (SPOJ is multi-language)."),
    ]

    # Penalize “application domains” that frequently create false positives,
    # unless there is a core code signal (then we keep it).
    negative_rules: List[Tuple[str, List[str], int, str]] = [
        ("aerospace_robotics", [r"\buav\b", r"\bairspace\b", r"\bflight\b", r"\bpreflight\b",
                               r"\brobot\b", r"\bmanipulation\b", r"\bgrasp(ing)?\b", r"\btrajectory\b", r"\bcontrol\b"], -25,
         "Primarily robotics/aerospace planning; often not code-judge driven."),
        ("info_extraction", [r"\btriplet extraction\b", r"\binformation extraction\b", r"\bfinancial report\b"], -15,
         "Primarily NLP extraction; less aligned with code + verdict training."),
        ("climate_geo", [r"\bclimate\b", r"\bprecipitation\b", r"\bhydro\b", r"\briver basin\b", r"\bcmip\b"], -35,
         "Climate/earth-science focus; unlikely to need SPOJ-like data."),
        ("medical_signals", [r"\becg\b", r"\beeg\b"\bppg\b", r"\bclinical\b", r"\bpatient\b", r"\bmedical\b"], -35,
         "Medical/signal processing focus; unlikely to need SPOJ-like data."),
        ("vision_video", [r"\bvideo\b", r"\bcodec\b", r"\bkeyframe\b", r"\bmotion vectors\b", r"\bimage encoder\b"], -20,
         "Video/vision infrastructure; weak link to code-judge training."),
        ("socio_hci", [r"\bloneliness\b", r"\battachment\b", r"\bcompanion\b", r"\bsurvey\b"], -20,
         "HCI/behavioral focus; not code dataset driven."),
    ]

    score = 0
    tags: List[str] = []
    reasons_pos: List[str] = []
    reasons_neg: List[str] = []

    for tag, patterns, pts, reason in positive_rules:
        if _hit(text, patterns):
            score += pts
            tags.append(tag)
            reasons_pos.append(reason)

    # Negatives apply strongly only when there's no core code signal
    for tag, patterns, pts, reason in negative_rules:
        if _hit(text, patterns):
            if core_code_signal:
                # soften penalty if core code signal exists
                score += int(pts / 2)
            else:
                score += pts
            tags.append(tag)
            reasons_neg.append(reason)

    # Gate: without core code signal, don't allow high scores
    if not core_code_signal:
        score = min(score, 35)

    score = max(0, min(100, score))

    reasons: List[str] = []
    for r in reasons_pos:
        if r not in reasons:
            reasons.append(r)
        if len(reasons) >= 3:
            break

    if not reasons:
        if reasons_neg:
            reasons = [reasons_neg[0], "Low direct relevance to code-judge training; likely not SPOJ-driven."]
        else:
            reasons = ["Low direct relevance signals found; needs manual review."]

    tags_unique: List[str] = []
    for t in tags:
        if t not in tags_unique:
            tags_unique.append(t)

    return FitResult(score=score, tags=tags_unique[:8], reasons=reasons)

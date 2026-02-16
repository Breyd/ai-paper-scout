from __future__ import annotations

from typing import List, Tuple

from paper_scout.models import Paper


def build_spoj_pitch(p: Paper) -> Tuple[str, List[str]]:
    """
    Returns: (one-line pitch, bullet reasons)
    Deterministic, no LLM.
    """
    tags = set((getattr(p, "spoj_fit_tags", []) or []))
    benches = set((getattr(p, "spoj_benchmarks", []) or []))

    bullets: List[str] = []

    if "SWE-bench" in benches or "RepoBench" in benches:
        bullets.append("Repo-level code editing + real-world patching signals match SPOJ-style iterative attempts + verdicts.")
    if {"HumanEval", "MBPP", "EvalPlus"} & benches:
        bullets.append("Strong code-gen evaluation focus → SPOJ adds scale + multi-language + harder long-tail problems.")
    if "APPS" in benches or "Codeforces" in benches or "CodeContests" in benches:
        bullets.append("Competitive-programming / algorithmic eval → direct overlap with SPOJ problem distribution.")
    if "verition" in tags:
        bullets.append("Correctness/verification angle → SPOJ provides accepted vs failing traces and error modes.")
    if "core_code" in tags:
        bullets.append("Execution/test/verdict signals → SPOJ provides structured feedback labels at massive scale.")
    if "agents_tools" in tags:
        bullets.append("Agentic coding/tool use → SPOJ supports verifiable tool-loop training via judge feedback.")

    # one-liner: choose strongest angle
    if "SWE-bench" in benches or "RepoBench" in benches:
        one = "SPOJ can complement your repo-level coding evaluations with large-scale judged submissions (multi-language, verdict-labeled, iterative attempts)."
    elif {"HumanEval", "MBPP", "EvalPlus"} & benches:
        one = "SPOJ can extend code-generation evaluation/training with 35k algorithmic tasks and 30M verdict-labeled submissions across languages."
    elif "APPS" in benches or "Codeforces" in benches or "CodeContests" in benches:
        one = "SPOJ is a direct fit: competirogramming style problems + millions of submissions with judge verdicts and error modes."
    elif "core_code" in tags or "verification" in tags:
        one = "SPOJ provides scalable, verifiable training/eval data: judged code submissions with timestamps, languages, and failure modes."
    else:
        one = "Potential SPOJ fit: large-scale code+verdict data may complement your evaluation/training pipeline."

    return one, bullets[:3]

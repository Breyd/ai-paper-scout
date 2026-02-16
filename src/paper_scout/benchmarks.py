from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class BenchmarkHit:
    name: str
    weight: int
    evidence: str


# Canonical name -> (weight, regex patterns)
BENCHMARKS: Dict[str, Tuple[int, List[str]]] = {
    # Code / SWE
    "SWE-bench": (45, [r"\bswe[- ]bench\b", r"\bswebench\b"]),
    "HumanEval": (40, [r"\bhuman[- ]?eval\b"]),
    "MBPP": (35, [r"\bmbpp\b"]),
    "Codeforces": (35, [r"\bcodeforces\b"]),
    "LeetCode": (25, [r"\bleet ?code\b"]),
    "APPS": (25, [r"\bapps\b( dataset)?"]),
    "DS-1000": (25, [r"\bds[- ]?1000\b"]),
    "EvalPlus": (20, [r"\bevalplus\b", r"\beval\+\b"]),
    "LiveCodeBench": (30, [r"\blivecodebench\b", r"\blive code bench\b"]),
    "CodeContests": (25, [r"\bcodecontests\b", r"\bcode contests\b"]),
    "CruxEval": (20, [r"\bcruxeval\b"]),
    "RepoBench": (25, [r"\brepobench\b", r"\brepo[- ]bench\b"]),
    "CodeSearchNet": (15, [r"\bcodesearchnet\b", r"\bcode search net\b"]),

    # Agent / tool-use / general eval signals
    "MMLU": (15, [r"\bmmlu\b"]),
    "MMMU": (15, [r"\bmmmu\b"]),
    "GSM8K": (10, [r"\bgsm8k\b"]),
    "ARC": (8, [r"\barc\b(?![- ]?length)"]),
    "HellaSwag": (8, [r"\bhellaswag\b"]),
    "TruthfulQA": (8, [r"\btruthfulqa\b"]),
    "Big-Bench": (8, [r"\bbig[- ]bench\b", r"\bbbh\b"]),
}



def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).lower().strip()


def extract_benchmarks(text: str) -> List[BenchmarkHit]:
    t = _norm(text)
    hits: List[BenchmarkHit] = []

    for name, (w, patterns) in BENCHMARKS.items():
        for pat in patterns:
            m = re.search(pat, t)
            if m:
                # evidence: small snippet around match
                start = max(0, m.start() - 30)
                end = min(len(t), m.end() + 30)
                evidence = t[start:end]
                hits.append(BenchmarkHit(name=name, weight=w, evidence=evidence))
                break

    # sort: strongest first
    hits.sort(key=lambda h: h.weight, reverse=True)
    return hits

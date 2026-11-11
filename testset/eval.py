"""Baseline eval over testset/messages.csv (Phase 1.8).

Runs the real pipeline in-process (rules, then Gemini, then fuse) and reports accuracy per language and split.
A message is predicted 'scam' when the final risk is medium or high. This is a baseline, not a target.

Usage (from the repo root, with GEMINI_API_KEY in .env):
    backend/.venv/Scripts/python testset/eval.py                 # rules + Gemini
    backend/.venv/Scripts/python testset/eval.py --no-llm        # rules only (quick mode)
    backend/.venv/Scripts/python testset/eval.py --write         # also write testset/baseline.md
"""
import argparse
import asyncio
import csv
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app import llm  # noqa: E402
from app.fuse import fuse  # noqa: E402
from app.rules import evaluate  # noqa: E402

MESSAGES = ROOT / "testset" / "messages.csv"
BASELINE = ROOT / "testset" / "baseline.md"
DEVA_RE = re.compile(r"[\u0900-\u097f]")
LETTER_RE = re.compile(r"[\u0900-\u097fA-Za-z]")
DEVA_SHARE_MIN = 0.5
REQUEST_GAP_S = 4.0


def deva_share(text: str) -> float:
    letters = len(LETTER_RE.findall(text))
    return len(DEVA_RE.findall(text)) / letters if letters else 0.0


async def run(use_llm: bool) -> tuple[dict[str, list[bool]], list[str], list[float], list[str]]:
    buckets: dict[str, list[bool]] = defaultdict(list)
    misses, latencies, mr_shares = [], [], []
    rows = list(csv.DictReader(MESSAGES.open(encoding="utf-8")))
    for row in rows:
        rule = evaluate(row["text"])
        start = time.perf_counter()
        answer = None
        if use_llm:
            hints = [f"{c}:{g}" for c, g in rule.matched]
            answer = await llm.analyze(row["text"], row["lang"], hints)
            latencies.append(time.perf_counter() - start)
            await asyncio.sleep(REQUEST_GAP_S)
        out = fuse(rule, answer, row["lang"])
        ok = (out.risk != "low") == (row["label"] == "scam")
        for key in ("overall", row["lang"], row["split"]):
            buckets[key].append(ok)
        if out.mode == "full" and row["lang"] == "mr":
            mr_shares.append(deva_share(" ".join([out.scam_type, *out.reasons, *out.next_steps])))
        if not ok:
            misses.append(f"{row['id']} label={row['label']} risk={out.risk} mode={out.mode}")
    return buckets, misses, latencies, [f"{s:.0%}" for s in mr_shares]


def render(buckets, misses, latencies, shares, use_llm: bool) -> str:
    lines = [f"# Baseline ({'rules + Gemini' if use_llm else 'rules only'})", "", "| Slice | Correct | Accuracy |", "| --- | --- | --- |"]
    for key in ("overall", "mr", "hi", "en", "dev", "holdout"):
        oks = buckets[key]
        lines.append(f"| {key} | {sum(oks)}/{len(oks)} | {sum(oks) / len(oks):.0%} |")
    if latencies:
        ordered = sorted(latencies)
        lines += ["", f"Gemini stage latency: p50 {ordered[len(ordered) // 2]:.1f}s, max {ordered[-1]:.1f}s"]
    if shares:
        lines += ["", f"Marathi output Devanagari share (full mode, min {DEVA_SHARE_MIN:.0%}): {', '.join(shares)}"]
    lines += ["", "Misses:", *(f"- {m}" for m in misses or ["none"])]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-llm", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = render(*asyncio.run(run(not args.no_llm)), not args.no_llm)
    print(report)
    if args.write:
        BASELINE.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()

"""Rules-only baseline over testset/messages.csv. Prints accuracy per language and split.

A message is predicted 'scam' when the rule floor is medium or high. This is a baseline, not a target.
Run from backend/: python -m scripts.rules_baseline
"""
import csv
from collections import defaultdict
from pathlib import Path

from app.rules import evaluate

MESSAGES = Path(__file__).resolve().parents[2] / "testset" / "messages.csv"


def main() -> None:
    buckets: dict[str, list[bool]] = defaultdict(list)
    for row in csv.DictReader(MESSAGES.open(encoding="utf-8")):
        res = evaluate(row["text"])
        ok = (res.floor != "low") == (row["label"] == "scam")
        for key in ("all", row["lang"], row["split"]):
            buckets[key].append(ok)
        if not ok:
            print(f"MISS {row['id']:6} label={row['label']:7} floor={res.floor:6} "
                  f"top={res.top_category} matched={res.matched}")
    for key, oks in sorted(buckets.items()):
        print(f"{key:8} {sum(oks)}/{len(oks)} = {sum(oks) / len(oks):.0%}")


if __name__ == "__main__":
    main()


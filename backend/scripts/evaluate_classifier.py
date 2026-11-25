"""Evaluation script for Sajag V2: rules baseline + optional ONNX classifier & fusion comparison.

Usage (from repo root):
    backend/.venv/Scripts/python.exe backend/scripts/evaluate_classifier.py
    backend/.venv/Scripts/python.exe backend/scripts/evaluate_classifier.py --with-llm
"""
import argparse
import asyncio
import csv
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import numpy as np  # noqa: E402
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score  # noqa: E402

from app import llm  # noqa: E402
from app.classifier import load_classifier  # noqa: E402
from app.fuse import fuse  # noqa: E402
from app.rules import evaluate  # noqa: E402

TESTSET_CSV = REPO_ROOT / "testset" / "messages.csv"
ML_TEST_CSV = BACKEND_DIR / "data" / "ml_dataset" / "test.csv"
METADATA_JSON = BACKEND_DIR / "data" / "ml_dataset" / "metadata.json"


def _eval_testset_config(rows: list[dict], classifier, use_ml: bool, use_rules: bool, use_llm: bool) -> dict:
    """Evaluate a signal configuration on the 40-message testset."""
    buckets: dict[str, list[bool]] = defaultdict(list)
    false_alarms: list[str] = []
    misses: list[str] = []
    latencies_ms: list[float] = []

    async def _run():
        for row in rows:
            t0 = time.perf_counter()
            rule = evaluate(row["text"]) if use_rules else evaluate("")
            ml = classifier.predict(row["text"]) if (use_ml and classifier is not None) else None
            llm_out = None
            if use_llm:
                hints = [f"{c}:{g}" for c, g in rule.matched]
                llm_out = await llm.analyze(row["text"], row["lang"], hints)
                await asyncio.sleep(4.0)

            if use_rules or use_llm:
                out = fuse(rule, llm_out, row["lang"], ml=ml)
                pred_scam = out.risk != "low"
                risk_label = out.risk
            else:
                # ML-only mode
                pred_scam = ml.is_scam if ml is not None else False
                risk_label = ml.risk if ml is not None else "low"

            latencies_ms.append((time.perf_counter() - t0) * 1000.0)
            is_scam = row["label"] == "scam"
            ok = pred_scam == is_scam
            for key in ("overall", row["lang"], row["split"]):
                buckets[key].append(ok)
            if not ok:
                misses.append(f"{row['id']} (label={row['label']}, pred_risk={risk_label})")
                if not is_scam and pred_scam:
                    false_alarms.append(row["id"])

    asyncio.run(_run())
    ordered_lat = sorted(latencies_ms)
    p95 = ordered_lat[min(len(ordered_lat) - 1, int(0.95 * len(ordered_lat)))] if ordered_lat else 0.0
    return {
        "overall_correct": sum(buckets["overall"]),
        "overall_total": len(buckets["overall"]),
        "accuracy": round(sum(buckets["overall"]) / len(buckets["overall"]), 4),
        "per_lang": {
            lang: f"{sum(buckets[lang])}/{len(buckets[lang])}"
            for lang in ("mr", "hi", "en")
        },
        "false_alarms": false_alarms,
        "misses": misses,
        "p95_ms": round(p95, 1),
    }


def _eval_ml_test_split(classifier) -> dict:
    """Evaluate ONNX classifier on backend/data/ml_dataset/test.csv."""
    rows = list(csv.DictReader(ML_TEST_CSV.open(encoding="utf-8")))
    texts = [r["text"] for r in rows]
    y_true = np.array([int(r["label"]) for r in rows])

    t0 = time.perf_counter()
    probs = classifier.predict_proba_batch(texts)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    y_pred = (probs[:, 1] > 0.5).astype(int)

    per_lang = {}
    for lang in ("English", "Hindi", "Hinglish", "Marathi"):
        mask = np.array([r["language"] == lang for r in rows])
        per_lang[lang] = {
            "samples": int(mask.sum()),
            "accuracy": round(float(accuracy_score(y_true[mask], y_pred[mask])), 4),
            "f1": round(float(f1_score(y_true[mask], y_pred[mask], pos_label=1, zero_division=0)), 4),
        }

    failures = [
        {
            "language": rows[i]["language"],
            "actual": int(y_true[i]),
            "pred": int(y_pred[i]),
            "scam_prob": round(float(probs[i, 1]), 3),
            "text": rows[i]["text"][:100],
        }
        for i in range(len(rows))
        if y_true[i] != y_pred[i]
    ][:10]

    return {
        "samples": len(rows),
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "f1": round(float(f1_score(y_true, y_pred, pos_label=1)), 4),
        "precision": round(float(precision_score(y_true, y_pred, pos_label=1, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, pos_label=1, zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
        "per_language": per_lang,
        "batch_latency_ms": round(elapsed_ms, 1),
        "sample_failures": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-llm", action="store_true", help="Also run Gemini LLM configs (needs API key).")
    parser.add_argument("--json-out", type=Path, default=None, help="Optional JSON output path.")
    args = parser.parse_args()

    testset_rows = list(csv.DictReader(TESTSET_CSV.open(encoding="utf-8")))
    classifier = load_classifier(enabled=True)

    results = {
        "ml_model_status": "loaded" if classifier is not None else "unavailable (pending Phase C ONNX model)",
        "dataset_metadata": json.loads(METADATA_JSON.read_text(encoding="utf-8")) if METADATA_JSON.exists() else {},
        "testset_40": {
            "rules_only": _eval_testset_config(testset_rows, None, use_ml=False, use_rules=True, use_llm=False),
        },
        "ml_test_split": None,
    }

    if args.with_llm:
        results["testset_40"]["rules_plus_llm"] = _eval_testset_config(
            testset_rows, None, use_ml=False, use_rules=True, use_llm=True
        )

    if classifier is not None:
        results["testset_40"]["ml_only"] = _eval_testset_config(
            testset_rows, classifier, use_ml=True, use_rules=False, use_llm=False
        )
        results["testset_40"]["rules_plus_ml"] = _eval_testset_config(
            testset_rows, classifier, use_ml=True, use_rules=True, use_llm=False
        )
        if args.with_llm:
            results["testset_40"]["rules_plus_ml_plus_llm"] = _eval_testset_config(
                testset_rows, classifier, use_ml=True, use_rules=True, use_llm=True
            )
        if ML_TEST_CSV.exists():
            results["ml_test_split"] = _eval_ml_test_split(classifier)

    print(json.dumps(results, indent=2, ensure_ascii=False))
    if args.json_out:
        args.json_out.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

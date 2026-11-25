#!/usr/bin/env python3
"""
Sajag ML Dataset Preparation Pipeline

Merges, deduplicates, masks entities, quarantines testset messages,
and produces stratified train/val/test splits for MuRIL fine-tuning.

Usage:
    cd SevaInnoHackathon
    python backend/scripts/prepare_dataset.py

Output:
    backend/data/ml_dataset/{train,val,test}.csv
    backend/data/ml_dataset/metadata.json
"""

import csv
import json
import random
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (relative to repo root)
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.normalize import PHONE_RE, URL_RE, normalize_text, preprocess_for_ml  # noqa: E402

DATASETS_DIR = REPO_ROOT / "datasets"
TESTSET_PATH = REPO_ROOT / "testset" / "messages.csv"
OUTPUT_DIR = REPO_ROOT / "backend" / "data" / "ml_dataset"

D1_PATH = DATASETS_DIR / "indian_call_scams_hinglish_sample.csv"
D3_PATH = DATASETS_DIR / "multilingual_mr_hi_en.csv"
# D2 (marathi_scam_ham.csv) intentionally skipped — 100% subset of D3.

RANDOM_SEED = 42
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15
SCAM_RATIO_MIN_PCT = 45.0
SCAM_RATIO_MAX_PCT = 55.0
HAM_MAX_RATIO_TO_SCAM = 1.08
TEN_DIGIT_RE = re.compile(r"(?<!\d)\d{10}(?!\d)")

preprocess_text = preprocess_for_ml


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
def load_d1() -> list[dict]:
    """Load indian_call_scams_hinglish_sample.csv, normalize labels/language."""
    rows = []
    with open(D1_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({
                "text": r["text"].strip(),
                "label": int(r["label"]),           # already 0/1
                "language": "Hinglish",              # all D1 rows are Hinglish
            })
    return rows


def load_d3() -> list[dict]:
    """Load multilingual_mr_hi_en.csv, normalize labels."""
    rows = []
    with open(D3_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            label = 1 if r["label"] == "scam" else 0
            rows.append({
                "text": r["text"].strip(),
                "label": label,
                "language": r["language"],            # English/Hindi/Hinglish/Marathi
            })
    return rows


def load_testset_texts() -> set[str]:
    """Load quarantined testset texts (normalized for matching)."""
    texts = set()
    with open(TESTSET_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            texts.add(r["text"].strip())
    return texts


def balance_ham_per_language(rows: list[dict], seed: int) -> tuple[list[dict], int]:
    """Deterministically downsample ham proportionally per language if ham exceeds target ratio."""
    scam_rows = [r for r in rows if r["label"] == 1]
    ham_rows = [r for r in rows if r["label"] == 0]
    target_ham = round(len(scam_rows) * HAM_MAX_RATIO_TO_SCAM)
    if len(ham_rows) <= target_ham:
        return rows, 0

    rng = random.Random(seed)
    by_lang: dict[str, list[dict]] = {}
    for r in ham_rows:
        by_lang.setdefault(r["language"], []).append(r)

    kept_ham: list[dict] = []
    total_ham = len(ham_rows)
    langs = sorted(by_lang)
    for idx, lang in enumerate(langs):
        group = list(by_lang[lang])
        rng.shuffle(group)
        if idx == len(langs) - 1:
            quota = max(1, target_ham - len(kept_ham))
        else:
            quota = round(len(group) / total_ham * target_ham)
        kept_ham.extend(group[:quota])

    combined = scam_rows + kept_ham
    rng.shuffle(combined)
    return combined, len(ham_rows) - len(kept_ham)


def deduplicate(rows: list[dict], key: str = "text") -> list[dict]:
    """Remove duplicate rows by text field. Keeps first occurrence."""
    seen = set()
    unique = []
    for r in rows:
        t = r[key]
        if t not in seen:
            seen.add(t)
            unique.append(r)
    return unique


def stratified_split(rows: list[dict], seed: int) -> tuple[list, list, list]:
    """
    Stratified train/val/test split (70/15/15) on (language, label).

    Uses sklearn if available; falls back to manual stratification.
    """
    try:
        from sklearn.model_selection import train_test_split
    except ImportError:
        print("ERROR: scikit-learn required. Install: pip install scikit-learn")
        sys.exit(1)

    # Build stratification key
    strat_keys = [f"{r['language']}_{r['label']}" for r in rows]

    # Check minimum samples per stratum (need at least 2 for split)
    strat_counts = Counter(strat_keys)
    min_count = min(strat_counts.values())
    if min_count < 3:
        print(f"WARNING: Smallest stratum has {min_count} samples: "
              f"{[k for k, v in strat_counts.items() if v == min_count]}")
        print("  Falling back to non-stratified split for tiny strata.")

    # First split: 70% train, 30% temp
    indices = list(range(len(rows)))
    train_idx, temp_idx = train_test_split(
        indices, test_size=0.30, random_state=seed, stratify=strat_keys,
    )

    # Second split: 50/50 of temp → 15% val, 15% test
    temp_strat = [strat_keys[i] for i in temp_idx]
    val_idx, test_idx = train_test_split(
        temp_idx, test_size=0.50, random_state=seed, stratify=temp_strat,
    )

    train = [rows[i] for i in train_idx]
    val = [rows[i] for i in val_idx]
    test = [rows[i] for i in test_idx]
    return train, val, test


def save_csv(rows: list[dict], path: Path) -> None:
    """Save rows to CSV with columns: text, label, language."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label", "language"])
        writer.writeheader()
        writer.writerows(rows)


def save_metadata(meta: dict, path: Path) -> None:
    """Save metadata JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate_splits(train, val, test, testset_texts_norm, testset_texts_processed):
    """Run all Gate B validation assertions. Returns list of error strings."""
    errors = []
    expected_langs = {"English", "Hindi", "Hinglish", "Marathi"}
    expected_pairs = {(lang, lbl) for lang in expected_langs for lbl in (0, 1)}

    for name, split in [("train", train), ("val", val), ("test", test)]:
        # V-1: No empty texts
        empties = sum(1 for r in split if not r["text"].strip())
        if empties:
            errors.append(f"{name}: {empties} empty text fields")

        # V-2: All 4 languages x both labels present
        pairs = {(r["language"], r["label"]) for r in split}
        missing_pairs = expected_pairs - pairs
        if missing_pairs:
            errors.append(f"{name}: missing language/label strata {sorted(missing_pairs)}")

        # V-3: Label balance within 45-55%
        total = len(split)
        scam_count = sum(1 for r in split if r["label"] == 1)
        scam_pct = scam_count / total * 100 if total else 0
        if not (SCAM_RATIO_MIN_PCT <= scam_pct <= SCAM_RATIO_MAX_PCT):
            errors.append(
                f"{name}: scam ratio {scam_pct:.1f}% outside {SCAM_RATIO_MIN_PCT}-{SCAM_RATIO_MAX_PCT}% range"
            )

        # V-4: No testset leakage (raw-normalized or preprocessed)
        split_texts = {r["text"] for r in split}
        leaks_proc = split_texts & testset_texts_processed
        leaks_raw = {normalize_text(r["text"]) for r in split} & testset_texts_norm
        if leaks_proc or leaks_raw:
            errors.append(
                f"{name}: testset leakage detected (proc={len(leaks_proc)}, raw={len(leaks_raw)})"
            )

        # V-6: No raw URL or Indian mobile number remains (PHONE_RE matches [6-9]\d{9}; excludes Railway PNRs)
        raw_urls = sum(1 for r in split if URL_RE.search(r["text"]))
        raw_phones = sum(1 for r in split if PHONE_RE.search(r["text"]))
        if raw_urls:
            errors.append(f"{name}: {raw_urls} rows still contain raw URLs")
        if raw_phones:
            errors.append(f"{name}: {raw_phones} rows still contain Indian mobile numbers")

    # V-5: No text appears in multiple splits
    train_texts = {r["text"] for r in train}
    val_texts = {r["text"] for r in val}
    test_texts_set = {r["text"] for r in test}

    tv_overlap = train_texts & val_texts
    tt_overlap = train_texts & test_texts_set
    vt_overlap = val_texts & test_texts_set

    if tv_overlap:
        errors.append(f"train/val overlap: {len(tv_overlap)} texts")
    if tt_overlap:
        errors.append(f"train/test overlap: {len(tt_overlap)} texts")
    if vt_overlap:
        errors.append(f"val/test overlap: {len(vt_overlap)} texts")

    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("SAJAG ML DATASET PREPARATION")
    print("=" * 60)

    # Step 1: Load raw data
    print("\n[1/11] Loading datasets...")
    d1_raw = load_d1()
    d3_raw = load_d3()
    print(f"  D1 (Hinglish call scams): {len(d1_raw)} rows")
    print(f"  D3 (multilingual):        {len(d3_raw)} rows")
    print(f"  D2 (Marathi): SKIPPED (100% subset of D3)")

    # Step 2+3: Labels and languages already normalized in load functions
    print("\n[2/11] Labels normalized: D1 (0/1 int), D3 (ham/scam → 0/1)")
    print("[3/11] Languages normalized: D1 → 'Hinglish', D3 uses existing tags")

    # Step 4: Deduplicate D1
    print("\n[4/11] Deduplicating D1...")
    d1_dedup = deduplicate(d1_raw)
    print(f"  D1 before: {len(d1_raw)} → after: {len(d1_dedup)} "
          f"({len(d1_raw) - len(d1_dedup)} duplicates removed)")

    # Step 5: Merge
    print("\n[5/11] Merging D1 + D3...")
    merged = d3_raw + d1_dedup  # D3 first (larger, balanced), then D1
    print(f"  Merged pool: {len(merged)} rows")

    # Verify no cross-dataset overlap
    d1_texts = set(r["text"] for r in d1_dedup)
    d3_texts = set(r["text"] for r in d3_raw)
    cross_overlap = d1_texts & d3_texts
    print(f"  Cross-dataset overlap: {len(cross_overlap)} (should be 0)")
    assert len(cross_overlap) == 0, f"Unexpected D1/D3 overlap: {len(cross_overlap)}"

    # Step 6: Quarantine testset (raw-normalized)
    print("\n[6/11] Quarantining testset messages...")
    testset_texts_raw = load_testset_texts()
    testset_texts_norm = {normalize_text(t) for t in testset_texts_raw}
    print(f"  Testset messages: {len(testset_texts_raw)}")

    before_quarantine = len(merged)
    merged = [
        r for r in merged
        if r["text"] not in testset_texts_raw and normalize_text(r["text"]) not in testset_texts_norm
    ]
    removed = before_quarantine - len(merged)
    print(f"  Removed from pool (raw): {removed} rows")
    print(f"  Pool after quarantine: {len(merged)} rows")

    # Step 7: Text preprocessing (NFC + masking via app.normalize.preprocess_for_ml)
    print("\n[7/11] Preprocessing text (NFC, URL masking, phone masking)...")

    urls_masked = 0
    phones_masked = 0
    for r in merged:
        original = r["text"]
        processed = preprocess_text(original)
        if "[URL]" in processed and "[URL]" not in original.lower():
            urls_masked += 1
        if "[PHONE]" in processed and "[PHONE]" not in original.lower():
            phones_masked += 1
        r["text"] = processed
    print(f"  URLs masked:   {urls_masked} texts")
    print(f"  Phones masked: {phones_masked} texts")

    # Also quarantine preprocessed testset texts and deduplicate
    testset_texts_processed = {preprocess_text(t) for t in testset_texts_raw}
    before_proc_quarantine = len(merged)
    merged = [r for r in merged if r["text"] not in testset_texts_processed]
    removed_proc = before_proc_quarantine - len(merged)
    if removed_proc:
        print(f"  Removed from pool (post-mask quarantine): {removed_proc} rows")
        removed += removed_proc

    # Step 8: Post-mask deduplication & stratified ham balance
    print("\n[8/11] Post-mask deduplication...")
    before_postmask = len(merged)
    merged = deduplicate(merged)
    postmask_removed = before_postmask - len(merged)
    print(f"  Removed: {postmask_removed} texts (identical after masking)")
    print(f"  Unique pool: {len(merged)} rows")

    merged, ham_downsampled = balance_ham_per_language(merged, RANDOM_SEED)
    if ham_downsampled:
        print(f"  Stratified ham downsample for 45-55% balance: removed {ham_downsampled} ham rows")
    print(f"  Final pool: {len(merged)} rows")
    non_mobile_10d = sum(1 for r in merged if TEN_DIGIT_RE.search(r["text"]))
    print(f"  Non-mobile 10-digit numbers retained (e.g., Railway PNRs): {non_mobile_10d} rows")

    # Print distribution
    label_dist = Counter(r["label"] for r in merged)
    lang_dist = Counter(r["language"] for r in merged)
    print(f"\n  Label distribution: ham={label_dist[0]}, scam={label_dist[1]} "
          f"({label_dist[1] / len(merged) * 100:.1f}% scam)")
    print(f"  Language distribution: {dict(sorted(lang_dist.items()))}")

    # Step 9: Stratified split
    print("\n[9/11] Stratified train/val/test split (70/15/15)...")
    train, val, test = stratified_split(merged, RANDOM_SEED)
    print(f"  Train: {len(train)} rows")
    print(f"  Val:   {len(val)} rows")
    print(f"  Test:  {len(test)} rows")

    # Per-split stats
    for name, split in [("Train", train), ("Val", val), ("Test", test)]:
        scam_n = sum(1 for r in split if r["label"] == 1)
        pct = scam_n / len(split) * 100
        lang_counts = Counter(r["language"] for r in split)
        print(f"  {name}: scam={scam_n}/{len(split)} ({pct:.1f}%) | "
              f"langs={dict(sorted(lang_counts.items()))}")

    # Step 10: Validate
    print("\n[10/11] Running validation checks...")
    validation_errors = validate_splits(train, val, test, testset_texts_norm, testset_texts_processed)
    if validation_errors:
        print("  VALIDATION FAILED:")
        for err in validation_errors:
            print(f"    - {err}")
        sys.exit(1)
    else:
        print("  All 5 validation gates PASSED")

    # Step 11: Save
    print("\n[11/11] Saving output files...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    save_csv(train, OUTPUT_DIR / "train.csv")
    save_csv(val, OUTPUT_DIR / "val.csv")
    save_csv(test, OUTPUT_DIR / "test.csv")

    metadata = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "random_seed": RANDOM_SEED,
        "sources": {
            "D1": str(D1_PATH.name),
            "D3": str(D3_PATH.name),
            "D2_skipped": "marathi_scam_ham.csv (100% subset of D3)",
        },
        "preprocessing": {
            "nfc_normalize": True,
            "lowercase": True,
            "url_masking": "[URL]",
            "phone_masking": "[PHONE]",
            "entity_masking_order": "URL first, then phone",
        },
        "quarantine": {
            "testset_path": str(TESTSET_PATH.name),
            "testset_texts_removed": removed,
        },
        "deduplication": {
            "d1_duplicates_removed": len(d1_raw) - len(d1_dedup),
            "post_mask_duplicates_removed": postmask_removed,
            "ham_downsampled_for_balance": ham_downsampled,
            "non_mobile_10_digit_rows": non_mobile_10d,
        },
        "splits": {
            "train": {
                "rows": len(train),
                "scam": sum(1 for r in train if r["label"] == 1),
                "ham": sum(1 for r in train if r["label"] == 0),
                "languages": dict(Counter(r["language"] for r in train)),
            },
            "val": {
                "rows": len(val),
                "scam": sum(1 for r in val if r["label"] == 1),
                "ham": sum(1 for r in val if r["label"] == 0),
                "languages": dict(Counter(r["language"] for r in val)),
            },
            "test": {
                "rows": len(test),
                "scam": sum(1 for r in test if r["label"] == 1),
                "ham": sum(1 for r in test if r["label"] == 0),
                "languages": dict(Counter(r["language"] for r in test)),
            },
        },
        "total_unique_texts": len(merged),
    }
    save_metadata(metadata, OUTPUT_DIR / "metadata.json")

    print(f"\n  Saved to: {OUTPUT_DIR}/")
    print(f"    train.csv  ({len(train)} rows)")
    print(f"    val.csv    ({len(val)} rows)")
    print(f"    test.csv   ({len(test)} rows)")
    print(f"    metadata.json")
    print("\n" + "=" * 60)
    print("PHASE 1 COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()

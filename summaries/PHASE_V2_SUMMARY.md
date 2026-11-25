# Phase V2 Summary — Custom ML Classifier & 3-Signal Fusion

**Date:** 2026-11-25  
**Branch:** `feat/v2-ml-classifier` (branched from `main`)  
**Previous summaries:** [PHASE_0_SUMMARY.md](PHASE_0_SUMMARY.md), [PHASE_1_SUMMARY.md](PHASE_1_SUMMARY.md), [PHASE_2_SUMMARY.md](PHASE_2_SUMMARY.md)

---

## What Was Built

1. **Repo Hygiene (Phase A):** Restored [render.yaml](../render.yaml) and [README.md](../README.md) to repository root, removed redundant copies in `mdfiles/`, fixed relative summary/README links, and updated [.gitignore](../.gitignore) to exclude `backend/model/` and `*.onnx` while keeping small dataset CSVs tracked.
2. **Unified ML Preprocessing & Stratified Corpus (Phase B):** Added shared `preprocess_for_ml()` to [normalize.py](../backend/app/normalize.py) and wired [prepare_dataset.py](../backend/scripts/prepare_dataset.py) to import it directly (fixing train/inference skew D1). Generated 3,632 deduplicated, entity-masked rows (`train`: 2,542, `val`: 545, `test`: 545; 48.1% scam across all four languages) with 31 testset overlaps quarantined.
3. **Colab Training & INT8 ONNX Notebook (Phase C):** Authored [train_classifier.ipynb](../backend/scripts/train_classifier.ipynb) for `google/muril-base-cased` with `[URL]`/`[PHONE]` special tokens, `resize_token_embeddings`, early stopping on val F1, opset-17 ONNX export, INT8 dynamic quantization, 50-sample parity check, and Hugging Face Hub upload instructions.
4. **3-Signal Backend Integration (Phase D):**
   - [classifier.py](../backend/app/classifier.py): Lightweight `onnxruntime` + Rust `tokenizers` (`tokenizer.json`) inference without importing `transformers` or `torch` (D3).
   - [explainer.py](../backend/app/explainer.py): Single-batch pure-NumPy word-occlusion explainer (max 100 variants, top 6 words, 2.0 s budget; replaces `lime` per D11).
   - [fuse.py](../backend/app/fuse.py): Preserved `fuse(rule, llm, lang, ml=None)` signature (D4); enforces that ML can raise risk only when `is_scam and confidence >= 0.55` and never lowers the rule floor or triggers the known-script branch on confident non-scam predictions (D9).
   - [main.py](../backend/app/main.py), [triage.py](../backend/app/routes/triage.py), [schemas.py](../backend/app/schemas.py), [config.py](../backend/app/config.py): Startup `lifespan` loading onto `app.state`, `HealthOut.ml_model` (`loaded` / `unavailable`, always HTTP 200), `asyncio.to_thread` ML execution, and on-demand `?explain=true`.
   - [download_model.py](../backend/scripts/download_model.py): Build-time Hugging Face Hub downloader for Render (D10).
5. **Frontend Confidence & Word Highlights (Phase E):** Updated [api.ts](../frontend/src/lib/api.ts), [ResultCard.tsx](../frontend/src/components/ResultCard.tsx), [Check.tsx](../frontend/src/pages/Check.tsx), `frontend/src/i18n/{mr,hi,en}.json`, and added [TokenHighlights.tsx](../frontend/src/components/TokenHighlights.tsx) (main JS chunk: `341.1 KiB` vs `337.0 KiB` baseline).
6. **Evaluation & Deployment Config (Phases F–G):** Added [evaluate_classifier.py](../backend/scripts/evaluate_classifier.py), [EVALUATION.md](../EVALUATION.md), updated root [render.yaml](../render.yaml) (`buildCommand`, `PYTHON_VERSION=3.13.2`, `HF_MODEL_REPO`, `ML_ENABLED`), [.env.example](../.env.example), and [README.md](../README.md).

---

## Key Deviations & Decisions

- **D10 (Build-time download):** Model artifacts download into `backend/model/` during `render.yaml` `buildCommand` instead of runtime `/tmp` because Render free tier wipes `/tmp` on 15-minute idle sleep.
- **D11 (Pure-NumPy word occlusion):** Replaced `lime` with single-batch word occlusion in [explainer.py](../backend/app/explainer.py) to avoid installing `scikit-image`, `scipy`, and `matplotlib` in the 512 MB Render image.
- **Option A (`test_health.py`):** Updated exact-dict equality assertion in [test_health.py](../backend/tests/test_health.py) to validate `status == "ok"` and `ml_model in {"loaded", "unavailable"}`.

---

## Problems Faced & Fixes

- **`pip install --target --upgrade` erased `google/genai`:** Resolved by merge-copying `google-genai` and `google-auth` back into `backend/.venv/Lib/site-packages/google/` alongside `protobuf` (logged in [MISTAKES.md](../mdfiles/MISTAKES.md)).
- **Post-mask deduplication skew & PNR digits:** Balanced ham proportionally (`3,632` rows, `48.1%` scam) and scoped leak assertion to `PHONE_RE` (`[6-9]\d{9}`) so 32 legitimate Railway PNR rows stay intact.

---

## Verification Status

| Gate | Status | Evidence |
| --- | --- | --- |
| Gate A (Repo hygiene) | PASSED | `feat/v2-ml-classifier` clean commits; 68/68 baseline tests green |
| Gate B (Dataset prep) | PASSED | 3,632 unique rows, 48.1% scam, 0 leaks/overlaps |
| Gate C (Colab training) | PENDING (HUMAN STEP) | Notebook AST-verified; run [train_classifier.ipynb](../backend/scripts/train_classifier.ipynb) on Colab T4 |
| Gate D (Backend + stub ML) | PASSED (ML-on PENDING) | 81/81 pytest green; `eval.py --no-llm` 40/40 |
| Gate E (Frontend build) | PASSED | `tsc -b && vite build` 0 errors; main chunk `341.1 KiB` (<= 370 KB) |
| Gate F–G (Eval & Render) | PARTIAL (HUMAN STEP) | Rules baseline 40/40 in `EVALUATION.md`; HF upload & Render deploy pending Colab |

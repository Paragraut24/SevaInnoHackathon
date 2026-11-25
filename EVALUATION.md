# Sajag — Model Evaluation Results

Generated from measured script outputs (`backend/data/ml_dataset/metadata.json` and `backend/scripts/evaluate_classifier.py`). No numbers are estimated or invented.

> **Current Status:** Rules-only baseline and dataset preparation are measured and verified. Custom MuRIL INT8 ONNX model metrics are **PENDING** execution of `backend/scripts/train_classifier.ipynb` on Colab T4 (Phase C) and re-running `backend/scripts/evaluate_classifier.py` with `backend/model/` populated.

---

## 1. Training Corpus (`backend/data/ml_dataset/`)

| Metric | Measured Value |
| --- | --- |
| Seed sources | `multilingual_mr_hi_en.csv` (4,400) + `indian_call_scams_hinglish_sample.csv` (320) |
| Skipped redundant source | `marathi_scam_ham.csv` (100% subset of multilingual corpus) |
| D1 internal duplicates removed | 121 |
| Testset messages quarantined | 31 (zero raw or post-mask overlap with `testset/messages.csv`) |
| Post-mask duplicates removed | 605 (templates differing only by masked `[URL]` / `[PHONE]`) |
| Stratified ham downsample | 331 (maintains 48.1% scam / 51.9% ham across every split) |
| **Final unique pool** | **3,632** (`train`: 2,542, `val`: 545, `test`: 545) |
| Train split breakdown | 1,222 scam / 1,320 ham (`Hindi`: 613, `Marathi`: 607, `English`: 609, `Hinglish`: 713) |
| Val split breakdown | 262 scam / 283 ham (`Marathi`: 131, `Hinglish`: 152, `Hindi`: 130, `English`: 132) |
| Test split breakdown | 262 scam / 283 ham (`Hinglish`: 153, `Hindi`: 132, `Marathi`: 130, `English`: 130) |

All splits use shared `preprocess_for_ml()` (`backend/app/normalize.py`): Unicode NFC, zero-width stripping, Devanagari-to-ASCII digit conversion, Latin lowercasing, URL masking (`[URL]`), and Indian mobile masking (`[PHONE]`). 32 rows retain non-mobile 10-digit numbers (such as Railway PNR references) by design.

---

## 2. Custom MuRIL Scam Classifier (`test.csv`, 545 samples)

| Metric | Target (Gate C) | Measured Value |
| --- | --- | --- |
| Base model | `google/muril-base-cased` (binary) | `PENDING (Phase C Colab run)` |
| Accuracy | >= 88% | `PENDING` |
| F1 (scam class) | >= 0.87 | `PENDING` |
| Precision (scam class) | >= 0.85 | `PENDING` |
| Recall (scam class) | >= 0.88 | `PENDING` |
| Quantized INT8 ONNX size | < 150 MB | `PENDING` |
| ONNX vs PyTorch parity | < 1e-2 max prob diff (50 samples) | `PENDING` |

### Per-Language Performance (`test.csv`)

| Language | Test Samples | Target F1 | Measured F1 |
| --- | --- | --- | --- |
| Marathi | 130 | >= 0.80 | `PENDING` |
| Hindi | 132 | >= 0.80 | `PENDING` |
| Hinglish | 153 | >= 0.80 | `PENDING` |
| English | 130 | >= 0.80 | `PENDING` |

---

## 3. Signal Pipeline Comparison (`testset/messages.csv`, 40 messages)

| Configuration | Overall | Marathi (14) | Hindi (13) | English (13) | Genuine False Alarms | Latency (p95) | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Rules only (`eval.py --no-llm` / `evaluate_classifier.py`) | **40/40 (100%)** | 14/14 | 13/13 | 13/13 | 0 | 1.9 ms | Measured |
| Rules + Gemini (`--with-llm`) | — | — | — | — | — | — | Not run in offline verification (requires live API quota) |
| ML only (`model_quantized.onnx`) | — | — | — | — | — | — | `PENDING (Phase C)` |
| Rules + ML | — | — | — | — | — | — | `PENDING (Phase C)` |
| Rules + ML + Gemini | — | — | — | — | — | — | `PENDING (Phase C)` |

---

## 4. Architecture Notes & Deviations from Initial V2 Plan

1. **Pure-NumPy Word Occlusion (`backend/app/explainer.py`, Deviation D11):** Replaced the `lime` Python package with a single-batch numpy word-occlusion explainer (max 100 variants, top 6 words, 2.0 s budget) to avoid pulling `scikit-image`, `scipy`, and `matplotlib` onto the 512 MB Render instance.
2. **Build-Time Model Download (Deviation D10):** `backend/scripts/download_model.py` fetches ONNX artifacts during Render's `buildCommand` into `backend/model/` rather than downloading into ephemeral `/tmp` at container wake.
3. **Runtime Memory Guard (Deviation D3):** Runtime inference imports only `onnxruntime` and Rust `tokenizers` (`tokenizer.json`), keeping `transformers` and `torch` out of production dependencies.

---

## 5. Failure Cases & Next Step

- **Rules-only misses on `testset/messages.csv`:** None (0/40).
- **Post-Colab refresh command:** After running `backend/scripts/train_classifier.ipynb` and placing `model_quantized.onnx`, `tokenizer.json`, and `config.json` into `backend/model/` (or downloading via `download_model.py`), run:
  ```bash
  backend/.venv/Scripts/python.exe backend/scripts/evaluate_classifier.py --json-out eval_results.json
  ```
  and replace the `PENDING` cells above with the measured script output and generated confusion matrix.

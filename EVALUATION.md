# Sajag — Model Evaluation Results

Generated from measured script outputs (`backend/data/ml_dataset/metadata.json` and `backend/scripts/evaluate_classifier.py`). No numbers are estimated or invented.

> **Current Status:** Gate C & offline Gate D–F verification **COMPLETE**. Trained `distilbert-base-multilingual-cased` (explicit Gate C size fallback) -> pre-processed INT8 ONNX (`129.59 MB`), evaluated both in Google Colab T4 and locally via `backend/scripts/evaluate_classifier.py` with `backend/model/` loaded. Gemini live-quota path (`--with-llm`) not executed in offline verification.

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

All splits use shared `preprocess_for_ml()` (`backend/app/normalize.py`): Unicode NFC, zero-width stripping, Devanagari-to-ASCII digit conversion, Latin lowercasing, URL masking (`[URL]`), phone masking (`[PHONE]`), and uppercase placeholder preservation for idempotency. 32 rows retain non-mobile 10-digit numbers (such as Railway PNR references) by design.

---

## 2. Custom Multilingual Scam Classifier (`test.csv`, 545 samples)

| Metric | Target (Gate C) | Measured Value |
| --- | --- | --- |
| Base model | `google/muril-base-cased` -> fallback `distilbert-base-multilingual-cased` | `distilbert-base-multilingual-cased` (`google/muril-base-cased` INT8 ONNX was 227.26–227.57 MB >= 150 MB cap) |
| Accuracy | >= 88% | **99.08%** (0.9908) |
| F1 (scam class) | >= 0.87 | **0.9904** |
| Precision (scam class) | >= 0.85 | **0.9923** |
| Recall (scam class) | >= 0.88 | **0.9885** |
| Confusion matrix (`ham`, `scam`) | — | `[[281, 2], [3, 259]]` (281 TN, 2 FP, 3 FN, 259 TP) |
| Quantized INT8 ONNX size | < 150 MB | **129.59 MB** (`tokenizer.json`: `2.78 MB`) |
| ONNX vs PyTorch parity | < 1e-2 FP32 / label match INT8 | FP32 max prob diff `0.000000`, INT8 label agreement **100.0%** (50 samples) |
| Process memory (RSS after load + explain) | < 450 MB | **279.5 MB** RSS (`289.3 MB` peak) |

### Per-Language Performance (`test.csv`, INT8 ONNX)

| Language | Test Samples | Target F1 | Measured Accuracy | Measured F1 |
| --- | --- | --- | --- | --- |
| Marathi | 130 | >= 0.80 | 0.9769 | **0.9756** |
| Hindi | 132 | >= 0.80 | 1.0000 | **1.0000** |
| Hinglish | 153 | >= 0.80 | 0.9935 | **0.9935** |
| English | 130 | >= 0.80 | 0.9923 | **0.9917** |

---

## 3. Signal Pipeline Comparison (`testset/messages.csv`, 40 messages)

| Configuration | Overall | Marathi (14) | Hindi (13) | English (13) | Genuine False Alarms | Latency (p95) | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Rules only (`evaluate_classifier.py`) | **40/40 (100%)** | 14/14 | 13/13 | 13/13 | 0 | 0.6 ms | Measured |
| ML only (`model_quantized.onnx`) | **36/40 (90.0%)** | 14/14 | 12/13 | 10/13 | 0 | 71.7 ms | Measured |
| Rules + ML (`fuse(rule, None, ml)`) | **40/40 (100%)** | 14/14 | 13/13 | 13/13 | 0 | 46.1 ms | Measured |
| Rules + Gemini (`--with-llm`) | — | — | — | — | — | — | Not run (requires live API quota) |
| Rules + ML + Gemini | — | — | — | — | — | — | Not run (requires live API quota) |

---

## 4. Architecture Notes & Deviations from Initial V2 Plan

1. **DistilBERT Fallback for Render Memory Budget (`distilbert-base-multilingual-cased`):** `google/muril-base-cased` achieved 0.9981 PyTorch F1, but its 197k-token embedding table kept INT8 ONNX at `227.26–227.57 MB` (exceeding Gate C `< 150 MB`). Switching to the explicit Gate C fallback `distilbert-base-multilingual-cased` with `quant_pre_process(..., skip_symbolic_shape=True)` + `per_channel=True, reduce_range=True, QInt8` yielded `129.59 MB` INT8 ONNX, `0.9904` F1, `100%` INT8 parity, and `279.5 MB` process RSS.
2. **Pure-NumPy Word Occlusion (`backend/app/explainer.py`, Deviation D11):** Replaced the `lime` Python package with a single-batch numpy word-occlusion explainer (max 100 variants, top 6 words, 2.0 s budget) to avoid pulling `scikit-image`, `scipy`, and `matplotlib` onto the 512 MB Render instance (measured `393.2 ms` on sample message).
3. **Build-Time Model Download (Deviation D10):** `backend/scripts/download_model.py` fetches ONNX artifacts during Render's `buildCommand` into `backend/model/` rather than downloading into ephemeral `/tmp` at container wake.
4. **Runtime Memory Guard (Deviation D3):** Runtime inference imports only `onnxruntime` and Rust `tokenizers` (`tokenizer.json`), keeping `transformers` and `torch` out of production dependencies.

---

## 5. Failure Cases & Verification Notes

- **Rules-only & Rules+ML misses on `testset/messages.csv`:** None (0/40, 0 false alarms).
- **ML-only misses on `testset/messages.csv` (4/40, all covered by deterministic rules):** `hi_02` (electricity disconnect), `en_02` (SBI KYC suspension), `en_03` (electricity overdue), `en_05` (private video extortion).
- **`test.csv` INT8 errors (5/545):** 2 Marathi ham false positives (LIC premium receipt notice, Netflix auto-debit notice) and 3 scam misses (1 Hinglish digital-arrest snippet, 1 Marathi Telegram ban phishing, 1 English UK lottery message).

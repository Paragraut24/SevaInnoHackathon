# Fix #1: Custom ML Scam Classifier — Fool-Proof Implementation Plan

> **Goal:** Train, export, deploy, and integrate an original multilingual scam classifier that becomes the third signal in Sajag's fusion pipeline — giving judges undeniable proof of original ML work.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Key Decisions (Already Made)](#2-key-decisions-already-made)
3. [Architecture: Before vs After](#3-architecture-before-vs-after)
4. [Phase 1 — Data Preparation](#4-phase-1--data-preparation)
5. [Phase 2 — Model Training (Colab)](#5-phase-2--model-training-colab)
6. [Phase 3 — Explainability (LIME)](#6-phase-3--explainability-lime)
7. [Phase 4 — ONNX Export & Quantization](#7-phase-4--onnx-export--quantization)
8. [Phase 5 — Backend Integration](#8-phase-5--backend-integration)
9. [Phase 6 — Frontend Integration](#9-phase-6--frontend-integration)
10. [Phase 7 — Evaluation & Results Artifact](#10-phase-7--evaluation--results-artifact)
11. [Phase 8 — Deployment](#11-phase-8--deployment)
12. [File Manifest](#12-file-manifest)
13. [Risk Register](#13-risk-register)
14. [Time Budget](#14-time-budget)

---

## 1. Executive Summary

**What we're building:** A fine-tuned MuRIL (`google/muril-base-cased`) transformer classifier for multilingual Indian scam detection, exported to ONNX with INT8 quantization, served alongside the existing rule engine and Gemini LLM in a three-signal fusion architecture with LIME-based token-level explainability.

**Why MuRIL over IndicBERT:** Our datasets contain heavy Hinglish code-mixing (Latin-script Hindi) alongside native-script Marathi and Hindi. MuRIL was explicitly pre-trained on transliterated pairs (Dakshina corpus), giving it a decisive edge on code-mixed text. IndicBERT excels on clean native-script text but struggles with romanized input without specialized fine-tuning.

**Why ONNX:** Render free tier has 512MB RAM. A full PyTorch + transformers runtime exceeds this easily (~800MB+). ONNX Runtime + quantized INT8 model keeps total RAM under 350MB, fitting comfortably. No GPU needed at inference time.

**End result for judges:**
- "We trained our own MuRIL-based classifier on 5,820 Indian scam messages across Marathi, Hindi, Hinglish, and English"
- "Our model achieves X% F1 on a held-out test set, and we can show you exactly which words triggered the detection" (LIME highlights)
- "The classifier runs as a 25MB quantized ONNX model — no GPU needed, sub-100ms inference"

---

## 2. Key Decisions (Already Made)

| Decision | Choice | Rationale |
|---|---|---|
| **Base model** | `google/muril-base-cased` (236M params) | Best code-mixed (Hinglish) + native-script Indian language support; pre-trained on transliterated pairs |
| **Task type** | Multi-class classification (scam categories) + binary (scam vs ham) | Binary head for the fusion pipeline; multi-class for the UI explanation card |
| **Training environment** | Google Colab Free Tier (T4 GPU) | 5,820 samples, 3 epochs = ~3-5 minutes training time; well within free tier limits |
| **Export format** | ONNX + INT8 dynamic quantization | Keeps model ~25-40MB on disk, ~80-120MB in RAM; fits Render's 512MB limit |
| **Explainability** | LIME (not SHAP) | Faster for single-instance explanations; model-agnostic so works with ONNX; generates HTML token highlights |
| **Deployment target** | Same Render instance as existing FastAPI backend | No new service needed; ONNX model loaded at startup as a global session |
| **Integration point** | New 3rd signal in `fuse.py` alongside rules and Gemini | ML classifier provides `ml_risk` + `ml_confidence` + `ml_scam_type`; fusion uses highest of (rule_floor, ml_risk, llm_risk) for known categories |

---

## 3. Architecture: Before vs After

### Before (Current — 2 Signals)
```
User text → Normalize → Rules Engine (floor) ──┐
                        │                       ├→ Fuse → TriageOut
                        └→ Gemini LLM (explain) ┘
```

### After (V2 — 3 Signals)
```
User text → Normalize ──┬→ Rules Engine (floor)         ──┐
                        ├→ MuRIL ONNX Classifier (ml)   ──┼→ Fuse V2 → TriageOut
                        └→ Gemini LLM (explain)          ──┘
                                     │
                              LIME explainer (on demand)
                                     │
                              token highlights → UI
```

### Fusion Logic V2 (Updated `fuse.py`)

```
1. rule_floor = rules.evaluate(text)         # existing: "low" | "medium" | "high"
2. ml_result  = classifier.predict(text)     # NEW: {risk, scam_type, confidence, top_tokens}
3. llm_result = gemini.analyze(text, hints)  # existing: {risk, scam_type, reasons, next_steps}

Final risk = max(rule_floor, ml_risk, llm_risk)  -- IF rule.known_script or ml.confidence > 0.7
           = max(ml_risk, llm_risk)              -- IF rule.floor == "low" and ml.confidence > 0.7
           = llm_risk                            -- fallback if ML also uncertain

ML classifier CANNOT lower risk below rule floor (same invariant as Gemini).
ML classifier CAN raise risk above rule floor (new capability).
```

---

## 4. Phase 1 — Data Preparation

**Time estimate: 1.5 hours**

### 4.1 Dataset Inventory

| Dataset | Rows | Languages | Scam/Ham |
|---|---|---|---|
| `multilingual_mr_hi_en.csv` | 4,400 | mr, hi, hinglish, en | ~2,200 / ~2,200 (balanced) |
| `marathi_scam_ham.csv` | 1,100 | mr | 550 / 550 |
| `indian_call_scams_hinglish_sample.csv` | 320 | hinglish | 280 / 40 |
| **Combined total** | **5,820** | 4 languages | ~3,030 scam / ~2,790 ham |

### 4.2 Label Taxonomy

We'll train **two heads** in a single model:

**Head 1 — Binary (used in fusion):**
- `0` = ham (legitimate)
- `1` = scam

**Head 2 — Multi-class (used for UI scam-type display):**
Mapped from the existing `scam_category` column in the datasets:

| ID | Label | Source datasets |
|---|---|---|
| 0 | ham | All datasets |
| 1 | digital_arrest | `indian_call_scams_hinglish_sample.csv` (police_digital_arrest) |
| 2 | kyc_bank | `indian_call_scams_hinglish_sample.csv` (bank_kyc), `multilingual_mr_hi_en.csv` |
| 3 | investment | `multilingual_mr_hi_en.csv` |
| 4 | job_lottery | `indian_call_scams_hinglish_sample.csv` (lottery), `multilingual_mr_hi_en.csv` |
| 5 | courier | `multilingual_mr_hi_en.csv` |
| 6 | utility_bill | `multilingual_mr_hi_en.csv` |
| 7 | family_emergency | `indian_call_scams_hinglish_sample.csv` (relative) |
| 8 | sextortion | `indian_call_scams_hinglish_sample.csv` (police_blackmail) |
| 9 | otp_request | `multilingual_mr_hi_en.csv` |
| 10 | loan_app | `multilingual_mr_hi_en.csv` |
| 11 | aadhaar | `indian_call_scams_hinglish_sample.csv` (aadhaar) |
| 12 | amazon | `indian_call_scams_hinglish_sample.csv` (amazon) |
| 13 | generic_scam | Any scam that doesn't fit above |

### 4.3 Preprocessing Pipeline

Create `backend/scripts/prepare_dataset.py`:

```python
"""
Merge all datasets → unified format → stratified train/val/test split.

Output: backend/data/ml_dataset/{train,val,test}.csv
Columns: text, binary_label, category_label, category_id, language
"""
```

**Steps:**
1. Load all 3 CSVs
2. Normalize category names → unified taxonomy (mapping table above)
3. Pre-process text:
   - NFC normalize (reuse `normalize.normalize_text()`)
   - Mask URLs with `[URL]` token (prevents overfitting on specific domains)
   - Mask phone numbers with `[PHONE]` token
   - Cap at 256 chars (MuRIL max_length=128 tokens; 256 chars ~= 80-100 tokens for Indian text)
4. Stratified split: **70% train / 15% val / 15% test**
   - Stratify on `(language, binary_label)` to ensure balanced representation
5. Save as `train.csv`, `val.csv`, `test.csv` in `backend/data/ml_dataset/`

**Data quality checks (assertions in script):**
- No empty text fields
- Every split has all 4 languages represented
- Scam/ham ratio within 40-60% in each split
- No duplicate texts across splits
- Print class distribution per split

### 4.4 Entity Masking (Critical for Generalization)

```python
import re
from app.normalize import URL_RE, PHONE_RE

def mask_entities(text: str) -> str:
    """Replace volatile entities to prevent overfitting on specific URLs/numbers."""
    text = URL_RE.sub("[URL]", text)
    text = PHONE_RE.sub("[PHONE]", text)
    return text
```

**Why this matters:** Without masking, the model learns "bit.ly = scam" rather than "urgency + link + KYC threat = scam". Masking forces the model to learn semantic patterns, not memorize URLs.

---

## 5. Phase 2 — Model Training (Google Colab)

**Time estimate: 2.5 hours (including Colab setup, debugging, iteration)**

### 5.1 Colab Notebook Structure

Create `backend/scripts/train_classifier.ipynb` (runs on Colab T4 GPU):

#### Cell 1: Setup
```python
# Install dependencies
!pip install transformers datasets evaluate accelerate scikit-learn onnx onnxruntime optimum[onnxruntime] lime -q

# Mount Google Drive (to save model artifacts)
from google.colab import drive
drive.mount('/content/drive')
```

#### Cell 2: Load & Tokenize Data
```python
import pandas as pd
from datasets import Dataset, DatasetDict
from transformers import AutoTokenizer

MODEL_ID = "google/muril-base-cased"
MAX_LENGTH = 128  # tokens
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

# Load prepared CSVs (upload from backend/data/ml_dataset/)
train_df = pd.read_csv("train.csv")
val_df = pd.read_csv("val.csv")
test_df = pd.read_csv("test.csv")

dataset = DatasetDict({
    "train": Dataset.from_pandas(train_df),
    "validation": Dataset.from_pandas(val_df),
    "test": Dataset.from_pandas(test_df),
})

def tokenize(batch):
    return tokenizer(batch["text"], truncation=True, max_length=MAX_LENGTH, padding="max_length")

tokenized = dataset.map(tokenize, batched=True, remove_columns=["text", "language", "category_label"])
tokenized = tokenized.rename_column("binary_label", "labels")
tokenized.set_format("torch", columns=["input_ids", "attention_mask", "labels"])
```

#### Cell 3: Training Configuration
```python
from transformers import AutoModelForSequenceClassification, TrainingArguments, Trainer
import evaluate
import numpy as np

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_ID,
    num_labels=2,  # binary: ham vs scam
    id2label={0: "ham", 1: "scam"},
    label2id={"ham": 0, "scam": 1},
)

accuracy_metric = evaluate.load("accuracy")
f1_metric = evaluate.load("f1")
precision_metric = evaluate.load("precision")
recall_metric = evaluate.load("recall")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        "accuracy": accuracy_metric.compute(predictions=preds, references=labels)["accuracy"],
        "f1": f1_metric.compute(predictions=preds, references=labels)["f1"],
        "precision": precision_metric.compute(predictions=preds, references=labels)["precision"],
        "recall": recall_metric.compute(predictions=preds, references=labels)["recall"],
    }

training_args = TrainingArguments(
    output_dir="./muril_scam_classifier",
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=32,
    per_device_eval_batch_size=32,
    num_train_epochs=5,
    weight_decay=0.01,
    warmup_ratio=0.1,
    fp16=True,
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    greater_is_better=True,
    logging_steps=25,
    report_to="none",
    seed=42,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized["train"],
    eval_dataset=tokenized["validation"],
    compute_metrics=compute_metrics,
)
```

**Hyperparameter choices:**
- `learning_rate=2e-5`: Standard for BERT fine-tuning; prevents catastrophic forgetting
- `num_train_epochs=5`: Small dataset benefits from more epochs; early stopping via `load_best_model_at_end`
- `warmup_ratio=0.1`: Gradual warmup prevents destabilizing pre-trained weights
- `weight_decay=0.01`: Mild regularization
- `fp16=True`: Halves memory on T4 GPU, speeds up 1.5x
- `batch_size=32`: T4 has 15GB VRAM; MuRIL at max_length=128 with bs=32 uses ~6GB — plenty of headroom

#### Cell 4: Train
```python
trainer.train()
```

**Expected output:** ~3-5 minutes total. 5 epochs x ~100 steps/epoch at bs=32 with 4,074 training samples.

#### Cell 5: Evaluate on Test Set
```python
results = trainer.evaluate(tokenized["test"])
print(results)

# Per-class detailed report
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

preds = trainer.predict(tokenized["test"])
y_pred = np.argmax(preds.predictions, axis=-1)
y_true = preds.label_ids

print(classification_report(y_true, y_pred, target_names=["ham", "scam"]))

# Confusion matrix
cm = confusion_matrix(y_true, y_pred)
plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=["ham", "scam"], yticklabels=["ham", "scam"])
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Sajag MuRIL Scam Classifier — Confusion Matrix")
plt.savefig("confusion_matrix.png", dpi=150, bbox_inches="tight")
plt.show()
```

#### Cell 6: Per-Language Breakdown
```python
# Evaluate per language
test_df["prediction"] = y_pred
for lang in ["English", "Hindi", "Hinglish", "Marathi"]:
    subset = test_df[test_df["language"] == lang]
    if len(subset) > 0:
        print(f"\n=== {lang} ({len(subset)} samples) ===")
        print(classification_report(
            subset["binary_label"], subset["prediction"],
            target_names=["ham", "scam"], zero_division=0
        ))
```

#### Cell 7: Save Model
```python
trainer.save_model("./muril_scam_final")
tokenizer.save_pretrained("./muril_scam_final")
```

### 5.2 Training Expectations

Based on research and dataset characteristics:

| Metric | Expected Range | Minimum Acceptable |
|---|---|---|
| **Accuracy** | 92-96% | 88% |
| **F1 (scam class)** | 91-95% | 87% |
| **Precision (scam)** | 90-95% | 85% |
| **Recall (scam)** | 92-97% | 88% |

If results fall below minimum: increase epochs to 8, try `learning_rate=3e-5`, or add class weights for the minority class.

### 5.3 Multi-Class Head (Optional Enhancement)

If binary model trains successfully, add a second training run with multi-class labels:

```python
# Same architecture, but num_labels=14 (ham + 13 scam categories)
multi_model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_ID, num_labels=14
)
# Train similarly, save as muril_scam_multiclass/
```

**Decision point:** If multi-class accuracy is poor (< 75% macro F1) due to class imbalance, stick with binary-only. The binary model is sufficient for the fusion pipeline; the multi-class is a nice-to-have for the UI.

---

## 6. Phase 3 — Explainability (LIME)

**Time estimate: 1.5 hours**

### 6.1 LIME Integration Module

Create `backend/app/explainer.py`:

```python
"""
LIME-based token explainability for the MuRIL scam classifier.

Generates per-token importance scores that show judges EXACTLY which words
triggered the scam detection — the "Responsible AI" differentiator.
"""
import logging
from functools import lru_cache

import numpy as np
from lime.lime_text import LimeTextExplainer

from app.classifier import get_classifier

logger = logging.getLogger("sajag.explainer")

# Cache the explainer instance (stateless, reusable)
@lru_cache
def _explainer() -> LimeTextExplainer:
    return LimeTextExplainer(
        class_names=["legitimate", "suspicious"],
        split_expression=r'\s+',  # word-level splits
        bow=False,
    )


def explain(text: str, num_features: int = 6) -> list[dict]:
    """
    Return top N tokens with their importance weights for the prediction.

    Returns: [{"token": "OTP", "weight": 0.82, "direction": "scam"}, ...]
    """
    classifier = get_classifier()
    if classifier is None:
        return []

    try:
        def predict_fn(texts: list[str]) -> np.ndarray:
            results = [classifier.predict(t) for t in texts]
            return np.array([[1 - r["confidence"], r["confidence"]] for r in results])

        exp = _explainer().explain_instance(
            text,
            predict_fn,
            num_features=num_features,
            num_samples=200,  # keep fast; 200 perturbations ~= 100ms
            top_labels=1,
        )

        label = exp.available_labels()[0]
        features = exp.as_list(label=label)

        return [
            {
                "token": token,
                "weight": round(abs(weight), 3),
                "direction": "suspicious" if weight > 0 else "legitimate",
            }
            for token, weight in sorted(features, key=lambda x: abs(x[1]), reverse=True)
        ]
    except Exception as exc:
        logger.warning("lime_explain_failed type=%s", type(exc).__name__)
        return []
```

### 6.2 When to Run LIME

LIME is computationally expensive (~200 forward passes per explanation). We only run it:
- When ML confidence > 0.6 (worth explaining)
- On demand via a query parameter `?explain=true` in the triage endpoint
- Never in the fast path — it's an async background enrichment

### 6.3 UI Display

Token highlights render in the `ResultCard` component as colored spans:
- Red-shaded tokens = pushed toward "scam" classification
- Green-shaded tokens = pushed toward "legitimate"
- Opacity proportional to weight (0.0 → transparent, 1.0 → solid)

This is the **"Responsible AI" feature judges want to see** — transparent, interpretable AI decisions.

---

## 7. Phase 4 — ONNX Export & Quantization

**Time estimate: 1 hour**

### 7.1 Export Script (In Colab)

Add to the training notebook:

```python
from optimum.onnxruntime import ORTModelForSequenceClassification
from onnxruntime.quantization import quantize_dynamic, QuantType
import os

# Step 1: Export to ONNX
ort_model = ORTModelForSequenceClassification.from_pretrained(
    "./muril_scam_final", export=True
)
ort_model.save_pretrained("./muril_onnx")
tokenizer.save_pretrained("./muril_onnx")

# Step 2: INT8 Dynamic Quantization
quantize_dynamic(
    model_input="./muril_onnx/model.onnx",
    model_output="./muril_onnx/model_quantized.onnx",
    weight_type=QuantType.QUInt8,
)

# Step 3: Verify sizes
original = os.path.getsize("./muril_onnx/model.onnx") / (1024 * 1024)
quantized = os.path.getsize("./muril_onnx/model_quantized.onnx") / (1024 * 1024)
print(f"Original ONNX: {original:.1f} MB")
print(f"Quantized ONNX: {quantized:.1f} MB")
print(f"Compression ratio: {original/quantized:.1f}x")
```

### 7.2 Expected Sizes

| Artifact | Size |
|---|---|
| PyTorch model (`pytorch_model.bin`) | ~900 MB |
| ONNX model (`model.onnx`) | ~450 MB |
| Quantized ONNX (`model_quantized.onnx`) | ~110-120 MB |

> **CRITICAL CONSTRAINT CHECK:** Render Free Tier = 512 MB RAM.
> - Python + FastAPI + Uvicorn baseline: ~80 MB
> - ONNX Runtime (cpu-only): ~30 MB
> - Quantized model in memory: ~150-200 MB (model graph + session overhead)
> - Existing app overhead: ~30 MB
> - **Total: ~290-340 MB** — fits within 512 MB with headroom.

### 7.3 If Model Is Too Large

**Fallback plan:** Use `google/muril-base-cased` with knowledge distillation or switch to a smaller student model:
- Option A: Use `distilbert-base-multilingual-cased` (66M params, ~170MB ONNX, ~45MB quantized) — less accurate on Indian languages but much smaller
- Option B: Use `ai4bharat/IndicBERTv2-MLM-only` (ALBERT-based, naturally smaller)
- Option C: Apply ONNX graph optimizations (`onnxruntime.transformers.optimizer`) to fuse layers and reduce overhead

**Decision rule:** If quantized ONNX > 150 MB, switch to Option A. Accuracy difference is ~3-5% which is acceptable for a hackathon.

### 7.4 Files to Commit

Copy from Colab to the repo:
```
backend/
  model/
    model_quantized.onnx      # The quantized model (~110MB, goes in Git LFS or downloaded at deploy time)
    tokenizer_config.json      # Tokenizer config
    vocab.txt                  # Vocabulary file
    special_tokens_map.json    # Special tokens
    config.json                # Model config (num_labels, id2label, etc.)
```

> **Git LFS decision:** If model > 50MB, store on Hugging Face Hub (free) and download at container startup. Do NOT commit large binaries to GitHub.
>
> **Deploy-time download approach (recommended):**
> ```python
> # In backend/app/classifier.py startup
> from huggingface_hub import hf_hub_download
> model_path = hf_hub_download(repo_id="your-team/sajag-scam-classifier", filename="model_quantized.onnx")
> ```

---

## 8. Phase 5 — Backend Integration

**Time estimate: 2 hours**

### 8.1 New File: `backend/app/classifier.py`

```python
"""
ONNX-based MuRIL scam classifier — the Sajag ML signal.

Loads a quantized ONNX model at startup and provides sync/async predict()
that returns binary risk, confidence, and scam category.
"""
import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

logger = logging.getLogger("sajag.classifier")

MODEL_DIR = Path(__file__).resolve().parents[1] / "model"
ONNX_FILE = "model_quantized.onnx"
CONFIDENCE_HIGH = 0.85
CONFIDENCE_MEDIUM = 0.55


@dataclass(frozen=True)
class MlResult:
    """Result from the ML classifier."""
    is_scam: bool
    confidence: float       # 0.0–1.0 for the predicted class
    risk: str               # "low" | "medium" | "high"
    # scam_type: str | None   # multi-class label (future)


@lru_cache
def get_classifier():
    """Load ONNX model + tokenizer once. Returns None if model files missing."""
    onnx_path = MODEL_DIR / ONNX_FILE
    if not onnx_path.exists():
        logger.warning("ml_model_not_found path=%s", onnx_path)
        return None

    try:
        import onnxruntime as ort
        from transformers import AutoTokenizer

        session = ort.InferenceSession(
            str(onnx_path),
            providers=["CPUExecutionProvider"],
            sess_options=_session_options(),
        )
        tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
        logger.info("ml_model_loaded path=%s", onnx_path)
        return _Classifier(session, tokenizer)
    except Exception as exc:
        logger.error("ml_model_load_failed type=%s msg=%s", type(exc).__name__, exc)
        return None


def _session_options():
    import onnxruntime as ort
    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    opts.intra_op_num_threads = 1  # single-threaded for Render's shared CPU
    opts.inter_op_num_threads = 1
    return opts


class _Classifier:
    """Thin wrapper around ONNX session + tokenizer."""

    def __init__(self, session, tokenizer):
        self._session = session
        self._tokenizer = tokenizer

    def predict(self, text: str) -> MlResult:
        inputs = self._tokenizer(
            text,
            truncation=True,
            max_length=128,
            padding="max_length",
            return_tensors="np",
        )
        ort_inputs = {
            "input_ids": inputs["input_ids"].astype(np.int64),
            "attention_mask": inputs["attention_mask"].astype(np.int64),
        }

        # Handle models with or without token_type_ids
        if "token_type_ids" in [i.name for i in self._session.get_inputs()]:
            ort_inputs["token_type_ids"] = inputs.get(
                "token_type_ids", np.zeros_like(inputs["input_ids"])
            ).astype(np.int64)

        logits = self._session.run(None, ort_inputs)[0]
        probs = _softmax(logits[0])
        scam_prob = float(probs[1])
        is_scam = scam_prob > 0.5

        if scam_prob >= CONFIDENCE_HIGH:
            risk = "high"
        elif scam_prob >= CONFIDENCE_MEDIUM:
            risk = "medium"
        else:
            risk = "low"

        return MlResult(
            is_scam=is_scam,
            confidence=round(scam_prob if is_scam else 1 - scam_prob, 3),
            risk=risk,
        )


def _softmax(x):
    e = np.exp(x - np.max(x))
    return e / e.sum()
```

### 8.2 Updated `backend/app/fuse.py` (V2)

```python
from app.classifier import MlResult, get_classifier
from app.rules import RuleResult, get_fallback
from app.schemas import Lang, LlmOut, Risk, TriageOut

RANK: dict[Risk, int] = {"low": 0, "medium": 1, "high": 2}
QUICK_CONFIDENCE: dict[Risk, float] = {"low": 0.3, "medium": 0.5, "high": 0.7}
MAX_ITEMS = 3
ML_TRUST_THRESHOLD = 0.55  # only use ML signal if confidence > this


def _build(risk: Risk, content: dict, confidence: float, lang: Lang, mode: str,
           ml_confidence: float | None = None, top_tokens: list | None = None) -> TriageOut:
    return TriageOut(
        risk=risk,
        scam_type=content["scam_type"],
        reasons=content["reasons"][:MAX_ITEMS],
        next_steps=content["next_steps"][:MAX_ITEMS],
        confidence=confidence,
        lang=lang,
        mode=mode,
        show_helpline=risk == "high",
        ml_confidence=ml_confidence,
        top_tokens=top_tokens or [],
    )


def fuse(rule: RuleResult, llm: LlmOut | None, ml: MlResult | None, lang: Lang) -> TriageOut:
    """Combine rule floor, ML classifier, and model output — 3-signal fusion.

    Priority: rule floor is never lowered. ML can raise risk if confident.
    Gemini provides explanations. ML provides confidence + explainability.
    """
    # Determine ML-influenced floor
    ml_floor = ml.risk if (ml and ml.confidence >= ML_TRUST_THRESHOLD) else "low"
    ml_conf = ml.confidence if ml else None

    # Combined floor: max of rules and ML
    effective_floor_rank = max(RANK[rule.floor], RANK[ml_floor])
    effective_floor: Risk = next(r for r, v in RANK.items() if v == effective_floor_rank)

    if llm is None:
        # Quick mode: rules + ML only, no Gemini explanation
        category = rule.top_category if rule.floor != "low" else None
        quick_risk = effective_floor
        return _build(quick_risk, get_fallback(category, lang),
                      QUICK_CONFIDENCE.get(quick_risk, 0.3), lang, "quick",
                      ml_confidence=ml_conf)

    # Full mode: consider all three signals
    if rule.known_script or (ml and ml.confidence >= ML_TRUST_THRESHOLD):
        risk = max(effective_floor, llm.risk, key=RANK.get)
    else:
        risk = llm.risk

    content = llm.model_dump()
    if RANK[llm.risk] < RANK[risk]:
        fb = get_fallback(rule.top_category, lang)
        content = {**fb, "reasons": [fb["reasons"][0], *llm.reasons]}

    return _build(risk, content, llm.confidence, lang, "full", ml_confidence=ml_conf)
```

### 8.3 Updated `backend/app/routes/triage.py`

```python
from fastapi import APIRouter, Query, Request

from app import llm
from app.classifier import get_classifier
from app.fuse import fuse
from app.limiter import limiter, rate_limit
from app.rules import evaluate
from app.schemas import ErrorOut, TriageIn, TriageOut

router = APIRouter()


@router.post(
    "/api/triage",
    response_model=TriageOut,
    responses={422: {"model": ErrorOut}, 429: {"model": ErrorOut}, 500: {"model": ErrorOut}},
)
@limiter.limit(rate_limit)
async def triage(request: Request, body: TriageIn, explain: bool = Query(False)) -> TriageOut:
    """Normalize, rule-check, ML-classify, ask Gemini, then fuse into one validated answer."""
    # Signal 1: Rules
    rule = evaluate(body.text)
    hints = [f"{category}:{group}" for category, group in rule.matched]

    # Signal 2: ML classifier (sync, fast ~50ms)
    classifier = get_classifier()
    ml = classifier.predict(body.text) if classifier else None

    # Signal 3: Gemini LLM (async, slower ~2-8s)
    llm_result = await llm.analyze(body.text, body.lang, hints)

    # Fuse all three signals
    result = fuse(rule, llm_result, ml, body.lang)

    # Optional: LIME explanation (expensive, on-demand only)
    if explain and ml and ml.confidence > 0.6:
        from app.explainer import explain as lime_explain
        result.top_tokens = lime_explain(body.text, num_features=6)

    request.state.log_extra = (
        f"lang={result.lang} risk={result.risk} mode={result.mode} "
        f"ml_conf={result.ml_confidence}"
    )
    return result
```

### 8.4 Updated `backend/app/schemas.py` (Add ML Fields)

Add these fields to `TriageOut`:

```python
class TriageOut(LlmOut):
    """Final server response after 3-signal fusion."""
    lang: Lang
    mode: Mode
    show_helpline: bool
    ml_confidence: float | None = Field(None, description="ML classifier confidence 0..1, null if unavailable.")
    top_tokens: list[dict] = Field(default_factory=list, description="LIME token importance weights.")
```

### 8.5 Updated `requirements.txt`

Add these dependencies:

```
onnxruntime>=1.18,<2.0
numpy>=1.26,<3.0
lime>=0.2.0
huggingface-hub>=0.24
```

**Size impact on Render:**
- `onnxruntime` (CPU wheel): ~15 MB installed
- `numpy`: already a transitive dep
- `lime`: ~200 KB
- `huggingface-hub`: ~500 KB

---

## 9. Phase 6 — Frontend Integration

**Time estimate: 1.5 hours**

### 9.1 Updated API Types (`frontend/src/lib/api.ts`)

Add to `TriageResult` interface:

```typescript
export interface TriageResult {
  // ... existing fields ...
  ml_confidence: number | null;
  top_tokens: TokenImportance[];
}

export interface TokenImportance {
  token: string;
  weight: number;
  direction: "suspicious" | "legitimate";
}
```

### 9.2 ML Confidence Badge in `ResultCard.tsx`

Add a small badge showing "ML: 94% confident" below the existing risk badge:

```tsx
{result.ml_confidence !== null && (
  <div className="flex items-center gap-2 text-sm text-slate-600">
    <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-slate-100 
                     border border-slate-200 text-xs font-mono">
      ML {(result.ml_confidence * 100).toFixed(0)}%
    </span>
    <span>{t("ml_confidence_label")}</span>
  </div>
)}
```

### 9.3 Token Highlights Component (New)

Create `frontend/src/components/TokenHighlights.tsx`:

A horizontal bar showing the top contributing tokens with color-coded weights. This is the visual "Responsible AI" proof for judges:

- Suspicious tokens: red background, opacity = weight
- Legitimate tokens: green background, opacity = weight
- Rendered as a row of `<span>` tags with rounded corners

### 9.4 i18n Keys

Add to all three language files (mr.json, hi.json, en.json):

```json
{
  "ml_confidence_label": "AI classifier confidence",
  "token_highlights_title": "Why this was flagged",
  "token_highlight_suspicious": "suspicious indicator",
  "token_highlight_legitimate": "safe indicator"
}
```

---

## 10. Phase 7 — Evaluation & Results Artifact

**Time estimate: 1 hour**

### 10.1 Evaluation Script

Create `backend/scripts/evaluate_classifier.py`:

Runs the quantized ONNX model against the held-out test set and generates:
1. Overall accuracy, F1, precision, recall
2. Per-language breakdown
3. Confusion matrix (saved as PNG)
4. Comparison table: Rules-only vs ML-only vs Rules+ML vs Rules+ML+Gemini
5. Failure analysis: list the messages ML got wrong

### 10.2 Results Document

Create `EVALUATION.md` at project root — this is what judges read:

```markdown
# Sajag — Model Evaluation Results

## Custom MuRIL Scam Classifier

| Metric | Value |
|---|---|
| Model | google/muril-base-cased (fine-tuned) |
| Training data | 4,074 messages (mr, hi, hinglish, en) |
| Test data | 873 messages (held-out) |
| Accuracy | X% |
| F1 (scam) | X% |
| Precision (scam) | X% |
| Recall (scam) | X% |

## Per-Language Performance
| Language | Samples | F1 |
|---|---|---|
| Marathi | X | X% |
| Hindi | X | X% |
| Hinglish | X | X% |
| English | X | X% |

## Comparison: Signal Pipeline Performance
| Configuration | Accuracy | F1 | Latency (p95) |
|---|---|---|---|
| Rules only | X% | X% | <5ms |
| ML only | X% | X% | ~50ms |
| Rules + ML | X% | X% | ~50ms |
| Rules + ML + Gemini | X% | X% | ~2.5s |

## Confusion Matrix
![Confusion Matrix](confusion_matrix.png)

## Key Findings
1. ...
2. ...
3. ...
```

### 10.3 README Update

Add a "Custom ML Classifier" section to the README with the key metrics and a link to EVALUATION.md.

---

## 11. Phase 8 — Deployment

**Time estimate: 1 hour**

### 11.1 Render Deployment Strategy

**Option A (Recommended): Hugging Face Hub download at startup**

1. Upload quantized model to a free Hugging Face Hub repo: `your-team/sajag-scam-classifier`
2. In `classifier.py`, download at first request using `huggingface_hub.hf_hub_download()`
3. Cache in `/tmp/sajag_model/` (persists until container restart)
4. Add `HF_MODEL_REPO` env var to Render

**Pros:** No Git LFS needed, model versioned separately, Render slug stays small.

**Option B: Bundle in Docker image**

1. Add model files to `backend/model/` folder
2. Use `.gitattributes` + Git LFS for files > 50MB
3. Render builds from repo directly

**Pros:** Simpler, no runtime downloads. **Cons:** Slow builds, large repo.

**Decision: Option A** — cleaner separation, faster deployments, free Hugging Face hosting.

### 11.2 Updated `render.yaml`

Add environment variables:

```yaml
envVars:
  - key: HF_MODEL_REPO
    value: "your-team/sajag-scam-classifier"
  - key: ML_ENABLED
    value: "true"
```

### 11.3 Startup Verification

Add a model status field to the health endpoint:

```python
@router.get("/api/health")
def health():
    classifier = get_classifier()
    return {
        "status": "ok",
        "ml_model": "loaded" if classifier else "unavailable",
    }
```

---

## 12. File Manifest

All files created or modified by this plan:

### New Files
| File | Purpose |
|---|---|
| `backend/scripts/prepare_dataset.py` | Merge, clean, split datasets |
| `backend/scripts/train_classifier.ipynb` | Colab training notebook |
| `backend/scripts/evaluate_classifier.py` | Post-training evaluation script |
| `backend/app/classifier.py` | ONNX model loader and predictor |
| `backend/app/explainer.py` | LIME token explainability |
| `backend/data/ml_dataset/train.csv` | Training split |
| `backend/data/ml_dataset/val.csv` | Validation split |
| `backend/data/ml_dataset/test.csv` | Test split |
| `backend/model/config.json` | Model config (id2label, num_labels) |
| `backend/model/tokenizer_config.json` | Tokenizer config |
| `backend/model/vocab.txt` | MuRIL vocabulary |
| `backend/model/special_tokens_map.json` | Special tokens |
| `frontend/src/components/TokenHighlights.tsx` | Token importance display |
| `EVALUATION.md` | Published evaluation results |

### Modified Files
| File | Change |
|---|---|
| `backend/app/fuse.py` | 3-signal fusion (add ML signal) |
| `backend/app/schemas.py` | Add `ml_confidence`, `top_tokens` to TriageOut |
| `backend/app/routes/triage.py` | Add ML classifier call + optional LIME |
| `backend/requirements.txt` | Add onnxruntime, numpy, lime, huggingface-hub |
| `frontend/src/lib/api.ts` | Add ML fields to TriageResult type |
| `frontend/src/components/ResultCard.tsx` | Add ML confidence badge |
| `frontend/src/i18n/mr.json` | Add ML-related i18n keys |
| `frontend/src/i18n/hi.json` | Add ML-related i18n keys |
| `frontend/src/i18n/en.json` | Add ML-related i18n keys |
| `render.yaml` | Add HF_MODEL_REPO env var |
| `README.md` | Add Custom ML Classifier section |

### Files NOT Modified (Preserved)
- `backend/app/rules.py` — untouched, still the first signal
- `backend/app/llm.py` — untouched, still the third signal
- `backend/app/links.py` — untouched
- `backend/app/media.py` — untouched
- All existing tests — preserved; new tests added

---

## 13. Risk Register

| Risk | Severity | Mitigation |
|---|---|---|
| **Quantized ONNX model > 150 MB, won't fit Render** | HIGH | Switch to DistilBERT multilingual (~45 MB quantized). Pre-validated as fallback. |
| **Colab T4 not available (quota exhausted)** | MEDIUM | Use CPU runtime (slower: ~20 min training). Or use Kaggle free T4. |
| **MuRIL accuracy < 85% on test set** | MEDIUM | Add 2 more training epochs; try class weights; augment data with paraphrases via Gemini. |
| **LIME too slow for demo (> 2s per request)** | LOW | Reduce `num_samples` from 200 to 100; only run on-demand via `?explain=true`. |
| **Model download fails on Render cold start** | LOW | Bundle a fallback: if HF download fails, classifier returns None and system degrades gracefully to 2-signal mode (existing behavior). |
| **Git LFS quota issues** | LOW | Use HF Hub hosting instead of Git LFS. Free, unlimited for small models. |

---

## 14. Time Budget

| Phase | Task | Hours |
|---|---|---|
| 1 | Data preparation (merge, clean, split, entity masking) | 1.5 |
| 2 | Model training on Colab (setup, train, evaluate, iterate) | 2.5 |
| 3 | Explainability module (LIME integration) | 1.5 |
| 4 | ONNX export & quantization | 1.0 |
| 5 | Backend integration (classifier.py, fuse v2, triage route, schemas) | 2.0 |
| 6 | Frontend integration (ML badge, token highlights, i18n) | 1.5 |
| 7 | Evaluation document (results, charts, comparison table) | 1.0 |
| 8 | Deployment (HF Hub upload, Render config, health check) | 1.0 |
| | **Buffer for debugging & iteration** | **1.5** |
| | **Total** | **13.5 hours** |

### Critical Path

```
Data prep (1.5h) → Training (2.5h) → ONNX export (1h) → Backend integration (2h) → Deploy (1h)
                                                        ↘ Explainability (1.5h) → Frontend (1.5h)
                                                        ↘ Evaluation doc (1h)
```

Phases 3, 6, 7 can run in parallel with Phase 5. **Minimum viable path (no LIME, no frontend highlights): 8.5 hours.**

---

## Post-Implementation Checklist

- [ ] `prepare_dataset.py` runs without errors; splits saved
- [ ] Training notebook runs end-to-end on Colab T4
- [ ] Test set F1 > 87%
- [ ] Per-language F1 > 80% for all 4 languages
- [ ] ONNX export succeeds; quantized model < 150 MB
- [ ] `classifier.py` loads model and returns predictions locally
- [ ] Fusion v2 passes all existing tests (no regression)
- [ ] New tests cover: ML signal integration, ML unavailable fallback, ML+rules agreement/disagreement
- [ ] LIME explains top-6 tokens for a scam message in < 500ms
- [ ] Frontend shows ML confidence badge
- [ ] Frontend shows token highlights when available
- [ ] Render deployment loads model on cold start
- [ ] Health endpoint reports `ml_model: loaded`
- [ ] EVALUATION.md has all charts and metrics
- [ ] README updated with Custom ML Classifier section
- [ ] Demo scenario works: paste a Marathi scam message → see risk + ML confidence + highlighted tokens


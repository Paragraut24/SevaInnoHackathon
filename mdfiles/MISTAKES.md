# Mistake Log

### Pre-push secret hook self-matched its own regex
**Problem:** `.githooks/pre-push` blocked the initial push with "Potential secret detected in tracked files" because `git grep` scanned `.githooks/pre-push` itself, matching the `GEMINI_API_KEY` and `SIGHTENGINE_API_SECRET` pattern regex tokens in the script.
**Context:** `.githooks/pre-push` line 9 during first push of `feat/mvp-scaffold`.
**Solution:** Added `':!.githooks/pre-push'` to the `git grep` pathspec exclusion list so the hook does not scan its own pattern string.
**Date:** 2026-11-11


### Gemini full Flash models time out (>10-25s) on Interactions API Free Tier
**Problem:** `gemini-3.8-flash`, `gemini-3.7-flash`, `gemini-3.6-flash`, and `gemini-3.5-flash` hit client-side `APITimeoutError` at 10-25s on `client.interactions.create` (breaking the <6s p95 budget), while `gemini-2.5-flash` and `gemini-flash-latest` returned `404 NotFoundError`.
**Context:** Phase 0.4 Gemini smoke test in `backend/scripts/smoke_gemini.py` and `backend/app/config.py`.
**Solution:** Default `GEMINI_MODEL` to `gemini-3.5-flash-lite` (completed Marathi structured JSON in ~2.3s; `gemini-3.1-flash-lite` also succeeded in ~2.6s). Keep `GEMINI_MODEL` env-configurable so it can be swapped without code changes.
**Date:** 2026-11-11


### `pip install --target --upgrade` wiped `google/genai` namespace subpackage
**Problem:** Installing `onnxruntime` and `huggingface-hub` into `backend/.venv/Lib/site-packages` with `--target --upgrade` pulled `protobuf`, replacing the shared `google/` directory and deleting `google/genai` and `google/auth`.
**Context:** Phase B dependency installation in `backend/.venv` (which lacks its own `pip` binary), discovered during Phase D `pytest` (`ImportError: cannot import name 'genai' from 'google'`).
**Solution:** Staged `google-genai` and `google-auth` (`--no-deps`) into a temporary directory and merge-copied `google/*` back into `backend/.venv/Lib/site-packages/google/` alongside `protobuf`.
**Date:** 2026-11-25


### Post-mask deduplication skew and Railway PNR 10-digit numbers
**Problem:** Unifying URL/phone masking caused 605 scam templates to collapse to identical strings (`44.1%` scam, just below the `45-55%` Gate B band), while a naive `\d{10}` check flagged 37 legitimate Railway PNR numbers in `ham` messages.
**Context:** Phase B `backend/scripts/prepare_dataset.py` Gate B validation after integrating `app.normalize.preprocess_for_ml`.
**Solution:** Added deterministic per-language ham downsampling (`HAM_MAX_RATIO_TO_SCAM = 1.08`, yielding `48.1%` scam across 3,632 unique rows) and kept `PHONE_RE` (`[6-9]\d{9}`) as the phone-leak assertion while logging non-mobile 10-digit rows (`32`) in `metadata.json`.
**Date:** 2026-11-25

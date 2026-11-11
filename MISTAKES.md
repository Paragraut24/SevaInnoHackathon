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

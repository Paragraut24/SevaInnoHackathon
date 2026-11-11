# Mistake Log

### Pre-push secret hook self-matched its own regex
**Problem:** `.githooks/pre-push` blocked the initial push with "Potential secret detected in tracked files" because `git grep` scanned `.githooks/pre-push` itself, matching the `GEMINI_API_KEY` and `SIGHTENGINE_API_SECRET` pattern regex tokens in the script.
**Context:** `.githooks/pre-push` line 9 during first push of `feat/mvp-scaffold`.
**Solution:** Added `':!.githooks/pre-push'` to the `git grep` pathspec exclusion list so the hook does not scan its own pattern string.
**Date:** 2026-11-11

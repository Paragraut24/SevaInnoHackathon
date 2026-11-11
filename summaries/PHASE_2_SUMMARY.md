# Phase 2 Summary — Feature Breadth

**Date:** 2026-11-11  
**Branch:** `feat/phase-2` (branched from `feat/triage-core`)  
**Commit:** `91264f8`

---

## What Was Built

### 2.1 Frontend Routing
- Installed `react-router-dom` and wrapped the app in `<BrowserRouter>`.
- Five routes: `/` (Check), `/safe-word`, `/scammed`, `/media`, `/dashboard`.
- Heavy pages (SafeWord, Scammed, Media, Dashboard) are **lazy-loaded** with `React.lazy` + `<Suspense>`, code-splitting jsPDF and QRCode out of the initial bundle.
- Sticky nav header with `<NavLink>` active state highlighting.

### 2.2 Safe Word (`lib/safeWord.ts`, `pages/SafeWord.tsx`)
- **100% client-side, no network, offline capable.**
- Generates a random adjective+noun phrase from trilingual word banks (Marathi/Hindi/English).
- Picks a random challenge question from language-specific banks.
- Displays a QRCode SVG (`qrcode.react` named export `QRCodeSVG`).
- Copy-to-clipboard button with 2s feedback.

### 2.3 Scammed Flow (`pages/Scammed.tsx`, `lib/pdf.ts`)
- **4-step stepper** with progress bar: (1) Call 1930 → (2) Collect evidence → (3) Portal guide → (4) Incident PDF.
- Evidence checklist with checkboxes (screenshots, transaction details, contact info, messages).
- Portal step lists exact steps for `cybercrime.gov.in` with a direct link.
- **Incident PDF** via `jsPDF`: plain-Latin summary with date, amount, account, phone, description, evidence list. Falls back to `window.print()` on failure.
- Explicit disclaimer that the PDF has no official status.

### 2.4 Link + Number Check (`app/links.py`, `app/routes/link_check.py`)
- **Offline only, no network calls.**
- `POST /api/link-check` accepts any text, extracts URLs and phone numbers via existing `normalize.py`.
- URL flags: `blocklisted_domain` (10 known scam domains in `blocklist.json`), `url_shortener` (13 shortener domains), `punycode_idn`, `unusual_tld_*`, `lookalike_<brand>` (Levenshtein ≤ 2 to 25 Indian brands/banks/services).
- Phone flags: `not_valid_indian_mobile`.
- Never says a URL is "safe" — returns empty flags list or named flags.

### 2.5 Media Check (`app/media.py`, `app/routes/media_check.py`)
- **Band system**: `unlikely` / `unclear` / `possible_synthetic` / `could_not_check`.
- Image: Sightengine `genai` model, scores AI-generated likelihood.
- Audio: HF Inference API (`facebook/wav2vec2-base`), looks for spoof label in classifier output.
- 450/day rolling counter (resets on process restart). Past limit → `could_not_check`.
- Temp file **always deleted** in `finally` block.
- Words "real", "fake", "genuine", "authentic", "deepfake" are **banned** from all band strings (enforced by `test_media.py`).
- Always includes `limits_note`.

### 2.6 Mock Dashboard (`data/dashboard_sample.json`, `app/routes/dashboard.py`, `pages/Dashboard.tsx`)
- `GET /api/dashboard` returns static synthetic data with `"sample": true`.
- Frontend shows an amber "Sample data" banner when `sample` is true.
- Summary cards (total, resolved, pending), category bar chart (custom CSS bars, no charting library), monthly trend bars, district table.

---

## Files Changed / Created

| File | Change |
| --- | --- |
| `backend/app/links.py` | New — offline URL/phone flag checker |
| `backend/app/media.py` | New — Sightengine + HF audio adapter |
| `backend/app/routes/link_check.py` | New — POST /api/link-check |
| `backend/app/routes/media_check.py` | New — POST /api/media-check |
| `backend/app/routes/dashboard.py` | New — GET /api/dashboard |
| `backend/app/main.py` | Wired 3 new routers |
| `backend/data/blocklist.json` | New — 10 known scam domains |
| `backend/data/brands.json` | New — 25 Indian brands for lookalike check |
| `backend/data/dashboard_sample.json` | New — synthetic district data |
| `backend/requirements.txt` | Added `python-multipart`, `pytest-asyncio` |
| `backend/tests/test_links.py` | New — 7 URL/phone flag tests |
| `backend/tests/test_media.py` | New — 5 band logic + no-forbidden-word tests |
| `frontend/src/main.tsx` | Added `<BrowserRouter>` |
| `frontend/src/App.tsx` | Full rewrite — routing + nav + lazy loading |
| `frontend/src/pages/SafeWord.tsx` | New |
| `frontend/src/pages/Scammed.tsx` | New |
| `frontend/src/pages/Media.tsx` | New |
| `frontend/src/pages/Dashboard.tsx` | New |
| `frontend/src/lib/safeWord.ts` | New |
| `frontend/src/lib/pdf.ts` | New |
| `frontend/src/i18n/{mr,hi,en}.json` | +60 keys each for Phase 2 UI |
| `frontend/package.json` | Added `react-router-dom`, `jspdf`, `qrcode.react` |

---

## Test Results

| Suite | Tests | Result |
| --- | --- | --- |
| All backend tests | 65/65 | PASS (0.48s) |
| Frontend build (tsc + vite) | — | PASS, code-split bundles |

---

## Problems Faced & Solutions

| Problem | Solution |
| --- | --- |
| `python-multipart` missing from venv (no pip exe in venv scripts) | Installed via `python -m pip install --target <venv/site-packages>` |
| `qrcode.react` has no default export — only named `QRCodeSVG`, `QRCodeCanvas` | Changed import to `import { QRCodeSVG } from "qrcode.react"` |
| `result.reason` typed `unknown` in JSX short-circuit rendered as child | Defined `MediaResult` interface with typed fields; `String(result.reason)` for safe render |
| jsPDF bundle too large in main chunk (769 kB) | Lazy-loaded Scammed page with `React.lazy` — Scammed chunk is now separate (397 kB), main chunk 342 kB |

---

## Gate 2 Checklist

| Item | Status |
| --- | --- |
| All routes navigate correctly | Manual — start both servers, click through all 5 nav links |
| Safe word generates phrase + QR code offline | Manual — works without network |
| Scammed flow reaches PDF download step | Manual |
| Link check flags bit.ly and blocklisted domains | Covered by `test_links.py` |
| Media check returns band + limits_note; never says "real"/"fake" | Covered by `test_media.py` |
| Dashboard shows "Sample data" banner | Manual — load `/dashboard` |
| 65/65 backend tests pass | DONE |
| Frontend builds without errors | DONE |

---

## Next: Phase 3 — Hardening & Evaluation

- Run `testset/eval.py` with Gemini against the local backend (target 34/40, ≤3 false alarms).
- Fix top misses in rules or prompt.
- Deploy to Vercel (frontend) + Render (backend).
- Two real phones: Chrome and Safari, PWA install, contrast, `ReadAloud` via Web Speech API.
- Privacy drill: scan logs for message content after a full test run.

Previous summary: [PHASE_1_SUMMARY.md](../backend/../summaries/PHASE_1_SUMMARY.md)

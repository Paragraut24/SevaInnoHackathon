# Phase 0 Summary — Foundations & Scaffolding

Connected to: [Build Plan.md](../Build%20Plan.md), [Phase 1 Plan.md](../Phase%201%20Plan.md), [TRD.md](../TRD.md)

## What Was Built
1. **Repository & Secret Hygiene:** Initialized git on `feat/mvp-scaffold`, added [.gitignore](../.gitignore), [.env.example](../.env.example), and [.githooks/pre-push](../.githooks/pre-push) (blocking `.env` tracking or leaked key prefixes).
2. **Backend Scaffold (`backend/`):**
   - [config.py](../backend/app/config.py): `Settings` (`pydantic-settings`) loading root `.env`.
   - [schemas.py](../backend/app/schemas.py): `TriageIn`, flat `LlmOut` (no `$defs`/`$ref`), `TriageOut`, `ErrorOut`, `HealthOut`.
   - [main.py](../backend/app/main.py): Stateless FastAPI app with CORS from `ALLOWED_ORIGIN`, `x-request-id` + metadata-only logging middleware (`req`, `method`, `path`, `status`, `latency_ms` — never request content), and `GET /api/health`.
   - [smoke_gemini.py](../backend/scripts/smoke_gemini.py): Calls `client.interactions.create` on `gemini-3.8-flash` with `store=False`, `generation_config={"thinking_level": "low"}`, and JSON-schema `response_format`.
   - [test_health.py](../backend/tests/test_health.py): Checks `/api/health`, `x-request-id`, and flat `LlmOut` schema.
   - Installed 49 Python packages into `backend/.venv`.
3. **Frontend PWA Shell (`frontend/`):**
   - Vite + React 19 + TypeScript + Tailwind CSS v4 (`@tailwindcss/vite`), `react-i18next` defaulting to Marathi (`mr`) with `hi` and `en` toggles ([i18n/index.ts](../frontend/src/i18n/index.ts), [App.tsx](../frontend/src/App.tsx)).
   - First-load privacy notice disclosing Gemini Free Tier terms, clickable `tel:1930` helpline banner, and offline shell PWA ([manifest.webmanifest](../frontend/public/manifest.webmanifest), [sw.js](../frontend/public/sw.js)).
   - Installed 88 npm packages into `frontend/node_modules` (0 vulnerabilities).
4. **Seed Datasets & 40-Message Test Set (`datasets/`, `testset/`):**
   - Fetched MIT-licensed Indian multilingual scam/ham rows into `datasets/` ([datasets/README.md](../datasets/README.md)) and curated [testset/messages.csv](../testset/messages.csv) (40 rows: 20 `scam` / 20 `genuine`, `14 mr / 13 hi / 13 en`, `30 dev / 10 holdout`, zero PII).

## Problems Faced & How They Were Solved
- **Machine-translated dataset quality & GPL risk:** `dbarbedillo/SMS_Spam_Multilingual_Collection_Dataset` used GPL and noisy UK/Singapore M2M100 translations. Solved by using MIT-licensed `anmolshrivastav/scam_ham_india_14_languages` + Apache-2.0 `chinna887/Indian_Cyber_Scam_PhoneCall_Hinglish_Dataset` + Maharashtra Cyber / Mahavitaran advisories.
- **Gemini Interactions API breaking change:** Official `gemini-api-docs-mcp` showed `response_mime_type` is removed from `interactions.create` and `temperature` is deprecated on Gemini 3.8 Flash. Solved by placing `"mime_type": "application/json"` inside `response_format`, using `thinking_level="low"`, `store=False`, and `interaction.output_text`.
- **`npm --prefix` path error:** `npm --prefix frontend install` tried reading root `package.json`. Solved by running `npm install` inside `frontend/`.

## Phase 0 Verification (Completed)
- **Backend unit tests (`pytest backend/tests`):** 2 passed (`test_health_ok_and_request_id`, `test_llm_out_schema_is_flat`).
- **Frontend build (`npm run build` in `frontend/`):** TypeScript + Vite build succeeded (`dist/` generated in 932 ms).
- **Sightengine Free Tier key:** `GET /1.0/check.json` with `models=genai,deepfake` returned HTTP `200` (`api_status: success`).
- **Gemini smoke test (`backend/scripts/smoke_gemini.py`):** Switched default `GEMINI_MODEL` from `gemini-3.8-flash` (which timed out at >15–25 s along with `3.7`/`3.6`/`3.5-flash`) to `gemini-3.5-flash-lite`, which returned schema-valid Marathi `LlmOut` JSON in ~2.3 s.
- **Remaining manual cloud step (0.5):** Deploy `frontend/` to Vercel and `backend/` to Render/Railway using your `.env` secrets and set `ALLOWED_ORIGIN` to the Vercel URL, then proceed to [Phase 1 Plan.md](../Phase%201%20Plan.md).


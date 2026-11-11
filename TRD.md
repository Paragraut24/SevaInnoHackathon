# Technical Requirements (TRD)

Sajag runs as a stateless web app plus a small API: rules and the Gemini API produce the risk answer, nothing user-supplied is stored, and every response is validated against a fixed schema before it reaches the screen.

## Stack

| Layer | Choice | Why |
| --- | --- | --- |
| Frontend | React with Vite, Tailwind CSS, installable as a PWA | Fast to build solo; mobile-first; works from a link |
| Backend | FastAPI (Python) | Quick to write, easy file handling for media, typed schemas |
| AI reasoning | Gemini API via `google-genai` Interactions API (configurable `GEMINI_MODEL`, e.g., `gemini-3.8-flash` / `gemini-2.5-flash`) | Free-tier accessible; strong multilingual output; JSON-schema responses |
| Media signal | Sightengine Free Tier (images & extracted video keyframes) + Hugging Face audio deepfake / acoustic heuristic, behind an adapter | Zero-cost within Sightengine free limits (2,000 ops/mo, 500/day); result shown only as a band |
| PDF evidence summary | Client-side `jsPDF` | Fast 2-day build; zero server PDF deps; victim incident details never leave the browser |
| Hosting | Vercel (frontend), Render or Railway (API), free tiers | Public demo link in minutes |
| Secrets | Environment variables on the host; never in the repo | Standard |

## Triage pipeline

1. **Normalize.** Trim, detect script (Devanagari or Latin), extract URLs and phone numbers.
2. **Rule engine.** Pattern lists in Marathi, Hindi and English for urgency, secrecy, money requests, impersonated authorities (police, CBI, bank, courier) and known scam scripts. Output: rule score, matched patterns.
3. **Link features.** Domain age is not available offline, so check lookalike distance against a short list of common brands and banks, URL shorteners, punycode, and suspicious TLDs.
4. **LLM reasoning.** Send the message, rule hints and target language to the Gemini Interactions API (`client.interactions.create`) with a strict system instruction; require JSON matching the response schema.
5. **Validate and fuse.** Reject any response that fails the schema and retry once. Final risk is the higher of the rule risk and the model risk when the rules match a known scam script; otherwise the model risk, never below Low.
6. **Respond** and drop the input from memory.

## API contracts

| Endpoint | Request | Response |
| --- | --- | --- |
| `POST /api/triage` | `{text, lang}` where lang is `mr`, `hi` or `en` | `{risk, scam_type, reasons[≤3], next_steps[≤3], confidence, lang}` |
| `POST /api/link-check` | `{url, lang}` | `{risk, flags[], notes, lang}` |
| `POST /api/media-check` | multipart file, `lang`; image/screenshot, audio ≤ 60 s, or video ≤ 30 s | `{band, limits_note, lang}` where band is `unlikely`, `unclear` or `possible_synthetic` |
| `POST /api/safe-word` | `{lang}` | `{phrase, challenge_question, share_text}` |
| Client-side PDF (`jsPDF`) | user-entered incident fields in browser | Downloaded PDF (no server request) |
| `GET /api/dashboard` | none | Static synthetic district data with `sample: true` |
| `GET /api/health` | none | `{status}` |

All errors return `{error_code, message}` with a localized message; no stack traces.

## Data model

There is no database in the MVP. Request data lives only in memory for the duration of the call. The only persisted data are static files: the scam pattern lists, the brand and bank lookalike list, the seeded number blocklist, the localized UI strings and the synthetic dashboard JSON. Operational logs hold request id, route, latency, status code, language and risk level, never the content.

## Non-functional requirements

| Area | Requirement |
| --- | --- |
| Latency | Triage p95 under 6 s; media check under 15 s |
| Availability | Demo-grade; a graceful fallback to rules-only results if the Gemini API fails or times out |
| Limits | Message text up to 2,000 characters; files up to 10 MB; 20 requests per minute per IP |
| Security | HTTPS only; CORS restricted to the app origin; file type and size checks; uploaded files deleted immediately after analysis |
| Privacy | No content stored or logged; no third-party analytics; clear notice in the UI |
| Accessibility | Large text, high contrast, voice-read-aloud of results via the browser speech API where available |
| Localization | All UI strings and AI outputs in Marathi, Hindi and English; fallback to English |
| Browser support | Current Chrome and Safari on Android and iOS |

## Configuration

Environment variables: `GEMINI_API_KEY`, `GEMINI_MODEL`, `SIGHTENGINE_API_USER`, `SIGHTENGINE_API_SECRET`, `HF_TOKEN` (optional, for Hugging Face audio inference), `ALLOWED_ORIGIN`, `RATE_LIMIT_PER_MIN`. A `.env.example` file lists them without values.

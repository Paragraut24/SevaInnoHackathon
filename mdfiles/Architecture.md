# Technical Architecture

Sajag is a thin web app in front of one stateless API: rules set a risk floor, Gemini explains the result in the user's language, and a schema check gates every answer.

## System diagram

&#91;embedded content: system architecture · 3 columns, 1 control point\]

A text check runs steps 1 to 5 top to bottom; a file upload takes the separate media route. The privacy rule applies to everything the API receives.

## Components

| Component | Responsibility | Notes |
| --- | --- | --- |
| Web app (PWA) | Language toggle (Marathi default), input screens, result cards, safe word, scammed flow (`jsPDF`), mock dashboard | Holds no user content after a check; read-aloud via browser speech |
| API gateway layer | CORS, rate limit, size and type checks, request id | Same FastAPI app; middleware only |
| Normalizer | Detects script, extracts links and phone numbers | Pure functions; unit tested |
| Rule engine | Matches known scam scripts and urgency, secrecy and payment cues in Marathi, Hindi and English | Pattern lists in versioned JSON; sets the risk floor |
| Link checks | Lookalike distance to common brands and banks, shorteners, punycode, odd TLDs | Offline checks only; says so when it cannot verify |
| Gemini reasoning | Produces scam type, reasons and next steps in the chosen language (`google-genai` Interactions API) | Strict system instruction; JSON schema; one retry on invalid output |
| Validate and fuse | Rejects invalid output, applies the rule floor, builds the final response | Falls back to rules-only text if Gemini fails |
| Media adapter | Wraps Sightengine Free Tier (images & extracted video keyframes) plus HF audio/heuristic fallback; maps scores to three bands | Never returns real or fake; always includes a limits note |
| Static data | Pattern lists, brand list, blocklist, UI strings, sample dashboard data | Shipped with the app; no database |

## Failure handling

- **Gemini API slow or down:** return a rules-only answer after 8 seconds, labelled "quick check", with the same next steps.
- **Invalid model output:** retry once, then fall back to rules-only.
- **Media detector unavailable:** show "could not check this file" and the safe word flow, never a guess.
- **Oversized or wrong file type:** reject before any processing, with a localized message.

## Deployment

Frontend on Vercel, API on Render or Railway, both on free tiers, with the API key in the host's environment settings. Production and demo are the same environment for the MVP. A Telegram or WhatsApp channel would call the same `/api/triage` route, which is why the API is kept channel-agnostic.

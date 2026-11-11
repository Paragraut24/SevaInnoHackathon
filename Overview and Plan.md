# Sajag — MVP Documentation Pack

Nov 11, 2026 · @Parag

Sajag (working title) is a multilingual web app that helps ordinary Indians verify suspicious calls, messages and media before they act, scoped as a two-day solo MVP for the Seva First Innovation Challenge Maharashtra.

## Problem and solution

Indians lost about ₹19,800 crore to financial cyber fraud in 2025 across 21.77 lakh complaints, with roughly 77% of it from investment scams ([I4C data via FastBull](https://www.fastbull.com/brokersview/news/indians-lost-over-%E2%82%B9198-billion-to-financial-fraud-in-2025-i4c-ncrp-data-show-319040)), and Maharashtra leads the states in monetary losses ([NewsBytes](https://www.newsbytesapp.com/news/science/this-is-how-much-india-lost-to-cybercrimes-in-6-years/story)). Voice-clone cases are rising too: Haryana's cyber cell reported a 450% jump in late 2025 ([ThreatCluster summary](https://threatcluster.io/cluster/ai-voice-cloning-scams-surge-in-india-124ab5b6)). Detection tools are weakest in regional Indian languages ([Nieman Lab](https://www.niemanlab.org/2025/04/fake-news-detection-ai-is-more-likely-to-fail-in-the-global-south-new-study-shows/)) and on very short clips ([Mint via Magzter](https://www.magzter.com/en/stories/newspaper/Mint-Bangalore/INSIDE-INDIAS-ATTEMPT-TO-TAME-DEEPFAKES)).

Sajag does not try to win the detection arms race. It combines four things that still work when a fake is perfect:

1. **Scam triage.** Paste a message, link or number and get a risk level, plain-language reasons and next steps in Marathi, Hindi or English.
2. **Media check (experimental).** Upload a voice note or video and get a cautious synthetic-media signal with honest low confidence.
3. **Family safe word.** Generate a challenge phrase and a callback checklist so a cloned voice cannot pass a verification step.
4. **I was scammed flow.** Guided steps for the 1930 helpline and the cybercrime portal, with a downloadable evidence summary.

The gap this fills: existing tools verify content or label it; none walk a non-technical person from "this feels wrong" to "here is exactly what to do in the next ten minutes" in their own language.

## MVP scope

| Capability | Status in 2-day build | Notes |
| --- | --- | --- |
| Text, link and phone-number scam triage | Built | Rules plus Gemini reasoning; the core of the demo |
| Marathi, Hindi, English output | Built | Language toggle (Marathi default); Gemini writes the explanation natively |
| Family safe word and callback checklist | Built | Fully client-side; no detection needed |
| I was scammed guide and evidence summary | Built | Static steps plus a client-side `jsPDF` summary the user downloads |
| Voice, video and image synthetic-media signal | Built, labelled experimental | Uses Sightengine Free Tier (images/video keyframes) + Hugging Face audio/heuristics; shows confidence bands, never a verdict |
| District scam dashboard | Mocked | Synthetic sample data, clearly labelled as such |
| WhatsApp or Telegram bot | Shown as deployment path | Slide plus optional Telegram stub if time remains |
| Accounts, payments, native app | Out | Not needed to prove the idea |

## Success criteria and challenge fit

The demo succeeds if a judge can paste a real scam message on their own phone and get a correct, understandable answer in Marathi within five seconds.

- **Accuracy:** at least 85% correct risk level on a 40-message test set of real scam and genuine messages (see Testing and Demo).
- **Speed:** triage answer in under 6 seconds at the 95th percentile.
- **Honesty:** the media check never shows a confident "real" or "fake" verdict.
- **Privacy:** no user uploads or messages stored; stated in the UI and demonstrable in the code.
- **Deployability:** a one-page note on how a district cyber cell or the state innovation society could run it.

The challenge plans 50 awardees across 10 sectors, each eligible for a work order ([Startup Grants India](https://www.startupgrantsindia.com/seva-first-innovation-challenge)), so the pitch frames Sajag as a public service a state department could adopt, not just a student app. The declared category is General, sector Emerging Technologies, sub theme Responsible AI, deepfake detection, cyber resilience and digital trust.

## Pack index and working assumptions

- **PRD:** users, stories, features and acceptance criteria.
- **TRD:** stack, API contracts, data model, non-functional requirements.
- **Architecture:** component diagram and request flow.
- **Access and Permissions:** roles, data rules, rate limits.
- **Roadmap:** the 2-day plan with gates, then post-challenge phases.
- **Testing and Demo:** test set, demo script, pitch outline.
- **Risks and Privacy:** risk register and responsible-AI rules.

Locked decisions: web app first, Gemini API (`google-genai` Interactions API) for reasoning, Marathi (`mr`) as the default demo language, Sightengine Free Tier (images/video keyframes) + free Hugging Face audio/heuristics for experimental media check, client-side PDF (`jsPDF`), a solo builder using Antigravity, and a free-tier host such as Vercel or Render. Competing work to check before pitching: the Misinformation Combat Alliance WhatsApp tipline, which focuses on public-interest deepfakes rather than personal scam protection.

## Sources

Checked 11 November 2026 from search results; figures are as reported by those outlets and should be re-verified before the final pitch.

- [I4C 2025 figures via FastBull](https://www.fastbull.com/brokersview/news/indians-lost-over-%E2%82%B9198-billion-to-financial-fraud-in-2025-i4c-ncrp-data-show-319040)
- [NewsBytes: I4C six-year report, Maharashtra](https://www.newsbytesapp.com/news/science/this-is-how-much-india-lost-to-cybercrimes-in-6-years/story)
- [ThreatCluster: AI voice cloning scams in India](https://threatcluster.io/cluster/ai-voice-cloning-scams-surge-in-india-124ab5b6)
- [Nieman Lab: detection fails more in the Global South](https://www.niemanlab.org/2025/04/fake-news-detection-ai-is-more-likely-to-fail-in-the-global-south-new-study-shows/)
- [Mint via Magzter: Inside India's attempt to tame deepfakes](https://www.magzter.com/en/stories/newspaper/Mint-Bangalore/INSIDE-INDIAS-ATTEMPT-TO-TAME-DEEPFAKES)
- [Startup Grants India: Seva First Innovation Challenge](https://www.startupgrantsindia.com/seva-first-innovation-challenge)

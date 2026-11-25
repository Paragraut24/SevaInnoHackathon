# Product Requirements (PRD)

Sajag's MVP must let a non-technical user in Maharashtra check a suspicious message, link or media file and act on the answer within one minute, in their own language.

## Users and needs

| Persona | Situation | Need |
| --- | --- | --- |
| Family member, 45-70, Marathi or Hindi speaker | Gets a call or voice note from a "relative" or "police officer" asking for money | A simple way to confirm the person is real without technical knowledge |
| Young adult, 18-30 | Receives investment, job or KYC links and sextortion threats | A fast second opinion and steps to report |
| Small shop owner | Gets fake bank or payment messages | A quick check plus guidance on what to do if money left the account |
| Fact-checker or district cyber cell volunteer (later) | Needs patterns, not single cases | Aggregated scam trends by district |

## User stories

1. As a user, I paste a message or link and see a risk level with plain-language reasons in my chosen language.
2. As a user, I upload a voice note or video and see a cautious signal with an explanation of its limits.
3. As a user, I create a family safe word and get a callback checklist I can share by message.
4. As a victim, I follow a guided flow to freeze funds and file a report, and download an evidence summary.
5. As an admin (demo only), I view anonymized trend data by district.

## Features and acceptance criteria

| ID | Feature | Acceptance criteria |
| --- | --- | --- |
| F1 | Scam triage | Returns risk (Low, Medium, High), scam type, up to 3 reasons and up to 3 next steps; output in selected language; p95 latency under 6 s |
| F2 | Link and number checks | Flags lookalike domains, URL shorteners, and numbers matching a seeded local blocklist; says clearly when it cannot check |
| F3 | Media check | Accepts audio up to 60 s, video up to 30 s, and suspicious images/screenshots; returns a signal band (Unlikely, Unclear, Possible synthetic) with a limits note; never says "real" or "fake" |
| F4 | Safe word | Generates a phrase and a challenge question; works offline once loaded; shareable text and QR |
| F5 | Scammed flow | Shows 1930 and cybercrime portal steps in order; generates a downloadable PDF summary from user-entered details |
| F6 | Language | Marathi, Hindi, English; UI strings and AI output both localized |
| F7 | Privacy notice | Plain-language notice on first load; states that nothing is stored |
| F8 | Dashboard (mock) | Charts from labelled synthetic data; visibly marked "Sample data" |

## Non-goals

- Proving that a piece of media is authentic or fake.
- Blocking calls or reading the user's messages automatically.
- Storing user content, user accounts or payment features.
- Legal advice or direct integration with police systems in the MVP.

## Metrics

| Metric | Target for demo |
| --- | --- |
| Triage accuracy on test set | 85% or higher |
| Time to first answer | Under 6 s at p95 |
| Languages working end to end | 3 of 3 |
| Judges who can complete a check unaided | 5 of 5 |

## Open questions

- [x] Default language for the live demo: Marathi (`mr`).
- [ ] Is a Telegram bot stub worth the time if Day 2 runs ahead?
- [x] Media check detector: Sightengine Free Tier (images & extracted video keyframes) + free Hugging Face audio / acoustic heuristic fallback.

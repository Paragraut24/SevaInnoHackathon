# Risks, Privacy and Responsible AI

The biggest risks are time, a wrong or falsely reassuring answer, and a privacy claim that the code cannot back up; each has a concrete control below.

## Risk register

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| Two days is not enough | High | High | Gates and cut list in the Roadmap; core first, extras last |
| Falsely reassuring answer on a real scam | Medium | High | Never say "safe"; Low means "no clear signs found"; always show the safe word and callback step |
| Weak Marathi or Hindi output | Medium | High | Native-speaker review of 10 outputs per language before the demo; prompt includes tone and register rules |
| Media detector is wrong or misleading | High | Medium | Band only, never a verdict; limits note on every result; marked experimental |
| Gemini API slow, down or out of quota | Medium | High | 8-second timeout, rules-only fallback, recorded demo, spare key and quota check on Day 2 |
| Privacy claim fails (a log leaks content) | Low | High | Metadata-only logging by design; privacy test in Session 3; no analytics |
| Prompt injection in pasted messages | Medium | Medium | Quoted-data template, schema validation, rule floor cannot be lowered by the model |
| Scammers probe the tool | Medium | Medium | Rate limits; outputs explain risk but never advise on evasion |
| Overlap with existing helplines such as the fact-checkers' WhatsApp tipline | High | Medium | Position as personal-scam protection with safe word and action steps, not public-interest fact-checking; name them as partners |
| WhatsApp business access takes too long | High | Low | Web app first; channel shown as deployment path |
| Perceived government endorsement or legal advice | Low | Medium | Footer: independent project, not official, not legal advice; 1930 and the portal named as the official routes |

## Responsible AI rules

| Rule | How it shows up |
| --- | --- |
| Be honest about uncertainty | Confidence shown on triage; media check shows bands with a limits note |
| Never claim certainty about media | The words "real" and "fake" do not appear in media results |
| Never declare something safe | Lowest level reads "no clear signs found"; reminder to verify with a trusted contact |
| Explain every result | Up to three plain-language reasons on each answer |
| Keep a human route | 1930 and the cybercrime portal on every High result |
| Protect privacy | No storage of content; stated in the first-load notice |
| Test for language fairness | The 40-message test set is balanced across mr, hi and en; accuracy reported per language |
| Respect accessibility | Large text, high contrast, read-aloud, short sentences |

## Wording rules for results

| Say | Never say |
| --- | --- |
| "High risk: this matches a known digital arrest scam" | "This is a scam" as a legal claim about a named person |
| "No clear signs found. Verify with someone you trust before sending money" | "This is safe" |
| "Possible synthetic voice. We cannot be sure" | "This is fake" or "This is real" |
| "Call 1930 now if money has left your account" | Promises that money will be recovered |

## Open questions for you

- [x] Default language for the live demo: Marathi (`mr`).
- [x] Media check detector: Sightengine Free Tier (images & extracted video keyframes) + free Hugging Face audio / acoustic heuristic fallback.
- [ ] Is a Telegram stub worth building if Session 2 finishes early?
- [ ] Have you already submitted an idea to the challenge, and what is the exact deadline for the next stage? Sources disagree on Maharashtra dates.
- [ ] Who can review Marathi and Hindi outputs before Friday?

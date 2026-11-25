# Testing and Demo Plan

Sajag ships only if the live app gets at least 34 of 40 test messages right, never shows a confident real or fake verdict on media, and holds up through a two-minute demo that can be re-run from a recording.

## Test set

Forty messages, built tonight in Session 0: 20 scams and 20 genuine, spread across Marathi, Hindi and English.

| Group | Count | Sources |
| --- | --- | --- |
| Scam: digital arrest, fake investment, KYC or bank, family emergency, courier, job or lottery, loan app, sextortion | 20 | Public advisories from the government and cyber police; scam examples you or your family received, with names and numbers removed |
| Genuine: bank alerts that warn against sharing OTPs, delivery updates, family chat, government notices, shop messages | 20 | Your own messages with personal details removed; public notices |

A scam is correct if the result is Medium or High; a genuine message is correct if the result is Low. At most 6 misses in total gives the 85% target (34 of 40); aim for no more than 3 false alarms on genuine messages, because false alarms erode trust.

## Test types

| Type | What is checked | When |
| --- | --- | --- |
| Unit | Normalizer, pattern matching, link lookalike scoring | Session 1 and 2 |
| Contract | Every API response validates against its schema; invalid model output triggers one retry then fallback | Session 1 |
| Language | Output language matches the selected language in 10 sampled checks per language | Session 3 |
| Privacy | After a test run, host logs contain no message text, URLs, numbers or file names; uploaded files are gone | Session 3 |
| Failure drills | Simulate a Gemini timeout and a detector outage; confirm the rules-only fallback and "could not check" messages | Session 3 |
| Device | Two real phones, Chrome and Safari; text size, contrast, read-aloud | Session 3 |
| Media honesty | Five audio and five video samples; confirm bands only, never real or fake wording | Session 2 and 3 |

## Demo script (2 minutes)

| Time | Show | Say |
| --- | --- | --- |
| 0:00 | Title and one statistic | India lost about ₹19,800 crore to cyber fraud in 2025; Maharashtra leads in losses |
| 0:15 | Paste a Marathi digital-arrest message | Result in seconds, reasons and steps in Marathi |
| 0:45 | Paste a link and a phone number | Lookalike flagged; clear when it cannot check |
| 1:00 | Upload a short voice note | Honest "unclear" band: detectors fail on Indian languages, so we do not pretend |
| 1:20 | Create a family safe word | The step that works even against a perfect clone |
| 1:40 | Open the scammed flow | 1930 first, then evidence, then portal |
| 1:50 | Sample dashboard and deployment slide | How a district cyber cell could run this |
| 2:00 | Close | Verify before you trust |

## Pitch outline

1. **Problem:** impersonation scams hit ordinary families and recovery is poor.
2. **Why current tools fall short:** detectors miss new generators, Indian languages and short clips; labels get stripped.
3. **Solution:** verify before you trust, in Marathi, Hindi and English.
4. **How it works:** rules, Gemini, schema check; privacy by design.
5. **Impact and deployability:** fit for a state cyber cell and the innovation society; low running cost.
6. **Roadmap and ask:** pilot in one district, evidence on Indian-language audio, partnerships.

## Demo-day backup

- [ ] Two-minute screen recording saved on the phone and laptop
- [ ] Ten test messages saved in a notes file for quick pasting
- [ ] Rules-only fallback confirmed working with the Gemini key removed
- [ ] Screenshots of every screen in the pitch deck as a last resort

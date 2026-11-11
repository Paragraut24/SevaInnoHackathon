# Development Roadmap

The build runs from tonight, Wednesday 11 November, to Friday 13 November 2026, in five sessions with four go or no-go gates; if a gate is missed, scope is cut, not the gate.

## Plan at a glance

&#91;embedded content: 2-day roadmap · 5 sessions, 4 gates\]

Sessions are not to scale. Gate 3 is the real decision point: if the live app misses 85% on the test set, Friday afternoon goes to fixing it, not to polish.

## Session plan

**Session 0 · Wed 11 Nov evening (about 3 hours)**

- [ ] Create the repository; scaffold React with Vite and FastAPI; push (45 min)
- [ ] Get one Gemini (`google-genai` Interactions API) call returning schema-valid JSON (30 min)
- [ ] Deploy the empty app and API; confirm the public URL works on a phone (45 min)
- [ ] Collect the 40-message test set: 20 scam, 20 genuine, across mr, hi, en (60 min)

**Session 1 · Thu 12 Nov morning (about 4 hours)**

- [ ] Normalizer and rule engine with the first pattern lists (90 min)
- [ ] System prompt, response schema, `/api/triage` with fusion and fallback (90 min)
- [ ] Result card UI and language toggle (60 min)

* Gate 1: a pasted scam message returns a correct Marathi result.

**Session 2 · Thu 12 Nov afternoon (about 4 hours)**

- [ ] Safe word generator and callback checklist (45 min)
- [ ] Scammed flow and client-side `jsPDF` summary (60 min)
- [ ] Link checks and number blocklist (45 min)
- [ ] Media route with Sightengine image/frame + HF audio heuristic adapter and band mapping (60 min)
- [ ] Mock dashboard with sample data labelled as such (30 min)

* Gate 2: all four features work on a laptop.

**Session 3 · Fri 13 Nov morning (about 4 hours)**

- [ ] Deploy the full app; run the 40-message test set (60 min)
- [ ] Fix the top five misses in rules or prompt (90 min)
- [ ] Test on two real phones; add privacy notice and read-aloud (60 min)
- [ ] Rate limits, file checks, secrets check (30 min)

* Gate 3: the live URL scores at least 85% on the test set.

**Session 4 · Fri 13 Nov afternoon (about 3 hours)**

- [ ] Record a 2-minute demo video (45 min)
- [ ] Build the pitch deck and the one-page deployment note (90 min)
- [ ] Clean the README; rehearse the pitch twice (45 min)

* Gate 4: video recorded and pitch rehearsed; submit.

## Cut list if a gate slips

1. Drop the live media check; show it as a roadmap slide.
2. Replace the dashboard with one static screenshot of sample data.
3. Shrink the scammed flow to a static checklist without the PDF.
4. Never cut: triage, the safe word, the privacy notice, the test set.

## After the challenge

| Phase | Focus | Exit condition |
| --- | --- | --- |
| Pilot | Telegram or WhatsApp channel using the same API; trial with volunteers from one district's cyber awareness effort | Volunteers complete checks unaided and report back on wrong answers |
| Evidence | Evaluate detectors on Marathi and Hindi audio; grow the test set from reported scam scripts | Published accuracy by language, including failures |
| Partnership | Aggregated, privacy-safe district trends for the state cyber cell; fact-checker accounts | Written agreement on data scope and a minimum group size |
| Integration | Bank and telecom hand-offs for fund freezing and number reporting | One partner pilot live |

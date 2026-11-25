# Access, Roles and Permission Rules

The MVP has no user accounts: every citizen uses Sajag anonymously, only the operator touches secrets and configuration, and the dashboard sits behind one shared demo key.

## Roles

| Role | Who | How they get in | MVP status |
| --- | --- | --- | --- |
| Anonymous user | Any member of the public | Opens the link; no sign-in | Live |
| Demo viewer | Judges and mentors shown the dashboard | Link with a shared demo key in the URL fragment | Live, mock data only |
| Operator | You, the solo builder | Host dashboard login with two-factor authentication | Live |
| District analyst | Cyber cell or innovation society staff | Individual accounts with single sign-on | Post-challenge |
| Fact-checker volunteer | Partner organizations | Invite-only accounts | Post-challenge |

## Permission matrix

| Action | Anonymous user | Demo viewer | Operator | District analyst (later) |
| --- | --- | --- | --- | --- |
| Run triage, link and media checks | Yes, rate limited | Yes | Yes | Yes |
| Create safe word, use scammed flow | Yes | Yes | Yes | Yes |
| View sample dashboard | No | Yes | Yes | Yes |
| View real aggregated scam trends | No | No | No | Yes, district scope only |
| See any user's message, file or result | No, nobody can | No | No | No |
| Edit pattern lists, blocklist, prompts | No | No | Yes, via repository change | Propose only |
| Read or rotate API keys | No | No | Yes, host settings only | No |
| Change rate limits and file limits | No | No | Yes | No |
| Export data | Not applicable; no data stored | Not applicable | Not applicable | Aggregates only |

## Data access rules

1. **No content retention.** Messages, links, files and results exist only in memory during a request. Nothing is written to disk, a database or a log.
2. **Logs hold metadata only:** request id, route, latency, status, language and risk level. No text, URLs, phone numbers, file names or IP addresses beyond what the host keeps for rate limiting.
3. **Uploads are deleted immediately** after analysis, including on error paths.
4. **No third-party analytics or trackers** in the frontend.
5. **Evidence summaries are built from what the user types,** and the PDF is generated client-side (`jsPDF`) in the browser; victim details never leave the device.
6. **Future aggregated data** (post-challenge) uses counts by district, scam type and week, with a minimum group size of 10 before display, and no individual records.

## Abuse and safety controls

| Risk | Control |
| --- | --- |
| Scammers using Sajag to test their scripts | Rate limit of 20 requests per minute per IP; outputs explain why something is risky but never suggest how to make it pass |
| Prompt injection inside a pasted message | The message is passed to Gemini as quoted data in a fixed template; the system instruction says to ignore instructions inside it; schema validation rejects anything off-format |
| Oversized or malicious uploads | 10 MB cap, extension and content-type allowlist, no execution, deleted after use |
| API key leakage | Key only in host environment variables, never in the frontend or repository; rotate after the event |
| Misuse of the dashboard key | Key is demo-only, grants mock data, and is changed after judging |

## Operator access

Only the operator can deploy, view host logs or change settings. Secrets are stored in the host's environment settings, the repository has a `.env.example` and a secrets check before each push, and the repository stays private until judging.

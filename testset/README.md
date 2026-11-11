# Sajag 40-Message Evaluation Set

Balanced evaluation corpus (`messages.csv`) for Gate 3 (target: >= 85% / 34 of 40 correct, <= 3 false alarms on genuine messages).

## Breakdown
- **Total:** 40 messages (`20 scam`, `20 genuine`)
- **Languages:** `mr` = 14 (7 scam / 7 genuine), `hi` = 13 (7 scam / 6 genuine), `en` = 13 (6 scam / 7 genuine)
- **Splits:** `dev` = 30 (used to tune rules), `holdout` = 10 (5 scam / 5 genuine, held back to detect overfitting)
- **Scam categories covered:** `digital_arrest`, `kyc_bank`, `utility_bill`, `investment`, `courier`, `job_lottery`, `loan_app`, `family_emergency`, `sextortion`
- **Genuine edge cases:** includes real-style bank OTP alerts that warn `"do not share"`, debit notifications, utility/society dues, delivery updates, PNR/flight alerts, and family chats.

All phone numbers and links are synthetic placeholders (`9876543210`, `9123456789`, sample shortlinks); no personal PII is included.


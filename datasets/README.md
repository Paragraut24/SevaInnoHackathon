# Sajag Seed Datasets

Downloaded datasets used to build `testset/messages.csv` and seed rule patterns in Marathi, Hindi, Hinglish, and English.

| File | Rows | Languages | License | Source |
| --- | --- | --- | --- | --- |
| `marathi_scam_ham.csv` | 1,100 (550 scam / 550 ham) | Marathi (`mr`) | MIT | [anmolshrivastav/scam_ham_india_14_languages](https://huggingface.co/datasets/anmolshrivastav/scam_ham_india_14_languages) (`indic_test_suite_clean.csv` + `scam_ham_india_14_languages.csv`) |
| `multilingual_mr_hi_en.csv` | 4,400 (1,100 per language) | Marathi, Hindi, Hinglish, English | MIT | [anmolshrivastav/scam_ham_india_14_languages](https://huggingface.co/datasets/anmolshrivastav/scam_ham_india_14_languages) |
| `indian_call_scams_hinglish_sample.csv` | 320 (40 per category) | Hinglish | Apache-2.0 | [chinna887/Indian_Cyber_Scam_PhoneCall_Hinglish_Dataset](https://huggingface.co/datasets/chinna887/Indian_Cyber_Scam_PhoneCall_Hinglish_Dataset) (`police_digital_arrest`, `police_blackmail`, `relative`, `bank_kyc`, `amazon`, `aadhaar`, `lottery`, `none`) |

Notes:
- Both Hugging Face sources are synthetic/curated benchmark datasets; verify and balance against real Maharashtra Cyber / Mahavitaran advisory messages when assembling the 40-message `testset/messages.csv` in Phase 0.
- `dbarbedillo/SMS_Spam_Multilingual_Collection_Dataset` (GPL, M2M100 translations of UCI UK/Singapore SMS) was skipped in favor of MIT/Apache-2.0 Indian-specific data.


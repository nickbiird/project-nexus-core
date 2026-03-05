# Yellowbird Telemetry — Lead Generation Pipeline

Automated prospecting for Catalonia-based logistics and construction materials
companies (€5M–€20M revenue). Outputs a CRM-ready CSV matching the Cold Email
Playbook format.

---

## Quick Start

```bash
# 1. Clone or copy this folder
cd yellowbird_lead_gen

# 2. Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API keys
cp .env.example .env
# Open .env in your editor and paste your real keys

# 5. Run
python lead_generator.py
```

## Output

The script generates **`yellowbird_leads.csv`** with these columns:

| Column | Source |
|--------|--------|
| Company Name | Apollo.io |
| Contact Name | Apollo.io |
| Email | Apollo.io (discovered) |
| Confidence Score | Hunter.io (0–100 verification score) |
| Revenue (est.) | Inferred from employee count proxy |
| Vertical | Logistics / Construction Materials |
| LinkedIn URL | Apollo.io |
| Email #1–3 sent dates | Empty — you fill these as you execute the Playbook |
| Reply received / sentiment | Empty — tracking columns |
| Next action | Pre-filled: "Research & Send Email #1" |

## API Keys — Where to Get Them

### Apollo.io (Contact Discovery)
1. Sign up at [app.apollo.io](https://app.apollo.io) — free tier available.
2. Go to **Settings → Integrations → API Keys**.
3. Copy the key into your `.env` file.

### Hunter.io (Email Verification)
1. Sign up at [hunter.io](https://hunter.io) — free tier: 25 searches + 25 verifications/month.
2. Go to **API** in the left sidebar.
3. Copy the key into your `.env` file.

## Rate Limits & Fair Use

| API | Free Tier Limit | Script Behavior |
|-----|-----------------|-----------------|
| Apollo | ~200 requests/day | 1.5s delay between requests |
| Hunter verification | 25/month | Verifies top 25 leads only, 2s delay |

The script will **not** burn through your quota silently. All API calls are
logged to `lead_gen.log` and to stdout in real time.

## After Running the Script

Follow the Playbook sequence:

1. Open `yellowbird_leads.csv` in Excel or Google Sheets.
2. Spend **15 minutes per prospect** on the Research Checklist (revenue
   confirmation, owner name, fleet/product range, recent news).
3. Personalise Email #1 from the Playbook templates.
4. Send first batch on **Tuesday or Thursday, 08:30–09:30 CET**.
5. Log send dates back into the CSV tracker columns.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `APOLLO_API_KEY is missing` | Check your `.env` file exists and has the key |
| `Hunter rate limit hit` | Script auto-pauses 60s and retries once |
| `0 contacts returned` | Apollo's free tier may limit search depth — try broadening keywords or reducing employee range |
| Empty CSV | Check `lead_gen.log` for detailed error messages |

## File Structure

```
yellowbird_lead_gen/
├── lead_generator.py      # Main script
├── requirements.txt       # Python dependencies
├── .env.example           # Template for API keys
├── .env                   # Your actual keys (git-ignored)
├── yellowbird_leads.csv   # Generated output
└── lead_gen.log           # Execution log
```

---

**Do not commit `.env` to version control.** Add it to `.gitignore`.

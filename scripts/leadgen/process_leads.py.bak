import csv
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")

CSV_HEADERS = [
    "Company Name",
    "Contact Name",
    "Email",
    "Confidence Score",
    "Revenue (est.)",
    "Vertical",
    "LinkedIn URL",
    "Email #1 sent date",
    "Email #1 opened?",
    "Email #2 sent date",
    "Email #3 sent date",
    "Reply received?",
    "Reply sentiment",
    "Next action",
]


def verify_hunter(email):
    if not HUNTER_API_KEY:
        return 0
    if not email or email.lower() == "none":
        return 0

    url = "https://api.hunter.io/v2/email-verifier"
    params = {"email": email, "api_key": HUNTER_API_KEY}

    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 429:
            print("Rate limit hit. Waiting 10s...")
            time.sleep(10)
            return verify_hunter(email)
        data = resp.json()
        return data.get("data", {}).get("score", 0)
    except Exception:
        return 0


def clean_value(val):
    """Removes weird markdown links and stray quotes."""
    # Fix [email](mailto:email) -> email
    if "](" in val:
        val = val.split("](")[0].replace("[", "")
    return val.strip().strip('"').strip()


def process_csv():
    input_file = "apollo_raw.csv"
    output_file = "yellowbird_leads.csv"

    processed_leads = []

    with open(input_file, encoding="utf-8-sig") as f:
        # Skip header
        next(f)

        for line in f:
            if len(line.strip()) < 10:
                continue

            # Split by comma but be careful of quotes.
            # Easiest way given the data structure is a raw split since Apollo puts email at index 5 or 6.
            parts = line.split(",")

            # Since the row might start with a quote, let's clean the first few columns
            first_name = clean_value(parts[0]) if len(parts) > 0 else ""
            last_name = clean_value(parts[1]) if len(parts) > 1 else ""
            name = f"{first_name} {last_name}".strip()

            company = clean_value(parts[3]) if len(parts) > 3 else ""

            # The email might be at index 5 or 6 depending on the quote structure
            email = ""
            for p in parts:
                if "@" in p and "." in p and "gmail.com" not in p.lower():
                    email = clean_value(p)
                    break

            if not email:
                continue

            # Grab linkedin if available
            linkedin = ""
            for p in parts:
                if "linkedin.com/in" in p:
                    linkedin = clean_value(p)
                    break

            # Determine vertical
            vertical = "Logistics"
            if (
                "construction" in line.lower()
                or "building" in line.lower()
                or "material" in line.lower()
            ):
                vertical = "Construction Materials"

            print(f"Verifying {email}...")
            score = verify_hunter(email)
            time.sleep(2)

            processed_leads.append(
                [
                    company,
                    name,
                    email,
                    score,
                    "€5M-€20M",
                    vertical,
                    linkedin,
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "Research & Send Email #1",
                ]
            )

    with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)
        writer.writerows(processed_leads)

    print(f"\nSuccess! Verified {len(processed_leads)} leads.")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    process_csv()

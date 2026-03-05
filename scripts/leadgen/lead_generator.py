#!/usr/bin/env python3
"""
Yellowbird Telemetry — Lead Generation Pipeline
================================================

Automated prospecting script for Catalonia-based logistics and
construction materials companies (€5M–€20M revenue).

Sources:
    - Apollo.io API (contact discovery + company search)
    - Hunter.io API (email verification)

Output:
    yellowbird_leads.csv — Minimum Viable CRM format

Usage:
    1. Copy .env.example → .env and add your API keys.
    2. pip install -r requirements.txt
    3. python lead_generator.py
"""

from __future__ import annotations

import csv
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

# ─── Configuration ────────────────────────────────────────────────────

load_dotenv()

APOLLO_API_KEY: str = os.getenv("APOLLO_API_KEY", "")
HUNTER_API_KEY: str = os.getenv("HUNTER_API_KEY", "")

# Rate-limit delays (seconds) — generous to stay within free tiers
APOLLO_DELAY: float = 1.5  # Apollo free: ~200 req/day
HUNTER_DELAY: float = 2.0  # Hunter free: 25 verifications/month

# API base URLs
APOLLO_BASE: str = "https://api.apollo.io/v1"
HUNTER_BASE: str = "https://api.hunter.io/v2"

# Output
OUTPUT_DIR: Path = Path(__file__).parent
OUTPUT_FILE: str = "yellowbird_leads.csv"
LOG_FILE: str = "lead_gen.log"

# CSV headers — exact match to Playbook CRM table
CSV_HEADERS: list[str] = [
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

# ─── Logging ──────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(OUTPUT_DIR / LOG_FILE, mode="w", encoding="utf-8"),
    ],
)
log = logging.getLogger("yellowbird")

# ─── Data Model ───────────────────────────────────────────────────────


@dataclass
class Lead:
    """Single qualified lead record."""

    company_name: str = ""
    contact_name: str = ""
    email: str = ""
    confidence_score: int = 0  # 0–100 from Hunter verification
    revenue_est: str = ""  # e.g. "€10M–€20M"
    vertical: str = ""  # "Logistics" | "Construction Materials"
    linkedin_url: str = ""
    email_1_sent: str = ""
    email_1_opened: str = ""
    email_2_sent: str = ""
    email_3_sent: str = ""
    reply_received: str = ""
    reply_sentiment: str = ""
    next_action: str = "Research & Send Email #1"

    def to_row(self) -> list[str]:
        """Return a list matching CSV_HEADERS order."""
        return [
            self.company_name,
            self.contact_name,
            self.email,
            str(self.confidence_score),
            self.revenue_est,
            self.vertical,
            self.linkedin_url,
            self.email_1_sent,
            self.email_1_opened,
            self.email_2_sent,
            self.email_3_sent,
            self.reply_received,
            self.reply_sentiment,
            self.next_action,
        ]


# ─── Search Profiles ─────────────────────────────────────────────────

# Apollo uses their own industry keywords + employee ranges as
# revenue proxy.  50-200 employees ≈ €5M–€20M for these verticals.

SEARCH_PROFILES: list[dict] = [
    {
        "label": "Logistics",
        "vertical": "Logistics",
        "revenue_est": "€10M–€20M",
        "person_titles": [
            "Director General",
            "Gerente",
            "CEO",
            "Consejero Delegado",
            "Owner",
            "Fundador",
            "Propietario",
        ],
        "organization_industry_tag_ids": [],  # filled at runtime if needed
        "q_organization_keyword_tags": [
            "logistics",
            "trucking",
            "freight",
            "transporte",
            "logística",
        ],
        "organization_locations": ["Spain, Catalonia"],
        "organization_num_employees_ranges": ["51,200"],
        "per_page": 15,  # request up to 15 to allow for filtering
        "target_count": 10,
    },
    {
        "label": "Construction Materials",
        "vertical": "Construction Materials",
        "revenue_est": "€8M–€20M",
        "person_titles": [
            "Director General",
            "Gerente",
            "CEO",
            "Consejero Delegado",
            "Owner",
            "Fundador",
            "Propietario",
        ],
        "organization_industry_tag_ids": [],
        "q_organization_keyword_tags": [
            "building materials",
            "construction materials",
            "materiales de construcción",
            "distribución materiales",
        ],
        "organization_locations": ["Spain, Catalonia"],
        "organization_num_employees_ranges": ["51,200"],
        "per_page": 15,
        "target_count": 10,
    },
]


# ─── Apollo.io Client ─────────────────────────────────────────────────


class ApolloClient:
    """Thin wrapper around Apollo.io's People Search endpoint."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "X-Api-Key": self.api_key,  # <--- WE ADDED THIS LINE
            }
        )

    def search_people(self, profile: dict) -> list[dict]:
        """
        New 2026 Flow:
        1. POST /v1/mixed_people/api_search (get IDs)
        2. POST /v1/people/bulk_match (get full profiles with emails)
        """
        # Step 1: Search for IDs (Free)
        search_url = f"{APOLLO_BASE}/mixed_people/api_search"
        search_payload = {
            "person_titles": profile["person_titles"],
            "q_organization_keyword_tags": profile["q_organization_keyword_tags"],
            "organization_locations": profile["organization_locations"],
            "organization_num_employees_ranges": profile["organization_num_employees_ranges"],
            "per_page": profile["per_page"],
            "page": 1,
        }

        log.info(
            "Apollo API Search: %s (titles=%d, keywords=%d)",
            profile["label"],
            len(profile["person_titles"]),
            len(profile["q_organization_keyword_tags"]),
        )

        try:
            resp = self.session.post(search_url, json=search_payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            people_partial = data.get("people", [])

            # Extract the IDs we need to enrich
            person_ids = [p.get("id") for p in people_partial if p.get("id")]

            if not person_ids:
                log.warning("No person IDs found for %s", profile["label"])
                return []

            log.info("Found %d IDs, now enriching for full profiles...", len(person_ids))

            # Step 2: Bulk Match to get full data (Uses Credits)
            enrich_url = f"{APOLLO_BASE}/people/bulk_match"
            enrich_payload = {"details": [{"id": pid} for pid in person_ids]}

            # Important: Apollo requires custom headers for auth sometimes
            headers = {"Cache-Control": "no-cache", "Content-Type": "application/json"}

            enrich_resp = self.session.post(
                enrich_url, headers=headers, json=enrich_payload, timeout=30
            )
            enrich_resp.raise_for_status()
            enrich_data = enrich_resp.json()

            # Extract matched records
            matches = enrich_data.get("matches", [])
            full_people = [match.get("person") for match in matches if match.get("person")]

            log.info(
                "Apollo returned %d full profiles for '%s'", len(full_people), profile["label"]
            )
            return full_people

        except requests.exceptions.HTTPError as exc:
            log.error("Apollo HTTP error: %s — %s", exc, getattr(exc.response, "text", ""))
            return []
        except requests.exceptions.RequestException as exc:
            log.error("Apollo request failed: %s", exc)
            return []

    def parse_leads(self, people: list[dict], profile: dict) -> list[Lead]:
        """Extract Lead objects from raw Apollo person records."""
        leads: list[Lead] = []

        for person in people:
            org = person.get("organization", {}) or {}
            email = person.get("email") or ""
            name = person.get("name") or ""
            company = org.get("name") or person.get("organization_name", "")
            linkedin = person.get("linkedin_url") or ""

            # Skip contacts without an email or company name
            if not email or not company:
                log.debug("Skipping %s — missing email or company", name)
                continue

            lead = Lead(
                company_name=company,
                contact_name=name,
                email=email,
                confidence_score=0,
                revenue_est=profile["revenue_est"],
                vertical=profile["vertical"],
                linkedin_url=linkedin,
            )
            leads.append(lead)

        return leads


# ─── Hunter.io Client ────────────────────────────────────────────────


class HunterClient:
    """Thin wrapper around Hunter.io's Email Verification endpoint."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.session = requests.Session()
        self._verified_count: int = 0

    @property
    def verified_count(self) -> int:
        return self._verified_count

    def verify_email(self, email: str) -> int:
        """
        GET /v2/email-verifier?email=...&api_key=...

        Returns a confidence score (0–100).
        Hunter free tier: 25 verifications/month — use wisely.
        """
        if not self.api_key:
            log.warning("Hunter API key not set — skipping verification for %s", email)
            return 0

        url = f"{HUNTER_BASE}/email-verifier"
        params = {"email": email, "api_key": self.api_key}

        try:
            resp = self.session.get(url, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.HTTPError as exc:
            status = getattr(exc.response, "status_code", None)
            if status == 429:
                log.warning("Hunter rate limit hit — pausing 60s")
                time.sleep(60)
                return self.verify_email(email)  # single retry
            log.error("Hunter HTTP error for %s: %s", email, exc)
            return 0
        except requests.exceptions.RequestException as exc:
            log.error("Hunter request failed for %s: %s", email, exc)
            return 0

        result = data.get("data", {})
        score = result.get("score", 0) or 0
        status = result.get("status", "unknown")

        self._verified_count += 1
        log.info(
            "Hunter verified %s → score=%d, status=%s  [%d verifications used]",
            email,
            score,
            status,
            self._verified_count,
        )
        return score

    def find_email(self, domain: str, first_name: str, last_name: str) -> tuple[str, int]:
        """
        GET /v2/email-finder?domain=...&first_name=...&last_name=...

        Fallback: if Apollo returns no email, try Hunter's email finder.
        Returns (email, confidence_score).
        """
        if not self.api_key:
            return ("", 0)

        url = f"{HUNTER_BASE}/email-finder"
        params = {
            "domain": domain,
            "first_name": first_name,
            "last_name": last_name,
            "api_key": self.api_key,
        }

        try:
            resp = self.session.get(url, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as exc:
            log.error(
                "Hunter email-finder failed for %s %s @ %s: %s", first_name, last_name, domain, exc
            )
            return ("", 0)

        result = data.get("data", {})
        email = result.get("email", "") or ""
        score = result.get("score", 0) or 0
        return (email, score)


# ─── Deduplication ────────────────────────────────────────────────────


def deduplicate_leads(leads: list[Lead]) -> list[Lead]:
    """Remove duplicate leads by (company_name, email) pair."""
    seen: set[tuple[str, str]] = set()
    unique: list[Lead] = []
    for lead in leads:
        key = (lead.company_name.lower().strip(), lead.email.lower().strip())
        if key not in seen:
            seen.add(key)
            unique.append(lead)
    return unique


# ─── CSV Writer ───────────────────────────────────────────────────────


def write_csv(leads: list[Lead], filepath: Path) -> None:
    """Write leads to CSV with the exact Playbook CRM headers."""
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)
        for lead in leads:
            writer.writerow(lead.to_row())
    log.info("Wrote %d leads to %s", len(leads), filepath)


# ─── Main Pipeline ────────────────────────────────────────────────────


def run_pipeline() -> None:
    """Execute the full lead-generation pipeline."""

    # ── Validate keys ──
    if not APOLLO_API_KEY:
        log.error("APOLLO_API_KEY is missing. Create a .env file with your key (see .env.example).")
        sys.exit(1)

    if not HUNTER_API_KEY:
        log.warning(
            "HUNTER_API_KEY is missing. Emails will NOT be verified — Confidence Score will be 0."
        )

    apollo = ApolloClient(APOLLO_API_KEY)
    hunter = HunterClient(HUNTER_API_KEY)

    all_leads: list[Lead] = []

    # ── Phase 1: Contact Discovery via Apollo ──
    log.info("=" * 60)
    log.info("PHASE 1 — Contact Discovery (Apollo.io)")
    log.info("=" * 60)

    for profile in SEARCH_PROFILES:
        log.info("─── Searching: %s ───", profile["label"])
        time.sleep(APOLLO_DELAY)

        people = apollo.search_people(profile)
        leads = apollo.parse_leads(people, profile)

        # Trim to target count
        target = profile["target_count"]
        if len(leads) > target:
            leads = leads[:target]
            log.info("Trimmed to %d leads for '%s'", target, profile["label"])

        all_leads.extend(leads)
        log.info(
            "Collected %d qualified leads for '%s' (running total: %d)",
            len(leads),
            profile["label"],
            len(all_leads),
        )

    # ── Phase 2: Deduplication ──
    pre_dedup = len(all_leads)
    all_leads = deduplicate_leads(all_leads)
    log.info(
        "Deduplication: %d → %d leads (%d removed)",
        pre_dedup,
        len(all_leads),
        pre_dedup - len(all_leads),
    )

    # ── Phase 3: Email Verification via Hunter ──
    log.info("=" * 60)
    log.info("PHASE 3 — Email Verification (Hunter.io)")
    log.info("=" * 60)

    if HUNTER_API_KEY:
        # Hunter free tier = 25 verifications/month.
        # We verify the top leads only; prioritize by vertical balance.
        max_verifications = min(len(all_leads), 25)
        log.info(
            "Verifying up to %d emails (Hunter free tier limit: 25/month)",
            max_verifications,
        )

        for i, lead in enumerate(all_leads[:max_verifications]):
            log.info("[%d/%d] Verifying: %s", i + 1, max_verifications, lead.email)
            score = hunter.verify_email(lead.email)
            lead.confidence_score = score
            time.sleep(HUNTER_DELAY)

        log.info("Verification complete. %d emails checked.", hunter.verified_count)
    else:
        log.warning("Skipping verification — no Hunter API key.")

    # ── Phase 4: Write Output ──
    log.info("=" * 60)
    log.info("PHASE 4 — Export")
    log.info("=" * 60)

    output_path = OUTPUT_DIR / OUTPUT_FILE
    write_csv(all_leads, output_path)

    # ── Summary ──
    log.info("=" * 60)
    log.info("PIPELINE COMPLETE")
    log.info("=" * 60)
    log.info("Total leads:       %d", len(all_leads))
    log.info("  Logistics:       %d", sum(1 for ld in all_leads if ld.vertical == "Logistics"))
    log.info(
        "  Construction:    %d", sum(1 for ld in all_leads if ld.vertical == "Construction Materials")
    )
    log.info("  Verified:        %d", sum(1 for ld in all_leads if ld.confidence_score > 0))
    log.info("Output file:       %s", output_path.resolve())
    log.info("")
    log.info("Next step: Open %s, review leads, begin prospect", OUTPUT_FILE)
    log.info("research per the Playbook checklist (15 min/prospect).")


# ─── Entry Point ──────────────────────────────────────────────────────

if __name__ == "__main__":
    log.info("Yellowbird Telemetry — Lead Generation Pipeline")
    log.info("Timestamp: %s", datetime.now().isoformat())
    log.info("")
    run_pipeline()

"""
Data models, enums, constants, and CSV definitions for the Lead Generation Pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TypedDict


class Vertical(StrEnum):
    """Business vertical classification."""

    LOGISTICS = "Logistics"
    CONSTRUCTION_MATERIALS = "Construction Materials"
    UNKNOWN = "Unknown"


class Tier(StrEnum):
    """Lead priority tier based on ICP score and Hunter confidence."""

    TIER_1 = "Tier 1"
    TIER_2 = "Tier 2"
    TIER_3 = "Tier 3"
    TIER_4 = "Tier 4"


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


@dataclass(frozen=True)
class Lead:
    """Single qualified lead record."""

    company_name: str = field(default="")
    contact_name: str = field(default="")
    email: str = field(default="")
    confidence_score: int = field(default=0)  # 0–100 from Hunter verification
    revenue_est: str = field(default="")  # e.g. "€10M–€20M"
    vertical: Vertical | str = field(default=Vertical.UNKNOWN)  # Can be a string or Vertical enum
    linkedin_url: str = field(default="")
    email_1_sent: str = field(default="")
    email_1_opened: str = field(default="")
    email_2_sent: str = field(default="")
    email_3_sent: str = field(default="")
    reply_received: str = field(default="")
    reply_sentiment: str = field(default="")
    next_action: str = field(default="Research & Send Email #1")

    def to_row(self) -> list[str]:
        """Return a list matching CSV_HEADERS order."""
        vert_str = str(self.vertical)
        return [
            self.company_name,
            self.contact_name,
            self.email,
            str(self.confidence_score),
            self.revenue_est,
            vert_str,
            self.linkedin_url,
            self.email_1_sent,
            self.email_1_opened,
            self.email_2_sent,
            self.email_3_sent,
            self.reply_received,
            self.reply_sentiment,
            self.next_action,
        ]

    @classmethod
    def from_row(cls, row: dict[str, str]) -> Lead:
        """Reconstruct a Lead object from a CSV row dictionary."""

        def get_int(val: str | None) -> int:
            if not val:
                return 0
            try:
                return int(val)
            except ValueError:
                return 0

        # Try to parse vertical back to enum if possible
        raw_vertical = row.get("Vertical", "")
        parsed_vertical: str | Vertical = raw_vertical
        for v in Vertical:
            if v.lower() == raw_vertical.lower():
                parsed_vertical = v
                break

        return cls(
            company_name=row.get("Company Name", ""),
            contact_name=row.get("Contact Name", ""),
            email=row.get("Email", ""),
            confidence_score=get_int(row.get("Confidence Score")),
            revenue_est=row.get("Revenue (est.)", ""),
            vertical=parsed_vertical,
            linkedin_url=row.get("LinkedIn URL", ""),
            email_1_sent=row.get("Email #1 sent date", ""),
            email_1_opened=row.get("Email #1 opened?", ""),
            email_2_sent=row.get("Email #2 sent date", ""),
            email_3_sent=row.get("Email #3 sent date", ""),
            reply_received=row.get("Reply received?", ""),
            reply_sentiment=row.get("Reply sentiment", ""),
            next_action=row.get("Next action", ""),
        )


class SearchProfile(TypedDict):
    """Type definition for an Apollo search profile dict."""

    label: str
    vertical: Vertical
    revenue_est: str
    person_titles: list[str]
    organization_industry_tag_ids: list[str]
    q_organization_keyword_tags: list[str]
    organization_locations: list[str]
    organization_num_employees_ranges: list[str]
    per_page: int
    target_count: int


SEARCH_PROFILES: list[SearchProfile] = [
    {
        "label": "Logistics",
        "vertical": Vertical.LOGISTICS,
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
        "organization_industry_tag_ids": [],
        "q_organization_keyword_tags": [
            "logistics",
            "trucking",
            "freight",
            "transporte",
            "logística",
        ],
        "organization_locations": ["Spain, Catalonia"],
        "organization_num_employees_ranges": ["51,200"],
        "per_page": 15,
        "target_count": 10,
    },
    {
        "label": "Construction Materials",
        "vertical": Vertical.CONSTRUCTION_MATERIALS,
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

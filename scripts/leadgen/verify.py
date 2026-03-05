"""
Email verification logic via the Hunter.io API.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests  # type: ignore[import-untyped]

log = logging.getLogger(__name__)

HUNTER_BASE: str = "https://api.hunter.io/v2"


class HunterCapExceededError(Exception):
    """Raised when the Hunter free tier limit is exceeded."""

    pass


class HunterClient:
    """Thin wrapper around Hunter.io's Email Verification endpoint.

    Includes 429 retry logic, free-tier rate capping, and delay management.
    """

    def __init__(self, api_key: str, free_tier_cap: int = 25, delay_seconds: float = 2.0) -> None:
        """Initialize the HunterClient.

        Args:
            api_key (str): The Hunter.io API key.
            free_tier_cap (int, optional): Max verifications per run. Defaults to 25.
            delay_seconds (float, optional): Seconds to sleep between calls. Defaults to 2.0.
        """
        if not api_key:
            raise ValueError("Hunter API key cannot be empty.")

        self.api_key = api_key
        self.session = requests.Session()
        self.free_tier_cap = free_tier_cap
        self.delay_seconds = delay_seconds
        self._verified_count: int = 0
        self._domain_search_count: int = 0
        self._find_email_count: int = 0

    @property
    def verified_count(self) -> int:
        """Returns the number of verifications completed in this session."""
        return self._verified_count

    @property
    def domain_search_count(self) -> int:
        """Returns the number of domain searches completed in this session."""
        return self._domain_search_count

    @property
    def find_email_count(self) -> int:
        """Returns the number of email finder calls completed in this session."""
        return self._find_email_count

    def verify_email(self, email: str) -> int:
        """Verifies an email via Hunter API with capping and rate limits.

        Args:
            email (str): The email address to verify.

        Returns:
            int: The confidence score (0-100). Returns 0 if no API key or invalid.

        Raises:
            HunterCapExceededError: If the maximum allowed verifications is exceeded.

        Example:
            >>> client = HunterClient("valid_api_key")
            >>> client.verify_email("john@example.com")
            98
        """
        if not self.api_key:
            log.warning("Hunter API key not set — skipping verification for %s", email)
            return 0

        if not email or email.lower() == "none":
            return 0

        if self._verified_count >= self.free_tier_cap:
            log.info(
                "Hunter free tier cap (%d) exceeded — halting verifications", self.free_tier_cap
            )
            raise HunterCapExceededError(f"Hunter free tier cap of {self.free_tier_cap} exceeded.")

        score = self._call_api(email)

        self._verified_count += 1
        log.info(
            "Verified %s (Score: %d) — %d/%d used",
            email,
            score,
            self._verified_count,
            self.free_tier_cap,
        )

        # Enforce rate limiting delay
        time.sleep(self.delay_seconds)

        return score

    def domain_search(
        self,
        domain: str,
        *,
        seniority: list[str] | None = None,
        department: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for email contacts associated with a company domain.

        Wraps Hunter's ``/v2/domain-search`` endpoint.

        Args:
            domain: Company web domain (e.g. ``"transportesgarcia.com"``).
            seniority: Optional seniority levels to filter (e.g.
                ``["executive", "director"]``).
            department: Optional department names to filter.

        Returns:
            A list of contact dictionaries from the ``emails`` key of the
            response.  Returns an empty list when Hunter has no data or on
            a non-2xx response.

        Raises:
            HunterCapExceededError: If the domain-search cap is reached.
        """
        if self._domain_search_count >= self.free_tier_cap:
            log.info(
                "Hunter domain-search cap (%d) exceeded — halting searches",
                self.free_tier_cap,
            )
            raise HunterCapExceededError(
                f"Hunter domain-search cap of {self.free_tier_cap} exceeded."
            )

        params: dict[str, str] = {"domain": domain, "api_key": self.api_key}
        if seniority:
            params["seniority"] = ",".join(seniority)
        if department:
            params["department"] = ",".join(department)

        data = self._call_api_json(f"{HUNTER_BASE}/domain-search", params)
        if data is None:
            log.info("Domain search for %s returned no results (non-2xx)", domain)
            return []

        self._domain_search_count += 1
        contacts: list[dict[str, Any]] = data.get("data", {}).get("emails", [])
        log.info(
            "Domain search for %s returned %d contacts — %d/%d used",
            domain,
            len(contacts),
            self._domain_search_count,
            self.free_tier_cap,
        )

        time.sleep(self.delay_seconds)
        return contacts

    def find_email(
        self,
        domain: str,
        first_name: str,
        last_name: str,
    ) -> dict[str, Any] | None:
        """Find an email address for a person at a given domain.

        Wraps Hunter's ``/v2/email-finder`` endpoint.

        Args:
            domain: Company web domain.
            first_name: Contact's first name.
            last_name: Contact's last name.

        Returns:
            The contact dictionary from the ``data`` key, or ``None`` if
            Hunter cannot find a match or the request fails.

        Raises:
            HunterCapExceededError: If the email-finder cap is reached.
        """
        if self._find_email_count >= self.free_tier_cap:
            log.info(
                "Hunter email-finder cap (%d) exceeded — halting lookups",
                self.free_tier_cap,
            )
            raise HunterCapExceededError(
                f"Hunter email-finder cap of {self.free_tier_cap} exceeded."
            )

        params: dict[str, str] = {
            "domain": domain,
            "first_name": first_name,
            "last_name": last_name,
            "api_key": self.api_key,
        }

        data = self._call_api_json(f"{HUNTER_BASE}/email-finder", params)
        if data is None:
            log.info(
                "Email finder for %s %s @ %s returned no results (non-2xx)",
                first_name,
                last_name,
                domain,
            )
            return None

        result: dict[str, Any] = data.get("data", {})
        if not result or not result.get("email"):
            log.info(
                "Email finder for %s %s @ %s — no match found",
                first_name,
                last_name,
                domain,
            )
            return None

        self._find_email_count += 1
        log.info(
            "Email finder for %s %s @ %s — found %s (confidence: %s) — %d/%d used",
            first_name,
            last_name,
            domain,
            result.get("email"),
            result.get("confidence"),
            self._find_email_count,
            self.free_tier_cap,
        )

        time.sleep(self.delay_seconds)
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _call_api(self, email: str) -> int:
        """Make the actual HTTP GET request to Hunter (email-verifier)."""
        url = f"{HUNTER_BASE}/email-verifier"
        params = {"email": email, "api_key": self.api_key}

        try:
            resp = self.session.get(url, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            result = data.get("data", {})
            return result.get("score", 0) or 0

        except requests.exceptions.HTTPError as exc:
            status = getattr(exc.response, "status_code", None)
            if status == 429:
                self._handle_rate_limit()
                return self._call_api(email)  # single retry
            log.error("Hunter HTTP error for %s: %s", email, exc)
            return 0

        except requests.exceptions.RequestException as exc:
            log.error("Hunter request failed for %s: %s", email, exc)
            return 0

    def _call_api_json(self, url: str, params: dict[str, str]) -> dict[str, Any] | None:
        """Make an HTTP GET request and return the parsed JSON response.

        Returns ``None`` on non-2xx responses (after exhausting retries) or
        on network failures.
        """
        try:
            resp = self.session.get(url, params=params, timeout=20)
            resp.raise_for_status()
            result: dict[str, Any] = resp.json()
            return result

        except requests.exceptions.HTTPError as exc:
            status = getattr(exc.response, "status_code", None)
            if status == 429:
                self._handle_rate_limit()
                return self._call_api_json(url, params)  # single retry
            log.error("Hunter HTTP error for %s: %s", url, exc)
            return None

        except requests.exceptions.RequestException as exc:
            log.error("Hunter request failed for %s: %s", url, exc)
            return None

    def _handle_rate_limit(self) -> None:
        """Handle 429 Too Many Requests by enforcing a 60-second backoff."""
        log.warning("Hunter rate limit hit — pausing 60s")
        time.sleep(60)

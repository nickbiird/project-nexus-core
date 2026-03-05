"""
Email verification logic via the Hunter.io API.
"""

import logging
import time

import requests  # type: ignore

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

    @property
    def verified_count(self) -> int:
        """Returns the number of verifications completed in this session."""
        return self._verified_count

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

    def _call_api(self, email: str) -> int:
        """Make the actual HTTP GET request to Hunter."""
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

    def _handle_rate_limit(self) -> None:
        """Handle 429 Too Many Requests by enforcing a 60-second backoff."""
        log.warning("Hunter rate limit hit — pausing 60s")
        time.sleep(60)

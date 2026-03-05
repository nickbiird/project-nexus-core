"""
Unit tests for the Hunter.io Email Verification client.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from scripts.leadgen.verify import HunterCapExceededError, HunterClient


class TestHunterClient:
    """Tests for the encapsulation and 429 processing of the Hunter.io API."""

    def test_verify_email_returns_score_from_api(self):
        """Must extract the native integer score structurally from the dict return layout."""
        client = HunterClient(api_key="valid_key", delay_seconds=0)

        with patch("scripts.leadgen.verify.requests.Session.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"data": {"score": 85}}
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp

            assert client.verify_email("test@domain.com") == 85

    def test_verify_email_returns_zero_on_empty_email(self):
        """Immediately skips verification sequences returning 0 natively."""
        client = HunterClient(api_key="valid_key", delay_seconds=0)
        assert client.verify_email("") == 0
        assert client.verify_email("none") == 0

    def test_verify_email_returns_zero_on_none_api_key(self):
        """Missing keys return 0 immediately without breaking routines."""
        # Note: __init__ enforces api_key, but if it gets cleared after init or an empty string gets passed:
        # Our modified initialization throws ValueError on empty init, so we test that behavior instead if possible.
        client = HunterClient(api_key="not_none", delay_seconds=0)
        client.api_key = ""  # Force zero test
        assert client.verify_email("test@domain.com") == 0

    @patch("scripts.leadgen.verify.time.sleep")
    def test_rate_limit_retry(self, mock_sleep):
        """A 429 MUST trigger the internal backoff before completing the secondary pass loop."""
        client = HunterClient(api_key="valid_key", delay_seconds=0)

        with patch("scripts.leadgen.verify.requests.Session.get") as mock_get:
            # First response fails with 429
            err_resp = MagicMock()
            err_resp.status_code = 429
            exc = requests.exceptions.HTTPError()
            exc.response = err_resp

            # Second response succeeds with 60
            ok_resp = MagicMock()
            ok_resp.json.return_value = {"data": {"score": 60}}

            mock_get.side_effect = [exc, ok_resp]

            assert client.verify_email("test@domain.com") == 60
            assert (
                mock_sleep.call_count == 2
            )  # Once for 60s backoff, once for end of function delay

    def test_cap_enforcement(self):
        """Raises natively once operational caps reach limit capacities."""
        client = HunterClient(api_key="valid_key", free_tier_cap=2, delay_seconds=0)

        with patch("scripts.leadgen.verify.requests.Session.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"data": {"score": 50}}
            mock_get.return_value = mock_resp

            client.verify_email("1@domain.com")
            client.verify_email("2@domain.com")

            with pytest.raises(HunterCapExceededError):
                client.verify_email("3@domain.com")

    def test_network_failure_returns_zero(self):
        """Hard network disconnects must fall through gracefully, yielding 0s."""
        client = HunterClient(api_key="valid_key", delay_seconds=0)

        with patch("scripts.leadgen.verify.requests.Session.get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Network down")

            assert client.verify_email("test@domain.com") == 0

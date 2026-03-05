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


# ===================================================================
# domain_search tests
# ===================================================================


class TestDomainSearch:
    """Tests for the HunterClient.domain_search method."""

    def test_returns_contacts_on_success(self):
        """Successful response returns the list of contacts and increments counter."""
        client = HunterClient(api_key="valid_key", delay_seconds=0)
        contacts_payload = [
            {"email": "juan@empresa.es", "confidence": 95},
            {"email": "maria@empresa.es", "confidence": 88},
        ]

        with patch("scripts.leadgen.verify.requests.Session.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"data": {"emails": contacts_payload}}
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp

            result = client.domain_search("empresa.es")
            assert result == contacts_payload
            assert client.domain_search_count == 1

    def test_returns_empty_list_on_no_results(self):
        """Hunter returns zero contacts — empty list, no exception."""
        client = HunterClient(api_key="valid_key", delay_seconds=0)

        with patch("scripts.leadgen.verify.requests.Session.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"data": {"emails": []}}
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp

            result = client.domain_search("unknown-domain.com")
            assert result == []
            assert client.domain_search_count == 1

    @patch("scripts.leadgen.verify.time.sleep")
    def test_rate_limit_retry(self, mock_sleep):
        """A 429 triggers backoff then retries successfully."""
        client = HunterClient(api_key="valid_key", delay_seconds=0)

        with patch("scripts.leadgen.verify.requests.Session.get") as mock_get:
            err_resp = MagicMock()
            err_resp.status_code = 429
            exc = requests.exceptions.HTTPError()
            exc.response = err_resp

            ok_resp = MagicMock()
            ok_resp.json.return_value = {"data": {"emails": [{"email": "a@b.com"}]}}

            mock_get.side_effect = [exc, ok_resp]

            result = client.domain_search("empresa.es")
            assert len(result) == 1
            # Backoff sleep (60s) + delay sleep
            assert mock_sleep.call_count >= 1

    def test_cap_enforcement(self):
        """Raises HunterCapExceededError when cap is exhausted."""
        client = HunterClient(api_key="valid_key", free_tier_cap=1, delay_seconds=0)

        with patch("scripts.leadgen.verify.requests.Session.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"data": {"emails": [{"email": "a@b.com"}]}}
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp

            client.domain_search("empresa.es")

            with pytest.raises(HunterCapExceededError):
                client.domain_search("otra-empresa.es")

            # Verify no extra HTTP call was made
            assert mock_get.call_count == 1

    def test_optional_params_included(self):
        """Seniority and department are passed as comma-separated strings."""
        client = HunterClient(api_key="valid_key", delay_seconds=0)

        with patch("scripts.leadgen.verify.requests.Session.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"data": {"emails": []}}
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp

            client.domain_search(
                "empresa.es",
                seniority=["executive", "director"],
                department=["sales", "management"],
            )

            call_kwargs = mock_get.call_args
            params = call_kwargs[1]["params"] if "params" in call_kwargs[1] else call_kwargs[0][1]
            assert params["seniority"] == "executive,director"
            assert params["department"] == "sales,management"

    def test_no_optional_params_omitted(self):
        """When no seniority or department, those keys are absent from the request."""
        client = HunterClient(api_key="valid_key", delay_seconds=0)

        with patch("scripts.leadgen.verify.requests.Session.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"data": {"emails": []}}
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp

            client.domain_search("empresa.es")

            call_kwargs = mock_get.call_args
            params = call_kwargs[1]["params"] if "params" in call_kwargs[1] else call_kwargs[0][1]
            assert "seniority" not in params
            assert "department" not in params


# ===================================================================
# find_email tests
# ===================================================================


class TestFindEmail:
    """Tests for the HunterClient.find_email method."""

    def test_returns_contact_on_success(self):
        """Successful response returns the contact dict and increments counter."""
        client = HunterClient(api_key="valid_key", delay_seconds=0)
        contact = {"email": "juan@empresa.es", "confidence": 92, "first_name": "Juan"}

        with patch("scripts.leadgen.verify.requests.Session.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"data": contact}
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp

            result = client.find_email("empresa.es", "Juan", "García")
            assert result == contact
            assert client.find_email_count == 1

    def test_returns_none_on_no_match(self):
        """Hunter returns no match — None returned, no exception."""
        client = HunterClient(api_key="valid_key", delay_seconds=0)

        with patch("scripts.leadgen.verify.requests.Session.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"data": {}}
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp

            result = client.find_email("empresa.es", "Nonexistent", "Person")
            assert result is None

    def test_cap_enforcement(self):
        """Raises HunterCapExceededError when cap is exhausted."""
        client = HunterClient(api_key="valid_key", free_tier_cap=1, delay_seconds=0)
        contact = {"email": "a@b.com", "confidence": 80}

        with patch("scripts.leadgen.verify.requests.Session.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"data": contact}
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp

            client.find_email("empresa.es", "Juan", "García")

            with pytest.raises(HunterCapExceededError):
                client.find_email("empresa.es", "Maria", "López")

            assert mock_get.call_count == 1


# ===================================================================
# Cross-endpoint cap independence
# ===================================================================


class TestCrossEndpointCaps:
    """Verify that exhausting one endpoint's cap does not affect others."""

    def test_domain_search_cap_does_not_block_find_email(self):
        """After exhausting domain_search cap, find_email still works."""
        client = HunterClient(api_key="valid_key", free_tier_cap=1, delay_seconds=0)
        contact = {"email": "juan@empresa.es", "confidence": 90}

        with patch("scripts.leadgen.verify.requests.Session.get") as mock_get:
            # domain_search succeeds once
            ds_resp = MagicMock()
            ds_resp.json.return_value = {"data": {"emails": [contact]}}
            ds_resp.raise_for_status.return_value = None

            # find_email succeeds
            fe_resp = MagicMock()
            fe_resp.json.return_value = {"data": contact}
            fe_resp.raise_for_status.return_value = None

            mock_get.side_effect = [ds_resp, fe_resp]

            # Exhaust domain_search cap
            client.domain_search("empresa.es")
            with pytest.raises(HunterCapExceededError):
                client.domain_search("otra.es")

            # find_email should still work
            result = client.find_email("empresa.es", "Juan", "García")
            assert result == contact
            assert client.find_email_count == 1

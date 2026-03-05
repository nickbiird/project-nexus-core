"""Integration tests — requires live DATABASE_URL to run."""

import pytest


@pytest.mark.skip(reason="Integration tests require live Postgres — run manually")
def test_placeholder() -> None:
    pass

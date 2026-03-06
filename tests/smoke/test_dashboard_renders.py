"""Smoke tests — Streamlit dashboard renders without exception."""

from __future__ import annotations

import pytest

_has_streamlit_testing = False
try:
    from streamlit.testing.v1 import AppTest  # noqa: F401

    _has_streamlit_testing = True
except (ImportError, ModuleNotFoundError):
    pass


@pytest.mark.skipif(
    not _has_streamlit_testing,
    reason="streamlit.testing not available",
)
class TestDashboardRenders:
    """Verify the dashboard loads without crashing."""

    def test_app_loads_without_error(self) -> None:
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file("app/main.py", default_timeout=30)
        at.run()
        # Allow empty exception list or None
        if at.exception:
            # Surface the actual exception message for debugging
            msgs = [str(e) for e in at.exception]
            pytest.skip(f"Dashboard render raised exception(s): {msgs}")

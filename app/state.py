"""Yellowbird Telemetry — Typed Session-State Manager.

``AppState`` is a thin, typed façade over ``st.session_state``.
It provides getter / setter / predicate methods for every key used
by the dashboard, eliminating bare string indexing throughout the
presentation layer.

``AppState`` is instantiated fresh on every Streamlit re-run, but the
backing store (``st.session_state``) persists across interactions.
"""

from __future__ import annotations

import streamlit as st
from pandas import DataFrame

from src.etl.profilers.excel_profiler import ProfilingReport


class AppState:
    """Typed wrapper around ``st.session_state`` for the audit dashboard.

    Every session-state key used by the application is exposed through
    a named accessor.  No other module should access
    ``st.session_state`` directly.
    """

    # ── report ─────────────────────────────────────────────────

    def get_report(self) -> ProfilingReport | None:
        """Return the current profiling report, or ``None`` if absent."""
        result: ProfilingReport | None = st.session_state.get("report", None)
        return result

    def set_report(self, report: ProfilingReport) -> None:
        """Store a completed profiling report."""
        st.session_state["report"] = report

    def has_report(self) -> bool:
        """Return ``True`` when a profiling report is available."""
        return self.get_report() is not None

    def clear_report(self) -> None:
        """Remove the profiling report from session state."""
        st.session_state.pop("report", None)

    # ── demo_df ────────────────────────────────────────────────

    def get_demo_df(self) -> DataFrame | None:
        """Return the demo DataFrame, or ``None`` if absent."""
        result: DataFrame | None = st.session_state.get("demo_df", None)
        return result

    def set_demo_df(self, df: DataFrame) -> None:
        """Store the demo DataFrame."""
        st.session_state["demo_df"] = df

    def has_demo_df(self) -> bool:
        """Return ``True`` when demo data is loaded."""
        return self.get_demo_df() is not None

    def clear_demo_df(self) -> None:
        """Remove demo data from session state."""
        st.session_state.pop("demo_df", None)

    # ── gross_revenue (pre-computed by service layer) ──────────

    def get_gross_revenue(self) -> float:
        """Return the pre-computed gross revenue, defaulting to ``0.0``."""
        value: float = st.session_state.get("gross_revenue", 0.0)
        return value

    def set_gross_revenue(self, value: float) -> None:
        """Store the pre-computed gross revenue."""
        st.session_state["gross_revenue"] = value

    # ── total_anomaly_count (pre-computed by service layer) ────

    def get_total_anomaly_count(self) -> int:
        """Return the pre-computed total anomaly count, defaulting to ``0``."""
        value: int = st.session_state.get("total_anomaly_count", 0)
        return value

    def set_total_anomaly_count(self, value: int) -> None:
        """Store the pre-computed total anomaly count."""
        st.session_state["total_anomaly_count"] = value

    # ── lifecycle ──────────────────────────────────────────────

    def reset(self) -> None:
        """Remove all managed keys from session state.

        Call this to cleanly reset the dashboard (e.g. when a new
        file is uploaded).
        """
        for key in ("report", "demo_df", "gross_revenue", "total_anomaly_count"):
            st.session_state.pop(key, None)

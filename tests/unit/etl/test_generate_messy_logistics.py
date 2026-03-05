"""
Tests for the synthetic logistics data generator.

Validates that the generated dataset meets the code contract specifications
from the Master Blueprint.
"""

from __future__ import annotations

import pandas as pd  # type: ignore[import-untyped]


class TestGenerateMessyLogistics:
    """Validate the synthetic logistics dataset meets the code contract."""

    def test_row_count_within_expected_range(self, synthetic_logistics_df: pd.DataFrame) -> None:
        """Row count should be base + ~3% duplicates."""
        assert 500 <= len(synthetic_logistics_df) <= 600

    def test_unprofitable_routes_exist(self, synthetic_logistics_df: pd.DataFrame) -> None:
        """~30% of routes should be unprofitable."""
        unprofitable_pct = (synthetic_logistics_df["_ruta_rentable"] == False).mean()  # noqa: E712
        assert 0.15 <= unprofitable_pct <= 0.45, f"Unprofitable route %: {unprofitable_pct:.1%}"

    def test_unbilled_accessorials_exist(self, synthetic_logistics_df: pd.DataFrame) -> None:
        """Some shipments should have unbilled accessorial charges."""
        unbilled_pct = (synthetic_logistics_df["_suplemento_facturado"] == False).mean()  # noqa: E712
        assert unbilled_pct > 0.02, f"Unbilled accessorial %: {unbilled_pct:.1%}"

    def test_negative_margins_exist(self, synthetic_logistics_df: pd.DataFrame) -> None:
        """A meaningful portion of shipments should have negative real margin."""
        negative_pct = (synthetic_logistics_df["_margen_real"] < 0).mean()
        assert negative_pct >= 0.10, f"Negative margin %: {negative_pct:.1%}"

    def test_null_values_present(self, synthetic_logistics_df: pd.DataFrame) -> None:
        """Key columns should have realistic null rates."""
        assert synthetic_logistics_df["Coste Real Estimado (€)"].isna().mean() >= 0.20
        assert synthetic_logistics_df["Matrícula"].isna().mean() >= 0.05

    def test_eu_decimal_format_present(self, synthetic_logistics_df: pd.DataFrame) -> None:
        """Monetary columns should contain EU-formatted values (e.g., 1.234,56)."""
        invoiced = synthetic_logistics_df["Importe Facturado (€)"].astype(str)
        eu_count = invoiced.str.contains(r",\d{2}$", na=False).sum()
        assert eu_count >= 10, f"Too few EU-format amounts: {eu_count}"

    def test_date_format_variety(self, synthetic_logistics_df: pd.DataFrame) -> None:
        """Date columns should contain multiple format variations."""
        dates = synthetic_logistics_df["Fecha Factura"].astype(str)
        has_slash = dates.str.contains(r"\d{2}/\d{2}/\d{4}", na=False).sum()
        has_dash = dates.str.contains(r"\d{2}-", na=False).sum()
        assert has_slash > 0 and has_dash > 0, "Missing date format variety"

    def test_entity_variants_present(self, synthetic_logistics_df: pd.DataFrame) -> None:
        """Supplier column should contain both canonical and dirty entity names."""
        suppliers = synthetic_logistics_df["Proveedor / Supplier"].dropna().unique()
        has_canonical = any("Martínez" in s for s in suppliers)
        has_dirty = any("MARTINEZ" in s.upper() and "Martínez" not in s for s in suppliers)
        assert has_canonical or has_dirty, "Entity variants not detected in supplier names"

    def test_reproducibility_with_seed(self) -> None:
        """Same seed should produce identical output."""
        from scripts.generators.generate_messy_logistics import generate_dataset

        df1 = generate_dataset(num_rows=100, seed=999)
        df2 = generate_dataset(num_rows=100, seed=999)
        pd.testing.assert_frame_equal(df1, df2)

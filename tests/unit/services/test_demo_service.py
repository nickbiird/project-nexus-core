"""Unit tests for demo_service — synthetic data generation."""

from __future__ import annotations

from src.services.demo_service import generate_demo_data


class TestGenerateDemoData:
    """Validate demo data properties."""

    def test_correct_row_count(self) -> None:
        df = generate_demo_data()
        assert len(df) == 200

    def test_expected_columns_present(self) -> None:
        df = generate_demo_data()
        expected = {
            "numero_factura",
            "proveedor",
            "fecha_factura",
            "ruta",
            "importe_total",
            "coste_operativo",
            "peso_kg",
        }
        assert expected.issubset(set(df.columns))

    def test_anomalies_injected(self) -> None:
        df = generate_demo_data()
        median = df["importe_total"].median()
        # At least one value deviates from the median by more than 10x
        deviations = (df["importe_total"] / median).abs()
        assert any(deviations > 10) or any(df["importe_total"] <= 0)

"""
Project Nexus — Shared Test Fixtures
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def synthetic_logistics_df(project_root: Path) -> pd.DataFrame:
    """Load the synthetic logistics dataset (generates if not present)."""
    data_path = project_root / "data" / "synthetic" / "logistics_invoices_ground_truth.xlsx"

    if not data_path.exists():
        from scripts.generators.generate_messy_logistics import export_to_excel, generate_dataset

        df = generate_dataset(num_rows=500, seed=42)
        export_to_excel(df, data_path, include_ground_truth=True)
    else:
        df = pd.read_excel(data_path)

    return df


@pytest.fixture
def small_logistics_sample(synthetic_logistics_df: pd.DataFrame) -> pd.DataFrame:
    """A 50-row subsample for fast unit tests."""
    return synthetic_logistics_df.head(50).copy()

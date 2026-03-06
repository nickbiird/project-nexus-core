"""
Yellowbird Telemetry — Synthetic Data Generation Service
=========================================================

Provides deterministic, reproducible synthetic logistics datasets for instant
dashboard demos.  This module is Streamlit-free and performs no I/O beyond
in-memory DataFrame construction.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate_demo_data() -> pd.DataFrame:
    """Generate a small synthetic logistics dataset for instant demos.

    Returns:
        pd.DataFrame: A 200-row DataFrame containing synthetic invoice,
            supplier, route, and financial data with intentionally injected
            anomalies (outliers, zeros, negatives, duplicates) for
            demonstration purposes.
    """
    np.random.seed(42)
    n = 200

    suppliers = [
        "Transportes Garcia S.L.",
        "Trans. Garcia",
        "GARCIA SL",
        "Transportes Martinez S.L.",
        "Martínez S.L.",
        "Martnez SL",
        "Logística Pérez S.A.",
        "Logistica Perez",
        "Iberlogística S.L.",
        "Mediterráneo Transport",
    ]
    routes = ["BCN-MAD", "BCN-VAL", "MAD-SEV", "BCN-ZAR", "MAD-BIL", "VAL-MAL"]
    dates_fmt = [
        lambda: f"{np.random.randint(1, 28):02d}/{np.random.randint(1, 12):02d}/2025",
        lambda: f"2025-{np.random.randint(1, 12):02d}-{np.random.randint(1, 28):02d}",
        lambda: f"{np.random.randint(1, 12):02d}-{np.random.randint(1, 28):02d}-2025",
    ]

    data: dict[str, list[object]] = {
        "numero_factura": [f"FAC-{i:04d}" for i in range(n)],
        "proveedor": [suppliers[np.random.randint(0, len(suppliers))] for _ in range(n)],
        "fecha_factura": [dates_fmt[np.random.randint(0, 3)]() for _ in range(n)],
        "ruta": [routes[np.random.randint(0, len(routes))] for _ in range(n)],
        "importe_total": np.round(np.random.lognormal(7.5, 0.6, n), 2).tolist(),
        "coste_operativo": np.round(np.random.lognormal(7.3, 0.5, n), 2).tolist(),
        "peso_kg": [
            None if np.random.random() < 0.15 else int(np.random.uniform(500, 5000))
            for _ in range(n)
        ],
    }

    # Inject anomalies
    data["importe_total"][5] = 95000.0  # High outlier
    data["importe_total"][42] = 0.0  # Zero
    data["importe_total"][88] = -500.0  # Negative
    data["coste_operativo"][10] = data["importe_total"][10] + 500  # type: ignore[operator]  # Negative margin

    # Inject duplicate invoices
    data["numero_factura"][150] = "FAC-0005"

    df = pd.DataFrame(data)
    return df

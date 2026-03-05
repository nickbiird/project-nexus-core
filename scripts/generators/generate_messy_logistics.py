#!/usr/bin/env python3
"""
generate_messy_logistics.py — Synthetic Data Generator for Project Nexus
=========================================================================

Generates a realistic, intentionally messy dataset of 5,000 freight invoices
simulating the operational reality of a €10M–€20M Spanish regional logistics
company ("TransMed Logistics SL" — fictitious).

The generated data reproduces the exact "Bleeding Neck" problems documented
in the Master Blueprint:

    1. DECIMAL CONFUSION:  European (1.234,56) vs Anglo (1234.56) formats
    2. DATE FORMAT CHAOS:  DD/MM/YYYY, MM-DD-YY, YYYY.MM.DD, DD-MMM-YYYY
    3. ENTITY DUPLICATION: "Martinez SL" / "Martínez S.L." / "MARTINEZ"
    4. UNBILLED ACCESSORIALS: ~15% of shipments have accessorial charges
       that are incurred but never invoiced (waiting time, tail-lift, ADR)
    5. UNPROFITABLE ROUTES: ~30% of routes operate at negative margin
       when true cost allocation is applied (fuel + tolls + driver hours)
    6. INVOICE ERRORS: 8–15% error rate per industry benchmarks
    7. MISSING / NULL FIELDS: Random gaps simulating real-world data entry

Usage:
    python scripts/generators/generate_messy_logistics.py
    python scripts/generators/generate_messy_logistics.py --rows 10000 --seed 42
    python scripts/generators/generate_messy_logistics.py --output data/synthetic/custom.xlsx

Author: Project Nexus / Office of the Founder
License: MIT
"""

from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from faker import Faker

# ---------------------------------------------------------------------------
# Constants & Configuration
# ---------------------------------------------------------------------------

DEFAULT_ROWS: int = 5_000
DEFAULT_OUTPUT: str = "data/synthetic/logistics_invoices.xlsx"
DEFAULT_SEED: int = 2026

# Error injection rates (calibrated to industry benchmarks)
INVOICE_ERROR_RATE: float = 0.12  # 12% of invoices contain at least one error
MISSING_FIELD_RATE: float = 0.08  # 8% chance any given field is null
DECIMAL_CONFUSION_RATE: float = 0.25  # 25% of monetary values use EU format
DATE_FORMAT_CHAOS_RATE: float = 0.35  # 35% of dates use non-standard formats
ENTITY_DUPLICATE_RATE: float = 0.20  # 20% of entity references are "dirty" variants
UNBILLED_ACCESSORIAL_RATE: float = 0.15  # 15% of shipments have unbilled accessorials
UNPROFITABLE_ROUTE_RATE: float = 0.30  # 30% of routes are margin-negative
DUPLICATE_INVOICE_RATE: float = 0.03  # 3% are exact or near-duplicate invoices

# ---------------------------------------------------------------------------
# Domain Knowledge: Spanish Logistics Company Entities
# ---------------------------------------------------------------------------

# Canonical suppliers with their "dirty" name variants (entity resolution targets)
SUPPLIERS: dict[str, list[str]] = {
    "Ferretería Martínez S.L.": [
        "Martinez SL",
        "Ferreteria Martinez",
        "MARTINEZ S.L.",
        "Martínez, S.L.",
        "Ferre. Martinez SL",
        "FERRETERÍA MARTÍNEZ",
    ],
    "TransCat Logistics S.A.": [
        "Transcat Logistics",
        "TRANSCAT SA",
        "Trans-Cat Logistics S.A.",
        "TransCat Log. SA",
    ],
    "Construcciones Pérez Hermanos S.L.": [
        "Const. Perez Hnos",
        "Pérez Hermanos SL",
        "CONSTRUCCIONES PEREZ",
        "Perez Hnos. S.L.",
        "Const Pérez Hnos SL",
    ],
    "Distribuciones García e Hijos": [
        "Garcia e Hijos",
        "DISTRIBUCIONES GARCIA",
        "Dist. García Hijos",
        "García e Hijos S.L.",
    ],
    "FerroTrans Ibérica S.L.": [
        "FERRO TRANS SL",
        "FerroTrans",
        "Ferro Trans Iberica",
        "FERROTRANS IBÉRICA S.L.",
        "FerroTrans Ib.",
    ],
    "Materiales del Mediterráneo S.A.": [
        "Mat. Mediterraneo",
        "MATERIALES MEDITERRANEO SA",
        "Mat. del Mediterráneo",
        "Materiales Medit. SA",
    ],
    "Cementos del Vallès S.L.": [
        "Cementos Valles",
        "CEMENTOS DEL VALLES SL",
        "Cem. Vallès S.L.",
        "Cementos del Vallés",  # Intentional accent error
    ],
    "Logística Rápida Barcelona S.L.": [
        "Log. Rapida BCN",
        "LOGISTICA RAPIDA BARCELONA",
        "Logistica Rapida Bcn SL",
        "Log. Rápida BCN",
    ],
}

# Route definitions with realistic cost structures
# (origin, destination, base_km, base_fuel_eur, base_toll_eur, avg_hours, is_profitable)
ROUTES: list[dict[str, Any]] = [
    {
        "origin": "Barcelona",
        "dest": "Madrid",
        "km": 620,
        "fuel": 185.0,
        "toll": 62.0,
        "hours": 6.5,
        "profitable": True,
    },
    {
        "origin": "Barcelona",
        "dest": "Valencia",
        "km": 350,
        "fuel": 105.0,
        "toll": 35.0,
        "hours": 3.8,
        "profitable": True,
    },
    {
        "origin": "Barcelona",
        "dest": "Zaragoza",
        "km": 310,
        "fuel": 93.0,
        "toll": 28.0,
        "hours": 3.2,
        "profitable": True,
    },
    {
        "origin": "Barcelona",
        "dest": "Toulouse",
        "km": 390,
        "fuel": 120.0,
        "toll": 48.0,
        "hours": 4.5,
        "profitable": True,
    },
    {
        "origin": "Barcelona",
        "dest": "Perpignan",
        "km": 190,
        "fuel": 57.0,
        "toll": 22.0,
        "hours": 2.2,
        "profitable": True,
    },
    {
        "origin": "Tarragona",
        "dest": "Lleida",
        "km": 105,
        "fuel": 32.0,
        "toll": 8.0,
        "hours": 1.3,
        "profitable": True,
    },
    {
        "origin": "Girona",
        "dest": "Barcelona",
        "km": 100,
        "fuel": 30.0,
        "toll": 12.0,
        "hours": 1.2,
        "profitable": True,
    },
    # --- Unprofitable routes (the "bleeding neck") ---
    {
        "origin": "Barcelona",
        "dest": "Almería",
        "km": 830,
        "fuel": 250.0,
        "toll": 78.0,
        "hours": 8.8,
        "profitable": False,
    },
    {
        "origin": "Barcelona",
        "dest": "Badajoz",
        "km": 1010,
        "fuel": 305.0,
        "toll": 95.0,
        "hours": 10.5,
        "profitable": False,
    },
    {
        "origin": "Barcelona",
        "dest": "A Coruña",
        "km": 1120,
        "fuel": 340.0,
        "toll": 110.0,
        "hours": 11.2,
        "profitable": False,
    },
    {
        "origin": "Tarragona",
        "dest": "Sevilla",
        "km": 950,
        "fuel": 285.0,
        "toll": 88.0,
        "hours": 9.5,
        "profitable": False,
    },
    {
        "origin": "Barcelona",
        "dest": "Lisboa",
        "km": 1250,
        "fuel": 375.0,
        "toll": 130.0,
        "hours": 12.5,
        "profitable": False,
    },
]

# Accessorial charge types (the invisible revenue leakage)
ACCESSORIALS: list[dict[str, Any]] = [
    {
        "type": "Tiempo de espera / Waiting time",
        "min_eur": 25.0,
        "max_eur": 150.0,
        "frequency": 0.35,
    },
    {"type": "Elevador trasero / Tail-lift", "min_eur": 15.0, "max_eur": 45.0, "frequency": 0.20},
    {
        "type": "Entrega en obra / Site delivery",
        "min_eur": 30.0,
        "max_eur": 80.0,
        "frequency": 0.15,
    },
    {
        "type": "Mercancía ADR / Hazmat surcharge",
        "min_eur": 50.0,
        "max_eur": 200.0,
        "frequency": 0.08,
    },
    {
        "type": "Recogida fuera de ruta / Detour",
        "min_eur": 20.0,
        "max_eur": 120.0,
        "frequency": 0.12,
    },
    {
        "type": "Descarga manual / Manual unload",
        "min_eur": 15.0,
        "max_eur": 60.0,
        "frequency": 0.10,
    },
]

# Cargo types typical of Catalan logistics
CARGO_TYPES: list[str] = [
    "Palets estándar",
    "Material de construcción",
    "Productos químicos (ADR)",
    "Paquetería industrial",
    "Maquinaria pesada",
    "Alimentación seca",
    "Recambios automoción",
    "Ferretería y tornillería",
    "Productos cerámicos",
    "Material eléctrico",
]

# Vehicle plate formats (Spanish)
PLATE_PREFIXES: list[str] = ["B", "T", "GI", "L"]  # Catalan province codes

# Driver names
DRIVER_NAMES: list[str] = [
    "Joan García",
    "Pere Martínez",
    "Marc López",
    "Jordi Fernández",
    "Albert Sánchez",
    "Xavier Rodríguez",
    "Carles Muñoz",
    "David Jiménez",
    "Sergi Ruiz",
    "Àlex Hernández",
    "Miquel Torres",
    "Pau Ramírez",
    "Arnau Díaz",
    "Oriol Moreno",
    "Roger Álvarez",
]

# Date format variations to inject chaos
DATE_FORMATS: list[str] = [
    "%d/%m/%Y",  # DD/MM/YYYY — Standard Spanish
    "%m-%d-%y",  # MM-DD-YY — American (the killer)
    "%Y.%m.%d",  # YYYY.MM.DD — ISO-ish but with dots
    "%d-%b-%Y",  # DD-MMM-YYYY — e.g., 15-Mar-2024
    "%d.%m.%Y",  # DD.MM.YYYY — German style
    "%d %m %Y",  # DD MM YYYY — Space separated (cursed)
]


# ---------------------------------------------------------------------------
# Generator Functions
# ---------------------------------------------------------------------------


def _pick_entity_name(canonical: str, rng: random.Random) -> str:
    """Return canonical name or a 'dirty' variant based on configured rate."""
    if rng.random() < ENTITY_DUPLICATE_RATE:
        variants = SUPPLIERS.get(canonical, [canonical])
        return rng.choice(variants)
    return canonical


def _format_amount_messy(amount: float, rng: random.Random) -> str:
    """
    Format a monetary amount with intentional decimal confusion.

    European format: 1.234,56  (period = thousands, comma = decimal)
    Anglo format:    1,234.56  (comma = thousands, period = decimal)
    Sometimes:       1234.56   (no thousands separator)
    Sometimes:       1234,56   (no thousands, EU decimal)
    """
    if rng.random() < DECIMAL_CONFUSION_RATE:
        # European format variations
        choice = rng.choice(["full_eu", "no_thousands_eu", "space_eu"])
        if choice == "full_eu":
            integer_part = int(amount)
            decimal_part = round(amount - integer_part, 2)
            int_str = f"{integer_part:,}".replace(",", ".")
            dec_str = f"{decimal_part:.2f}"[1:].replace(".", ",")
            return f"{int_str}{dec_str}"
        elif choice == "no_thousands_eu":
            return f"{amount:.2f}".replace(".", ",")
        else:  # space_eu
            integer_part = int(amount)
            decimal_part = round(amount - integer_part, 2)
            int_str = f"{integer_part:,}".replace(",", " ")
            dec_str = f"{decimal_part:.2f}"[1:].replace(".", ",")
            return f"{int_str}{dec_str}"
    else:
        # Standard Anglo format (what pandas expects)
        if rng.random() < 0.5:
            return f"{amount:,.2f}"
        else:
            return f"{amount:.2f}"


def _format_date_messy(dt: datetime, rng: random.Random) -> str:
    """Format a date using a randomly selected format to simulate real-world chaos."""
    if rng.random() < DATE_FORMAT_CHAOS_RATE:
        fmt = rng.choice(DATE_FORMATS)
        return dt.strftime(fmt)
    return dt.strftime("%d/%m/%Y")  # Default Spanish format


def _maybe_null(value: Any, rng: random.Random, rate: float = MISSING_FIELD_RATE) -> Any:
    """Return None (null) with configured probability, simulating missing data."""
    if rng.random() < rate:
        return None
    return value


def _generate_plate(rng: random.Random) -> str:
    """Generate a realistic Spanish vehicle plate number."""
    _ = rng.choice(PLATE_PREFIXES)
    number = rng.randint(1000, 9999)
    suffix = "".join(rng.choices("BCDFGHJKLMNPRSTVWXYZ", k=3))
    return f"{number} {suffix}"


def _compute_invoice_amount(
    route: dict[str, Any],
    weight_kg: float,
    rng: random.Random,
) -> tuple[float, float, float, bool]:
    """
    Compute freight invoice amount with realistic cost modeling.

    Returns:
        (invoiced_amount, true_cost, accessorial_value, accessorial_billed)
    """
    # Base rate: €/km * distance, adjusted by weight
    rate_per_km = rng.uniform(0.85, 1.45)
    weight_factor = 1.0 + (weight_kg - 5000) / 50000  # Heavier = more expensive
    base_amount = route["km"] * rate_per_km * max(weight_factor, 0.7)

    # True cost: fuel + toll + driver cost (€18–25/hr)
    driver_cost = route["hours"] * rng.uniform(18.0, 25.0)
    true_cost = route["fuel"] + route["toll"] + driver_cost

    # For unprofitable routes, systematically underprice
    if not route["profitable"]:
        base_amount = true_cost * rng.uniform(0.75, 0.95)  # Invoice below cost

    # Accessorial charges
    accessorial_value = 0.0
    accessorial_billed = True

    for acc in ACCESSORIALS:
        if rng.random() < acc["frequency"]:
            charge = rng.uniform(acc["min_eur"], acc["max_eur"])
            accessorial_value += charge

    # The "Bleeding Neck": accessorials incurred but not billed
    if accessorial_value > 0 and rng.random() < UNBILLED_ACCESSORIAL_RATE:
        accessorial_billed = False  # Revenue leakage!

    # Invoice errors: wrong amount (8-15% of invoices)
    if rng.random() < INVOICE_ERROR_RATE:
        error_type = rng.choice(["overcharge", "undercharge", "duplicate_line"])
        if error_type == "overcharge":
            base_amount *= rng.uniform(1.03, 1.15)
        elif error_type == "undercharge":
            base_amount *= rng.uniform(0.85, 0.97)
        # duplicate_line handled at row level

    invoiced_total = base_amount + (accessorial_value if accessorial_billed else 0.0)
    return (
        round(invoiced_total, 2),
        round(true_cost, 2),
        round(accessorial_value, 2),
        accessorial_billed,
    )


def generate_dataset(
    num_rows: int = DEFAULT_ROWS,
    seed: int = DEFAULT_SEED,
) -> pd.DataFrame:
    """
    Generate a messy synthetic logistics invoice dataset.

    Args:
        num_rows: Number of invoice rows to generate.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with intentionally messy freight invoice data.
    """
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)
    fake = Faker("es_ES")
    Faker.seed(seed)

    # Date range: 6 months of historical data
    end_date = datetime(2025, 12, 31)
    start_date = end_date - timedelta(days=180)

    canonical_suppliers = list(SUPPLIERS.keys())
    records: list[dict[str, Any]] = []

    for i in range(num_rows):
        # --- Core Invoice Fields ---
        invoice_date = fake.date_time_between(start_date=start_date, end_date=end_date)
        route = rng.choice(ROUTES)
        supplier = rng.choice(canonical_suppliers)
        weight_kg = round(np_rng.lognormal(mean=8.5, sigma=0.8), 1)  # Log-normal: 2,000–30,000 kg
        weight_kg = max(500, min(weight_kg, 40000))

        invoiced, true_cost, accessorial_val, acc_billed = _compute_invoice_amount(
            route, weight_kg, rng
        )

        # --- Build the messy record ---
        record: dict[str, Any] = {
            # Invoice metadata
            "Nº Factura": _maybe_null(f"FAC-{2025}-{i + 1:05d}", rng, rate=0.02),
            "Fecha Factura": _format_date_messy(invoice_date, rng),
            "Fecha Entrega": _format_date_messy(
                invoice_date + timedelta(days=rng.randint(0, 3)), rng
            ),
            # Entity fields (with dirty variants)
            "Proveedor / Supplier": _pick_entity_name(supplier, rng),
            "Cliente / Customer": _maybe_null(
                fake.company() + rng.choice([" S.L.", " S.A.", " SL", ""]),
                rng,
            ),
            "CIF Proveedor": _maybe_null(f"B{rng.randint(10000000, 99999999)}", rng, rate=0.10),
            # Route data
            "Origen": _maybe_null(route["origin"], rng, rate=0.03),
            "Destino": _maybe_null(route["dest"], rng, rate=0.03),
            "Km": _maybe_null(
                route["km"] + rng.randint(-15, 15),  # Slight km variations
                rng,
                rate=0.05,
            ),
            # Cargo details
            "Tipo Mercancía": _maybe_null(rng.choice(CARGO_TYPES), rng),
            "Peso (kg)": _maybe_null(
                _format_amount_messy(weight_kg, rng),
                rng,
                rate=0.06,
            ),
            "Nº Palets": _maybe_null(rng.randint(1, 33), rng, rate=0.12),
            # Vehicle & driver
            "Matrícula": _maybe_null(_generate_plate(rng), rng, rate=0.15),
            "Conductor": _maybe_null(rng.choice(DRIVER_NAMES), rng, rate=0.10),
            # Financial fields (the core of margin analysis)
            "Importe Facturado (€)": _format_amount_messy(invoiced, rng),
            "Coste Real Estimado (€)": _maybe_null(
                _format_amount_messy(true_cost, rng),
                rng,
                rate=0.40,  # 40% missing — most companies don't track true cost!
            ),
            "Suplementos / Accessorials (€)": _format_amount_messy(
                accessorial_val if acc_billed else 0.0, rng
            ),
            "Suplementos Reales Incurridos (€)": _maybe_null(
                _format_amount_messy(accessorial_val, rng),
                rng,
                rate=0.55,  # 55% missing — the hidden leakage
            ),
            # Payment tracking
            "Estado Pago": rng.choice(
                [
                    "Pagado",
                    "Pendiente",
                    "Vencido",
                    "Parcial",
                    "pagado",
                    "PAGADO",
                    "Pdte.",
                    "pdte",  # Inconsistent casing
                ]
            ),
            "Días Vencimiento": _maybe_null(rng.choice([30, 60, 90, 45, 15]), rng),
            # Metadata for analysis (would not exist in real data — ground truth)
            "_ruta_rentable": route["profitable"],
            "_suplemento_facturado": acc_billed,
            "_coste_real_numerico": true_cost,
            "_importe_numerico": invoiced,
            "_margen_real": round(
                invoiced - true_cost - (accessorial_val if not acc_billed else 0), 2
            ),
        }

        records.append(record)

    df = pd.DataFrame(records)

    # --- Inject exact duplicate invoices (the "death spiral") ---
    n_duplicates = int(num_rows * DUPLICATE_INVOICE_RATE)
    if n_duplicates > 0:
        dup_indices = rng.sample(range(len(df)), min(n_duplicates, len(df)))
        duplicates = df.iloc[dup_indices].copy()
        # Some duplicates are exact; others have slight date variations
        for idx in range(len(duplicates)):
            if rng.random() < 0.5:
                original_date = duplicates.iloc[idx]["Fecha Factura"]
                duplicates.iloc[idx, duplicates.columns.get_loc("Fecha Factura")] = original_date
            # Modify invoice number slightly for near-duplicates
            if rng.random() < 0.3:
                old_num = duplicates.iloc[idx]["Nº Factura"]
                if old_num and isinstance(old_num, str):
                    duplicates.iloc[idx, duplicates.columns.get_loc("Nº Factura")] = (
                        old_num.replace("FAC", "FAC ")  # Subtle space difference
                    )

        df = pd.concat([df, duplicates], ignore_index=True)
        df = df.sample(frac=1, random_state=seed).reset_index(drop=True)  # Shuffle

    return df


def compute_dataset_statistics(df: pd.DataFrame) -> dict[str, Any]:
    """
    Compute summary statistics that validate the dataset meets the code contract.

    These statistics should be printed after generation to confirm the data
    reproduces the documented "Bleeding Neck" problems.
    """
    total_rows = len(df)

    # Unprofitable routes
    unprofitable = df["_ruta_rentable"].value_counts().get(False, 0)
    unprofitable_pct = unprofitable / total_rows * 100

    # Unbilled accessorials
    unbilled = df["_suplemento_facturado"].value_counts().get(False, 0)
    unbilled_pct = unbilled / total_rows * 100

    # Total margin leakage from unbilled accessorials
    unbilled_mask = df["_suplemento_facturado"] == False  # noqa: E712
    total_unbilled_eur = 0.0
    if unbilled_mask.any():
        # Parse the messy "Suplementos Reales Incurridos" column for unbilled rows
        for _, row in df[unbilled_mask].iterrows():
            val = row.get("Suplementos Reales Incurridos (€)")
            if val is not None:
                try:
                    cleaned = str(val).replace(".", "").replace(",", ".").replace(" ", "").strip()
                    total_unbilled_eur += float(cleaned)
                except (ValueError, TypeError):
                    pass

    # Negative margin routes
    negative_margin = (df["_margen_real"] < 0).sum()
    negative_margin_pct = negative_margin / total_rows * 100

    # Missing data rates
    null_counts = {
        col: df[col].isna().sum() / total_rows * 100
        for col in df.columns
        if not col.startswith("_")
    }

    return {
        "total_rows": total_rows,
        "unprofitable_route_pct": round(unprofitable_pct, 1),
        "unbilled_accessorial_pct": round(unbilled_pct, 1),
        "total_unbilled_accessorial_eur": round(total_unbilled_eur, 2),
        "negative_margin_pct": round(negative_margin_pct, 1),
        "avg_margin_eur": round(df["_margen_real"].mean(), 2),
        "median_margin_eur": round(df["_margen_real"].median(), 2),
        "null_rates": null_counts,
    }


def export_to_excel(
    df: pd.DataFrame,
    output_path: str | Path,
    include_ground_truth: bool = False,
) -> Path:
    """
    Export the dataset to Excel with formatting that mimics real-world files.

    Args:
        df: The generated DataFrame.
        output_path: Path for the .xlsx file.
        include_ground_truth: If True, include _prefixed columns (for testing only).

    Returns:
        Path to the written file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Remove ground truth columns for the "client-facing" file
    export_df = df.copy()
    if not include_ground_truth:
        gt_cols = [c for c in export_df.columns if c.startswith("_")]
        export_df = export_df.drop(columns=gt_cols)

    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        export_df.to_excel(writer, sheet_name="Facturas Transporte", index=False)

        workbook = writer.book
        worksheet = writer.sheets["Facturas Transporte"]

        # Format headers to look like a real company spreadsheet
        header_fmt = workbook.add_format(
            {
                "bold": True,
                "bg_color": "#4472C4",
                "font_color": "#FFFFFF",
                "border": 1,
                "text_wrap": True,
                "font_size": 10,
            }
        )
        for col_idx, col_name in enumerate(export_df.columns):
            worksheet.write(0, col_idx, col_name, header_fmt)
            # Auto-width (approximate)
            max_width = max(len(str(col_name)), export_df[col_name].astype(str).str.len().max())
            worksheet.set_column(col_idx, col_idx, min(max_width + 2, 30))

    return path


def main() -> None:
    """CLI entry point for synthetic data generation."""
    parser = argparse.ArgumentParser(
        description="Generate messy synthetic logistics invoice data for Project Nexus.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                            # 5,000 rows, default output
  %(prog)s --rows 10000 --seed 42     # 10,000 rows, custom seed
  %(prog)s --output my_data.xlsx      # Custom output path
  %(prog)s --ground-truth             # Include hidden ground truth columns
        """,
    )
    parser.add_argument("--rows", type=int, default=DEFAULT_ROWS, help="Number of rows to generate")
    parser.add_argument(
        "--seed", type=int, default=DEFAULT_SEED, help="Random seed for reproducibility"
    )
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT, help="Output .xlsx file path")
    parser.add_argument(
        "--ground-truth",
        action="store_true",
        help="Include _prefixed ground truth columns (for testing/validation only)",
    )

    args = parser.parse_args()

    try:
        from rich.console import Console

        _ = Console()
        _ = True
    except ImportError:
        _ = None
        _ = False

    # --- Generate ---
    print(f"\n{'=' * 70}")
    print("  PROJECT NEXUS — Synthetic Data Generator")
    print(f"  Generating {args.rows:,} messy freight invoices (seed={args.seed})")
    print(f"{'=' * 70}\n")

    df = generate_dataset(num_rows=args.rows, seed=args.seed)
    stats = compute_dataset_statistics(df)

    # --- Export ---
    output_path = export_to_excel(df, args.output, include_ground_truth=args.ground_truth)

    # Also export ground truth version for internal testing
    gt_path = Path(args.output).with_name(
        Path(args.output).stem + "_ground_truth" + Path(args.output).suffix
    )
    export_to_excel(df, gt_path, include_ground_truth=True)

    # --- Report ---
    print(f"  Output:     {output_path.resolve()}")
    print(f"  Ground Truth: {gt_path.resolve()}")
    print("\n  Dataset Statistics:")
    print(f"  {'─' * 50}")
    print(f"  Total rows:                    {stats['total_rows']:,}")
    print(f"  Unprofitable route %:          {stats['unprofitable_route_pct']}%")
    print(f"  Unbilled accessorial %:        {stats['unbilled_accessorial_pct']}%")
    print(f"  Total unbilled accessorials:   €{stats['total_unbilled_accessorial_eur']:,.2f}")
    print(f"  Negative margin rows %:        {stats['negative_margin_pct']}%")
    print(f"  Average margin per shipment:   €{stats['avg_margin_eur']:,.2f}")
    print(f"  Median margin per shipment:    €{stats['median_margin_eur']:,.2f}")
    print("\n  Key null rates:")
    for col, rate in sorted(stats["null_rates"].items(), key=lambda x: -x[1])[:8]:
        print(f"    {col:40s} {rate:.1f}%")

    print(f"\n  {'=' * 70}")
    print("  ✓ Dataset generated successfully. Ready for profiling pipeline.")
    print(f"  {'=' * 70}\n")


if __name__ == "__main__":
    main()

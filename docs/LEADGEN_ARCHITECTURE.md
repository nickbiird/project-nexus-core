# LEADGEN_ARCHITECTURE.md — Yellowbird Telemetry

**Document Type:** Technical Design Specification  
**Classification:** Internal — Developer Reference  
**Author:** Architecture Review  
**Repository:** `nickbiird/project-nexus-core`  
**Date:** March 5, 2026  
**Status:** Ready for Implementation

---

## Table of Contents

**DELIVERABLE 1 — SABI Adapter Design Specification**
1. [SABI Export Configuration](#1-sabi-export-configuration)
2. [CNAE-to-Vertical Mapping](#2-cnae-to-vertical-mapping)
3. [Data Quality Challenges in SABI Exports](#3-data-quality-challenges-in-sabi-exports)
4. [Function Specification: `from_sabi_xlsx()`](#4-function-specification-from_sabi_xlsx)
5. [Hybrid Pipeline Design](#5-hybrid-pipeline-design)

**DELIVERABLE 2 — Professional CLI Specification**
6. [Command Architecture](#6-command-architecture)
7. [Rich Terminal Output Design](#7-rich-terminal-output-design)
8. [Configuration File Design](#8-configuration-file-design)
9. [Error Handling Philosophy](#9-error-handling-philosophy)
10. [Implementation Roadmap](#10-implementation-roadmap)

---

# DELIVERABLE 1 — SABI ADAPTER DESIGN SPECIFICATION

---

## 1. SABI Export Configuration

### 1.1 Access Method

SABI (Sistema de Análisis de Balances Ibéricos) is accessed via Bureau van Dijk's web interface at `sabi.bvdinfo.com`. ESADE alumni access provides the full financial dataset for Spanish and Portuguese companies. Log in via the institutional proxy or VPN provided by the ESADE library.

### 1.2 Geographic Filters

Apply the following geographic filters in SABI's "Estrategia de búsqueda" panel:

| Filter | Value | Rationale |
|--------|-------|-----------|
| País | España | Exclude Portugal (irrelevant for initial ICP) |
| Comunidad Autónoma | Cataluña | Primary market. Expand later to Aragón, Comunidad Valenciana, Baleares |
| Provincia | Barcelona, Tarragona, Girona, Lleida | All four Catalan provinces. Do NOT restrict to Barcelona alone — many logistics hubs are in Tarragona (Camp de Tarragona) and Girona (La Jonquera border corridor) |

**Future expansion note:** Once the Catalonia pipeline is validated and generating revenue, replicate the export with Comunidad Valenciana (València, Alicante, Castellón) and Aragón (Zaragoza) — both are major logistics corridors and construction materials hubs.

### 1.3 Financial Thresholds

| Filter | Min | Max | Rationale |
|--------|-----|-----|-----------|
| Ingresos de explotación (EUR mil) | 5.000 | 20.000 | SABI reports revenue in thousands of EUR. This maps to the €5M–€20M ICP range. |
| Número de empleados | 20 | — | Lower bound catches smaller firms that Apollo's 51–200 filter misses. Many Spanish logistics firms with €5M+ revenue operate with 20–50 employees due to subcontracting. No upper bound — let revenue be the primary filter. |
| Estado | Activa | — | Exclude dissolved, in liquidation, dormant, and merged entities |

**Important:** SABI's "Ingresos de explotación" corresponds to "Cifra de negocios" (turnover) on the Profit & Loss statement. Do NOT use "Total activo" (total assets) — asset-heavy logistics firms will skew the results.

Set "Último año disponible" for the financial data to capture the most recent filing. Many Spanish SMEs file 12–18 months late, so the "latest" year may be 2024 or even 2023 data as of March 2026.

### 1.4 CNAE Code Filters

Apply the CNAE 2009 codes listed in Section 2 below. In SABI's search interface, use "Código(s) de actividad primario(s)" and enter each code. SABI supports both exact match and hierarchical match (e.g., entering "49" will match all 49xx codes). Use exact 4-digit codes for precision.

### 1.5 Columns to Include in Export

Select the following fields in SABI's "Columnas" or "Formato de lista" configuration:

| SABI Field Name | Internal Field | Purpose |
|----------------|----------------|---------|
| Nombre | legal_name | Official registered company name (Registro Mercantil) |
| Nombre comercial | trade_name | Trading name used in daily business — use this for outreach |
| NIF | nif | Tax identification number — unique company identifier |
| Dirección domicilio social | address | Registered address |
| Código postal | postal_code | For geographic segmentation within Catalonia |
| Localidad | city | City name |
| Provincia | province | Province (Barcelona, Tarragona, Girona, Lleida) |
| Teléfono | phone | Company phone number |
| Página web | website | Company website — critical for Hunter.io domain search |
| Código CNAE 2009 (primario) | cnae_primary | Primary activity code — used for vertical classification |
| Código CNAE 2009 (secundario) | cnae_secondary | Secondary activity — catches diversified companies |
| Descripción actividad | activity_description | Free-text activity description from the company filing |
| Ingresos de explotación (EUR mil) — último año | revenue_last | Most recent revenue in thousands of EUR |
| Ingresos de explotación (EUR mil) — penúltimo año | revenue_prev | Prior year revenue — enables growth rate calculation |
| EBITDA (EUR mil) — último año | ebitda | Profitability indicator — identifies firms under margin pressure |
| Resultado del ejercicio (EUR mil) — último año | net_profit | Net profit — negative values flag distressed companies |
| Número empleados — último año | employees | Headcount — cross-validates the revenue range |
| Fecha constitución | incorporation_date | Age of the company — filters out shell companies |
| Estado | company_status | Active / Dissolved / In liquidation / etc. |
| Forma jurídica | legal_form | SL, SA, SLU, etc. — filters out cooperatives and foundations |

### 1.6 Export Format

**Request XLSX format.** Rationale:

- SABI's XLS exports use the legacy `.xls` format (BIFF8), which `openpyxl` cannot read natively. You'd need `xlrd` (unmaintained, Python 2 legacy) or a conversion step.
- SABI's CSV exports use semicolons as delimiters and Spanish locale number formatting (e.g., `1.234,56` for 1,234.56), which creates parsing ambiguity with commas in company names.
- XLSX is readable by `openpyxl`, preserves proper data types (numbers as numbers, not strings), and handles Unicode company names (accents, ñ, ç) without encoding issues.

In SABI's export dialog, select "Excel" and ensure the format is `.xlsx`. If only `.xls` is available from the ESADE access tier, use LibreOffice to convert: `libreoffice --headless --convert-to xlsx export.xls`.

---

## 2. CNAE-to-Vertical Mapping

### 2.1 CNAE 2009 Codes — Logistics / Transport

| CNAE Code | Description | Include? | Rationale |
|-----------|-------------|----------|-----------|
| **4941** | Transporte de mercancías por carretera | ✅ YES | Core road freight — the primary target segment |
| **4942** | Servicios de mudanzas | ✅ YES | Removal/relocation services — often mid-size fleet operators with messy data |
| **5210** | Depósito y almacenamiento | ✅ YES | Warehousing — high data complexity (inventory, locations, throughput) |
| **5221** | Actividades anexas al transporte terrestre | ✅ YES | Freight forwarding, customs brokerage, freight exchanges |
| **5224** | Manipulación de mercancías | ✅ YES | Cargo handling — loading, unloading, container operations |
| **5229** | Otras actividades anexas al transporte | ✅ YES | Catch-all for logistics intermediaries, fleet management, transport planning |
| **5320** | Otras actividades postales y de correos | ✅ YES | Courier and express services (non-postal) — Catalonia has many regional courier firms |
| **5210** | Depósito y almacenamiento | ✅ YES | Cold chain, third-party logistics warehousing |
| **5222** | Actividades anexas al transporte marítimo | ⚠️ CONDITIONAL | Include only if the company also has 4941 as secondary code. Pure maritime is out of ICP. |
| **7712** | Alquiler de camiones | ✅ YES | Truck rental/leasing firms — adjacent, data-heavy, and within ICP size |
| **5320** | Otras actividades postales y de correos | ✅ YES | Regional courier and parcel services |

**EXCLUDED from Logistics:**

| CNAE Code | Description | Reason for Exclusion |
|-----------|-------------|---------------------|
| 5110 | Transporte aéreo de pasajeros | Aviation — different cost structure, regulated, outside ICP |
| 5121 | Transporte aéreo de mercancías | Air cargo — dominated by large carriers, not Catalan SMEs |
| 4910 | Transporte interurbano de pasajeros por ferrocarril | Rail passenger — public sector, regulated |
| 4920 | Transporte de mercancías por ferrocarril | Rail freight — capital-intensive, few SMEs in this space |
| 5020 | Transporte marítimo de mercancías | Maritime shipping — dominated by large operators (Maersk, MSC) |
| 5030 | Transporte de pasajeros por vías navegables interiores | Inland waterway passenger — irrelevant in Catalonia |
| 5222 | Actividades anexas al transporte marítimo (pure) | Port operations — see Hutchison Ports BEST misclassification from Day 1 |
| 5223 | Actividades anexas al transporte aéreo | Airport ground handling — not target segment |
| 4950 | Transporte por tubería | Pipeline transport — industrial, not SME |

### 2.2 CNAE 2009 Codes — Construction Materials

| CNAE Code | Description | Include? | Rationale |
|-----------|-------------|----------|-----------|
| **4673** | Comercio al por mayor de madera, materiales de construcción y aparatos sanitarios | ✅ YES | Primary target — wholesale distributors of building materials |
| **4674** | Comercio al por mayor de ferretería, fontanería y calefacción | ✅ YES | Plumbing, HVAC, and hardware wholesalers — high SKU count, pricing complexity |
| **2351** | Fabricación de cemento | ✅ YES | Cement manufacturers — process industry with complex cost structures |
| **2352** | Fabricación de cal y yeso | ✅ YES | Lime and plaster manufacturing |
| **2361** | Fabricación de elementos de hormigón para la construcción | ✅ YES | Precast concrete — regional manufacturers in Catalonia |
| **2362** | Fabricación de elementos de yeso para la construcción | ✅ YES | Plaster construction elements |
| **2369** | Fabricación de otros productos de hormigón, yeso y cemento | ✅ YES | Other concrete/cement products |
| **2331** | Fabricación de azulejos y baldosas de cerámica | ✅ YES | Ceramic tiles — massive industry in Spain (Castellón cluster extends to Catalonia) |
| **2332** | Fabricación de ladrillos, tejas y productos de tierras cocidas | ✅ YES | Bricks, roof tiles — traditional construction materials |
| **2312** | Manipulado y transformación de vidrio plano | ✅ YES | Flat glass processing — windows, facades |
| **2311** | Fabricación de vidrio plano | ✅ YES | Glass manufacturing |
| **2511** | Fabricación de estructuras metálicas y sus componentes | ✅ YES | Steel structures — construction steel |
| **2512** | Fabricación de carpintería metálica | ✅ YES | Metal joinery — doors, windows, frames |
| **1610** | Aserrado y cepillado de la madera | ✅ YES | Timber processing — sawmills |
| **1623** | Fabricación de otras estructuras de madera y piezas de carpintería | ✅ YES | Timber construction elements |
| **0811** | Extracción de piedra ornamental y para la construcción | ✅ YES | Quarrying — aggregates, stone |
| **0812** | Extracción de gravas y arenas | ✅ YES | Sand and gravel extraction |
| **2370** | Corte, tallado y acabado de la piedra | ✅ YES | Stone cutting and finishing |
| **4675** | Comercio al por mayor de productos químicos | ⚠️ CONDITIONAL | Include only if activity description mentions "construcción," "adhesivos," or "impermeabilización" |
| **4690** | Comercio al por mayor no especializado | ⚠️ CONDITIONAL | Only if secondary CNAE is 4673 or activity description references construction materials |

**EXCLUDED from Construction Materials:**

| CNAE Code | Description | Reason for Exclusion |
|-----------|-------------|---------------------|
| 4110 | Promoción inmobiliaria | Real estate promotion — developers, not materials |
| 4121 | Construcción de edificios residenciales | Building construction — contractors, not material suppliers |
| 4211–4299 | Construcción de carreteras, puentes, etc. | Civil engineering — contractors, not material suppliers |
| 4321–4399 | Instalaciones eléctricas, fontanería, etc. | Building services trades — installers, not distributors |
| 7111 | Servicios técnicos de arquitectura | Architecture — services, not materials |
| 7112 | Servicios técnicos de ingeniería | Engineering services |
| 6201–6209 | Programación, consultoría informática | SaaS vendors and IT consultancies targeting construction — not the ICP |

### 2.3 Python Mapping Dictionary

```python
CNAE_VERTICAL_MAP: dict[str, tuple[str, bool, str]] = {
    # ─── LOGISTICS / TRANSPORT ───────────────────────────────
    "4941": ("Logistics", True, "Road freight transport — core target"),
    "4942": ("Logistics", True, "Removal services — fleet operators"),
    "5210": ("Logistics", True, "Warehousing and storage"),
    "5221": ("Logistics", True, "Land transport ancillary — forwarding, brokerage"),
    "5224": ("Logistics", True, "Cargo handling — loading/unloading"),
    "5229": ("Logistics", True, "Other transport ancillary — fleet mgmt, planning"),
    "5320": ("Logistics", True, "Courier and express services"),
    "7712": ("Logistics", True, "Truck rental and leasing"),
    # Conditional logistics
    "5222": ("Logistics", False, "Maritime ancillary — include only if also 4941"),
    # Excluded logistics
    "5110": ("Logistics", False, "EXCLUDED: Air passenger transport"),
    "5121": ("Logistics", False, "EXCLUDED: Air freight — large carriers only"),
    "4910": ("Logistics", False, "EXCLUDED: Rail passenger — public sector"),
    "4920": ("Logistics", False, "EXCLUDED: Rail freight — capital-intensive"),
    "5020": ("Logistics", False, "EXCLUDED: Maritime shipping — large operators"),
    "5223": ("Logistics", False, "EXCLUDED: Airport ground handling"),
    "4950": ("Logistics", False, "EXCLUDED: Pipeline transport"),
    # ─── CONSTRUCTION MATERIALS ──────────────────────────────
    # Wholesale / distribution
    "4673": ("Construction Materials", True, "Wholesale — building materials, timber, sanitary"),
    "4674": ("Construction Materials", True, "Wholesale — hardware, plumbing, HVAC"),
    # Cement, concrete, plaster
    "2351": ("Construction Materials", True, "Cement manufacturing"),
    "2352": ("Construction Materials", True, "Lime and plaster manufacturing"),
    "2361": ("Construction Materials", True, "Precast concrete elements"),
    "2362": ("Construction Materials", True, "Plaster construction elements"),
    "2369": ("Construction Materials", True, "Other concrete/cement products"),
    # Ceramics
    "2331": ("Construction Materials", True, "Ceramic tiles and flags"),
    "2332": ("Construction Materials", True, "Bricks and roof tiles"),
    # Glass
    "2311": ("Construction Materials", True, "Flat glass manufacturing"),
    "2312": ("Construction Materials", True, "Flat glass processing — windows, facades"),
    # Metal
    "2511": ("Construction Materials", True, "Steel structures and components"),
    "2512": ("Construction Materials", True, "Metal joinery — doors, windows, frames"),
    # Timber
    "1610": ("Construction Materials", True, "Timber sawmilling"),
    "1623": ("Construction Materials", True, "Timber structures and carpentry"),
    # Quarrying / aggregates
    "0811": ("Construction Materials", True, "Ornamental and building stone extraction"),
    "0812": ("Construction Materials", True, "Sand and gravel extraction"),
    "2370": ("Construction Materials", True, "Stone cutting and finishing"),
    # Conditional construction
    "4675": ("Construction Materials", False, "Chemical wholesale — only if construction-related"),
    "4690": ("Construction Materials", False, "General wholesale — only if secondary CNAE is 4673"),
    # Excluded construction-adjacent
    "4110": ("Construction Materials", False, "EXCLUDED: Real estate promotion"),
    "4121": ("Construction Materials", False, "EXCLUDED: Residential construction"),
    "4321": ("Construction Materials", False, "EXCLUDED: Electrical installation"),
    "4322": ("Construction Materials", False, "EXCLUDED: Plumbing/HVAC installation"),
    "7111": ("Construction Materials", False, "EXCLUDED: Architecture services"),
    "7112": ("Construction Materials", False, "EXCLUDED: Engineering services"),
    "6201": ("Construction Materials", False, "EXCLUDED: Software/SaaS"),
}
```

---

## 3. Data Quality Challenges in SABI Exports

### 3.1 Trade Name vs Legal Name

SABI provides two name fields: "Nombre" (legal name from the Registro Mercantil) and "Nombre comercial" (trading name).

**Rule:** Use `trade_name` for all outreach. Fall back to `legal_name` only if `trade_name` is null.

Rationale: The legal name often includes the legal form suffix (e.g., "TRANSPORTES GARCIA PEREZ SL") which reads like a tax filing, not a business relationship. The trade name is what appears on the company's trucks, website, and business cards. When you email a CEO and say "he revisado los datos de Transportes García," they recognise the name immediately.

**Implementation:** `company_name = trade_name.strip() if trade_name else legal_name.strip()`. Then strip trailing legal form suffixes (" SL", " SA", " SLU", " SAU", " SCCLP", " SCP") for display purposes, preserving the original legal name in a separate field for contract/invoice use.

### 3.2 Revenue Field Formats

SABI's revenue field ("Ingresos de explotación") has the following known quirks:

- **Units:** Always in thousands of EUR (EUR mil). A value of `12.500` means €12,500,000 (twelve and a half million), not €12.50. This is the most dangerous parsing error. The function must multiply by 1,000 to get the actual revenue in EUR.
- **Spanish locale formatting:** SABI's XLSX export *usually* stores numbers as Excel numeric types (which `openpyxl` reads correctly as floats). However, some fields may be exported as strings with Spanish formatting: `12.500,34` (period as thousands separator, comma as decimal). The parser must detect and handle both formats.
- **Null values:** Revenue is null for approximately 10–15% of companies, particularly recent filings or micro-companies that file abbreviated accounts ("cuentas abreviadas"). Null revenue does not necessarily mean the company is small — it may mean the filing hasn't been processed yet.
- **Negative values:** Legitimate in SABI. A company with negative "Ingresos de explotación" is rare but possible (accounting adjustments, reversals). Treat as a data quality flag.

**Implementation:**

```python
def parse_sabi_revenue(raw_value: Any) -> int | None:
    """Convert SABI revenue field (EUR thousands) to EUR.
    
    Returns None if the value is missing or unparseable.
    Returns the value in whole EUR (not thousands).
    """
    if raw_value is None or raw_value == "":
        return None
    if isinstance(raw_value, (int, float)):
        return int(raw_value * 1000)
    # String handling for Spanish locale
    s = str(raw_value).strip()
    s = s.replace(".", "")       # Remove thousands separator
    s = s.replace(",", ".")      # Decimal comma → decimal point
    try:
        return int(float(s) * 1000)
    except ValueError:
        return None
```

### 3.3 Missing Fields and Realistic Null Rates

Based on typical SABI exports for Catalan SMEs in the €5M–€20M range:

| Field | Expected Null Rate | Handling Strategy |
|-------|-------------------|-------------------|
| Nombre (legal name) | ~0% | Always present — required for Registro Mercantil filing |
| Nombre comercial (trade name) | ~30–40% | Fall back to legal name. Many SMEs don't register a separate trade name |
| NIF | ~0% | Always present |
| Dirección | ~2% | Not critical for outreach — skip |
| Teléfono | ~15–20% | Not critical for email outreach. Useful for follow-up calls |
| Página web | ~25–35% | Critical for Hunter.io domain search. If null, attempt to construct from trade name (e.g., `transportesgarcia.com`, `transportesgarcia.es`). Log for manual lookup |
| Código CNAE primario | ~1% | Almost always present. If missing, use activity description for keyword matching |
| Ingresos de explotación | ~10–15% | If null, the lead still proceeds but is flagged as `revenue_verified=False` and scored lower |
| EBITDA | ~20–25% | Many SMEs file abbreviated P&L without EBITDA line. Not a blocker |
| Resultado del ejercicio | ~10% | Similar to revenue — abbreviated filings may omit |
| Número empleados | ~15–20% | Self-reported. Many SMEs leave this blank. Cross-reference with Social Security data if available |

### 3.4 Company Status Flags

SABI's "Estado" field contains one of the following values:

| Estado | Action |
|--------|--------|
| Activa | ✅ Include |
| Activa — con incidencias | ⚠️ Include but flag — "incidencias" may indicate tax irregularities or judicial notices. Still a valid outreach target. |
| Disuelta | ❌ Exclude — company no longer exists |
| En liquidación | ❌ Exclude — company is winding down |
| Extinguida | ❌ Exclude — fully dissolved |
| Fusionada / Absorbida | ❌ Exclude — merged into another entity. The resulting entity may be a valid target under a different name |
| Inactiva | ❌ Exclude — dormant |
| Concurso de acreedores | ❌ Exclude — bankruptcy proceedings |

**Implementation:** Maintain an `ACTIVE_STATUSES` set and filter on it:

```python
ACTIVE_STATUSES = {"Activa", "Activa - con incidencias"}
```

### 3.5 Holding Company vs Operating Entity

SABI does not explicitly flag holding companies vs operating entities. However, several heuristics identify holdings:

1. **Legal name contains "INVERSIONES," "PARTICIPACIONES," "HOLDING," "GRUPO," or "GESTIÓN PATRIMONIAL."** These are almost always holding companies that consolidate ownership but don't operate fleets or warehouses.
2. **CNAE code 6420** ("Actividades de las sociedades holding") — filter these out entirely.
3. **Revenue present but employees = 0 or 1.** A "logistics company" with €15M revenue and 1 employee is a holding entity. The operating subsidiary is a separate record.
4. **Multiple entries with the same address.** If three companies at the same address all have the same founding family name but different CNAE codes, one is probably the holding and the others are operating entities.

**Rule:** Exclude any company where `cnae_primary == "6420"` or where `employees < 3 AND revenue > 5_000_000`. Flag companies with "HOLDING" or "INVERSIONES" in the name for manual review rather than automatic exclusion (some use these terms in operating entities).

### 3.6 Multi-Location Companies

SABI reports the "domicilio social" (registered office), which is often the legal address (lawyer's office, tax advisor's address) rather than the operational headquarters. For logistics companies, the actual depot or warehouse may be in a different province entirely.

**Impact:** A company registered in Barcelona may operate its fleet from a depot in Martorell or Valls. The geographic filter will correctly include it (registered in Catalonia), but the address in the SABI record may not correspond to the operational site.

**Handling:** Do not use the SABI address for geographic targeting. Use the province filter for the initial query (which uses the registered address), but do not make assumptions about the operational location in outreach emails. The prospect research phase (15 min per lead) should identify the actual operational locations from the company website.

---

## 4. Function Specification: `from_sabi_xlsx()`

### 4.1 Function Signature

```python
from pathlib import Path
from models import Lead, Vertical, Tier

def from_sabi_xlsx(
    path: Path,
    *,
    min_revenue_eur: int = 5_000_000,
    max_revenue_eur: int = 20_000_000,
    min_employees: int = 3,
    include_unverified_revenue: bool = False,
    cnae_map: dict[str, tuple[str, bool, str]] | None = None,
) -> list[Lead]:
    """Parse a SABI XLSX export into Lead objects.

    Reads a Bureau van Dijk SABI export file (XLSX format) and 
    produces a list of company-level Lead stubs. Each Lead contains 
    verified financial data (revenue, EBITDA, employees) and vertical 
    classification derived from CNAE codes, but does NOT contain 
    individual contact names or email addresses — these must be 
    enriched downstream via Hunter.io domain search and/or LinkedIn.

    Parameters
    ----------
    path : Path
        Path to the SABI XLSX export file. Must be a valid .xlsx 
        file exported from SABI with the column selection defined 
        in Section 1.5 of LEADGEN_ARCHITECTURE.md.
    min_revenue_eur : int, default 5_000_000
        Minimum revenue in EUR (not thousands). Companies below 
        this threshold are excluded. SABI stores revenue in EUR 
        thousands — the function converts internally.
    max_revenue_eur : int, default 20_000_000
        Maximum revenue in EUR. Companies above this threshold 
        are excluded.
    min_employees : int, default 3
        Minimum employee count. Filters out holding companies 
        and shell entities that report revenue but have 0–2 staff.
    include_unverified_revenue : bool, default False
        If True, includes companies where SABI revenue is null. 
        These leads will have revenue_est="" and 
        revenue_verified=False. Useful for expanding the pipeline 
        when the verified pool is too small.
    cnae_map : dict or None
        Custom CNAE-to-vertical mapping. If None, uses the default 
        CNAE_VERTICAL_MAP defined in this module. Keys are 4-digit 
        CNAE code strings, values are (vertical, include, reason) 
        tuples.

    Returns
    -------
    list[Lead]
        Company-level Lead objects with the following fields populated:
        - company_name (from trade_name, falling back to legal_name)
        - legal_name (always the Registro Mercantil name)
        - nif (tax ID — unique identifier)
        - revenue_est (formatted string, e.g. "€12.3M")
        - revenue_eur (int — exact revenue in EUR)
        - revenue_verified (True — SABI data is from official filings)
        - vertical (from CNAE mapping)
        - website (from SABI export)
        - employees (int)
        - ebitda_eur (int or None)
        - city, province (from SABI)
        - cnae_primary (4-digit code string)
        - source ("sabi")
        
        The following fields are left empty for downstream enrichment:
        - contact_name, email, linkedin_url, confidence_score

    Raises
    ------
    FileNotFoundError
        If `path` does not exist or is not readable.
    InvalidSABIFormatError
        If the file cannot be parsed as XLSX, or if fewer than 5 of 
        the expected SABI columns are found in the header row. This 
        indicates the file was not exported with the correct column 
        configuration.
    EmptyExportError
        If the file contains a valid header but zero data rows after 
        filtering. This is not an error per se but warrants a warning.

    Notes
    -----
    - Deduplication is performed on NIF (tax ID). If the same company 
      appears twice (e.g., due to overlapping SABI search strategies), 
      the first occurrence is kept.
    - Holdings (CNAE 6420) are excluded automatically.
    - Companies with status other than "Activa" or 
      "Activa - con incidencias" are excluded.
    """
```

### 4.2 Processing Algorithm (Pseudocode)

```
FUNCTION from_sabi_xlsx(path, ...):

    1. VALIDATE INPUT
       - Assert path exists and has .xlsx extension
       - Open workbook with openpyxl (read_only=True, data_only=True)
       - Read header row (row 1)
       - Map column letters to SABI field names using fuzzy matching
         (SABI sometimes exports headers as "Ingresos explotación mil EUR"
         or "Ingresos de explotación (EUR mil)" depending on version)
       - If fewer than 5 expected columns found → raise InvalidSABIFormatError

    2. LOAD CNAE MAP
       - If cnae_map is None, use default CNAE_VERTICAL_MAP
       - Build a set of included CNAE codes: {code for code, (_, inc, _) 
         in map if inc is True}

    3. ITERATE ROWS
       - For each row after the header:
           a. EXTRACT RAW VALUES by column mapping
           b. PARSE REVENUE: call parse_sabi_revenue(raw_revenue)
              - If None and not include_unverified_revenue → skip row
              - If < min_revenue_eur or > max_revenue_eur → skip row
           c. PARSE EMPLOYEES: int(raw_employees) if not None
              - If < min_employees → skip row
           d. CHECK STATUS: if status not in ACTIVE_STATUSES → skip row
           e. CHECK CNAE: if cnae_primary not in included_codes → skip row
              - Also check cnae_secondary as fallback
           f. CHECK HOLDING HEURISTICS:
              - If cnae_primary == "6420" → skip
              - If employees < 3 and revenue > 5M → skip
              - If legal_name contains HOLDING_KEYWORDS → flag, don't skip
           g. RESOLVE COMPANY NAME:
              - company_name = trade_name if trade_name else legal_name
              - Strip trailing legal form suffixes
           h. RESOLVE VERTICAL:
              - vertical = cnae_map[cnae_primary].vertical
              - If cnae_primary not in map, try cnae_secondary
              - If neither matches → classify as "Unknown" and flag
           i. RESOLVE WEBSITE:
              - Strip protocol and trailing slashes
              - Validate it looks like a domain (contains ".")
              - If null → attempt domain_from_name(company_name)
           j. FORMAT REVENUE ESTIMATE:
              - If revenue_eur: format as "€{revenue/1e6:.1f}M"
              - Else: revenue_est = ""
           k. CREATE LEAD OBJECT and append to results list

    4. DEDUPLICATE
       - By NIF (tax ID) — keep first occurrence
       - Log count of duplicates removed

    5. SORT
       - By revenue_eur descending (highest-revenue companies first)
       - This ensures the first leads in the list are the best ICP fit

    6. RETURN leads list

    7. LOG SUMMARY
       - Total rows in file
       - Rows excluded by: revenue filter, employee filter, status, 
         CNAE mismatch, holding heuristic, deduplication
       - Final lead count
       - Vertical distribution
```

### 4.3 Edge Cases

| Edge Case | Handling |
|-----------|----------|
| SABI header row uses different column names than expected | Fuzzy-match column headers using a synonym dict. E.g., "Cifra de negocios" → revenue field. Log which mapping was applied. |
| Revenue is zero (not null) | Include — a company with €0 revenue in the most recent year may have just filed an abbreviated statement. Flag as `revenue_verified=False`. |
| CNAE primary doesn't match but secondary does | Use secondary CNAE for vertical classification. Log that the primary CNAE was out of scope. |
| Company has both logistics and construction CNAE codes | Classify by primary CNAE. Add a `dual_vertical=True` flag. These companies may be good targets for cross-sell. |
| Website field contains full URL with path | Strip to domain only. E.g., `https://www.transportesgarcia.com/contacto` → `transportesgarcia.com` |
| Website field contains multiple URLs separated by semicolons | Take the first URL only. |
| Trade name is identical to legal name minus suffix | Use trade name as-is (no special handling needed). |
| Excel file has merged cells in header | `openpyxl` reads merged cells — only the top-left cell of a merge has a value. Handle by skipping None header cells. |
| File has multiple worksheets | SABI exports to a single worksheet. Read only the first sheet. Log a warning if multiple sheets exist. |

---

## 5. Hybrid Pipeline Design

### 5.1 Workflow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│  PHASE 1 — SABI EXPORT (Manual, ~20 min)                     │
│                                                              │
│  SABI Web Interface                                          │
│  ├── Apply filters: Catalonia, CNAE codes, €5M–€20M         │
│  ├── Select 20 columns (Section 1.5)                         │
│  ├── Export as XLSX                                          │
│  └── Save as: sabi_export_YYYYMMDD.xlsx                      │
│                                                              │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  PHASE 2 — SABI ADAPTER (Automated, ~5 sec)                  │
│                                                              │
│  yellowbird-leads from-sabi sabi_export_20260305.xlsx        │
│  ├── Parse XLSX → validate columns                           │
│  ├── Filter by revenue, employees, status, CNAE              │
│  ├── Classify vertical via CNAE mapping                      │
│  ├── Deduplicate by NIF                                      │
│  └── Output: sabi_leads_stub.csv                             │
│      (company-level: name, revenue, vertical, website, NIF)  │
│      (NO contact names, NO emails)                           │
│                                                              │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  PHASE 3 — HUNTER.IO DOMAIN SEARCH (Automated, ~2 min)      │
│                                                              │
│  yellowbird-leads enrich sabi_leads_stub.csv                 │
│  ├── For each lead with a website domain:                    │
│  │   ├── GET /v2/domain-search?domain={domain}               │
│  │   ├── Filter results by seniority: "executive","director" │
│  │   ├── Filter by department: "executive", "management"     │
│  │   ├── Select highest-confidence email                     │
│  │   └── Populate: contact_name, email, confidence_score     │
│  ├── For leads WITHOUT a website:                            │
│  │   └── Flag as "manual_enrichment_needed"                  │
│  ├── Rate limit: 2s between calls                            │
│  └── Output: sabi_leads_enriched.csv                         │
│      (now has contacts for ~60-70% of companies)             │
│                                                              │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  PHASE 4 — LINKEDIN MANUAL ENRICHMENT (Manual, ~10 min/lead)│
│                                                              │
│  For each lead where Hunter returned no contact:             │
│  ├── Search LinkedIn: "{company_name} Director General"      │
│  ├── OR: visit company LinkedIn page → People tab            │
│  ├── Record: contact name, title, LinkedIn URL               │
│  ├── Attempt Hunter email-finder with name + domain          │
│  └── Update sabi_leads_enriched.csv                          │
│                                                              │
│  For ALL leads (even Hunter-enriched):                       │
│  ├── Verify the contact is C-suite (CEO, DG, Gerente, Owner) │
│  ├── Record LinkedIn URL                                     │
│  └── Note any recent posts/activity for personalization      │
│                                                              │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  PHASE 5 — SCORING & TIERING (Automated, ~1 sec)            │
│                                                              │
│  yellowbird-leads score sabi_leads_enriched.csv              │
│  ├── ICP Score (0–100) computed from:                        │
│  │   ├── Revenue fit (0–30): distance from €10M sweet spot   │
│  │   ├── Email confidence (0–25): Hunter score               │
│  │   ├── Data completeness (0–20): fields populated          │
│  │   ├── Vertical match (0–15): primary CNAE vs secondary    │
│  │   └── Financial health (0–10): positive EBITDA = bonus    │
│  ├── SABI Revenue Bonus: +10 points for revenue_verified=True│
│  │   (SABI revenue is from official filings, not estimated)  │
│  ├── Tier assignment: T1 ≥ 80, T2 ≥ 60, T3 ≥ 40, T4 < 40  │
│  └── Output: yellowbird_leads_final.csv (14-column CRM)      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 Function Call Chain

```python
# Full hybrid pipeline — invoked by CLI or script
from pathlib import Path
from leadgen.io import from_sabi_xlsx, write_leads_csv
from leadgen.enrich import hunter_domain_search, hunter_email_finder
from leadgen.scoring import compute_icp_score, assign_tier
from leadgen.models import Lead

def run_sabi_pipeline(
    sabi_path: Path,
    output_path: Path,
    hunter_api_key: str,
    dry_run: bool = False,
) -> list[Lead]:
    """Execute the full SABI → enriched leads pipeline."""
    
    # Phase 2: Parse SABI export
    leads = from_sabi_xlsx(sabi_path)
    
    # Phase 3: Hunter domain search for contacts
    if not dry_run:
        for lead in leads:
            if lead.website:
                domain = extract_domain(lead.website)
                contact = hunter_domain_search(
                    domain=domain,
                    api_key=hunter_api_key,
                    seniority=["executive", "director"],
                    department=["executive", "management"],
                )
                if contact:
                    lead.contact_name = contact.name
                    lead.email = contact.email
                    lead.confidence_score = contact.confidence
                else:
                    lead.next_action = "LinkedIn manual enrichment"
            else:
                lead.next_action = "Find website → then enrich"
    
    # Phase 5: Score and tier
    for lead in leads:
        lead.icp_score = compute_icp_score(lead)
        lead.tier = assign_tier(lead.icp_score)
    
    # Sort by score descending
    leads.sort(key=lambda l: l.icp_score, reverse=True)
    
    # Write output
    write_leads_csv(leads, output_path)
    
    return leads
```

### 5.3 Hunter.io Domain Search vs Email Verifier

The current pipeline uses **email-verifier** (checks if a known email is valid). The SABI pipeline requires **domain-search** (finds contacts at a given domain). These are different endpoints with different credit costs:

| Endpoint | Purpose | Free Tier | When to Use |
|----------|---------|-----------|-------------|
| `GET /v2/email-verifier` | Verify a known email address | 25/month | Apollo pipeline (email already known) |
| `GET /v2/domain-search` | Find all emails at a domain | 25 searches/month | SABI pipeline (only domain known) |
| `GET /v2/email-finder` | Find a specific person's email | 25 finds/month | LinkedIn enrichment (name + domain known) |

**Budget strategy for free tier:** With 25 of each per month, a single SABI batch of 25 companies uses all domain-search credits. Prioritize the highest-revenue companies first. For the remaining leads, use the LinkedIn manual enrichment path to find the name, then use email-finder credits for the top candidates.

### 5.4 Why SABI Leads are Higher Quality

The ICP scoring formula should award a bonus to SABI-sourced leads because:

1. **Revenue is verified.** Apollo estimates revenue from employee count and industry averages. SABI revenue comes from official Registro Mercantil filings — the same data the tax authority uses. A company showing €12M in SABI genuinely has €12M in revenue.
2. **EBITDA enables margin pressure targeting.** A company with €15M revenue and negative EBITDA is under extreme margin pressure — exactly the "bleeding neck" that the Challenger Sale methodology exploits. Apollo has no profitability data.
3. **CNAE codes enable precise vertical targeting.** Apollo's industry tags are self-reported and often wrong (cf. Flowbox and Hutchison Ports from the Day 1 batch). CNAE codes are assigned by the tax authority based on the actual primary business activity.
4. **Historical comparison is possible.** With `revenue_last` and `revenue_prev`, the scoring function can identify companies whose revenue is declining — a signal that they may be receptive to a margin recovery message.

---

# DELIVERABLE 2 — PROFESSIONAL CLI SPECIFICATION

---

## 6. Command Architecture

### 6.1 Top-Level Structure

```
yellowbird-leads [OPTIONS] COMMAND [ARGS]

Global Options:
  --config PATH      Path to .yellowbird.toml (default: ./.yellowbird.toml)
  --verbose / -v     Enable debug logging
  --quiet / -q       Suppress non-essential output
  --version          Show version and exit
  --help             Show help and exit

Commands:
  from-apollo    Parse an Apollo.io CSV export into CRM leads
  from-sabi      Parse a SABI XLSX export into CRM leads
  enrich         Add Hunter.io email verification/discovery to a leads CSV
  score          Re-score and re-tier an existing leads CSV
  research       Generate per-lead prospect research notes (LLM-powered)
  report         Print a rich terminal summary of a leads CSV
  validate       Check a leads CSV for data quality issues
```

### 6.2 Command Specifications

---

#### `from-apollo`

**Purpose:** Replace the current `process_leads.py` with a robust, logged, resumable importer.

```
yellowbird-leads from-apollo [OPTIONS] INPUT_CSV

Arguments:
  INPUT_CSV          Path to raw Apollo.io CSV export [required]

Options:
  --output PATH      Output CSV path [default: ./yellowbird_leads.csv]
  --skip-verify      Skip Hunter.io email verification
  --verify-limit N   Max Hunter verifications (overrides config) [default: 25]
  --min-score N      Minimum Hunter confidence score to include [default: 0]
  --dry-run          Parse and display results without writing files or calling APIs
  --help             Show help and exit
```

**Input:** Raw Apollo CSV export file (the messy format documented in GTM Day 1 Runbook Section 5.3).

**Output:** 14-column CRM CSV matching the Cold Email Playbook schema. Additionally creates a `_rejected.csv` with rows that were filtered out and the reason.

**Console output while running:**

```
 Yellowbird Leads — Apollo Import
 ─────────────────────────────────
 Input:  apollo_raw_20260305.csv (47 rows)
 Output: yellowbird_leads.csv

 Parsing Apollo export...
  ✓ 47 rows read
  ✗ 3 rows rejected (no email found)
  ✗ 2 rows rejected (gmail.com — personal email)
  ✓ 42 leads extracted

 Verifying emails via Hunter.io...
  [████████████████████████████████████████] 25/25
  ✓ 22 verified (score ≥ 50)
  ⚠ 3 low confidence (score < 50)

 ┌─ Summary ──────────────────────────────────┐
 │ Total leads written:  25                    │
 │ Logistics:            11 (44%)              │
 │ Construction:         14 (56%)              │
 │ Avg confidence:       78.3                  │
 │ Hunter credits used:  25 / 25 remaining: 0  │
 │ Rejected leads:       17 → apollo_rejected.csv │
 │ Elapsed:              52.3s                 │
 │ Output:               ./yellowbird_leads.csv │
 └─────────────────────────────────────────────┘
```

**Exit codes:** 0 = success, 1 = input file not found, 2 = invalid CSV format, 3 = Hunter API error (partial output written).

**Example invocations:**

```bash
# Standard run
yellowbird-leads from-apollo ~/Downloads/apollo_raw.csv

# Dry run — see what would happen without API calls
yellowbird-leads from-apollo ~/Downloads/apollo_raw.csv --dry-run

# Skip verification (just clean and format)
yellowbird-leads from-apollo apollo_raw.csv --skip-verify --output cleaned.csv

# Custom output location
yellowbird-leads from-apollo apollo_raw.csv -o leads/batch_003.csv
```

---

#### `from-sabi`

**Purpose:** Parse SABI XLSX export into company-level lead stubs.

```
yellowbird-leads from-sabi [OPTIONS] INPUT_XLSX

Arguments:
  INPUT_XLSX         Path to SABI XLSX export [required]

Options:
  --output PATH      Output CSV path [default: ./sabi_leads.csv]
  --min-revenue EUR  Minimum revenue in EUR [default: 5000000]
  --max-revenue EUR  Maximum revenue in EUR [default: 20000000]
  --min-employees N  Minimum employee count [default: 3]
  --include-null-revenue  Include companies with no revenue data
  --enrich           Auto-run Hunter domain search after parsing
  --dry-run          Parse and display results without writing
  --help             Show help and exit
```

**Console output while running:**

```
 Yellowbird Leads — SABI Import
 ──────────────────────────────
 Input:  sabi_export_20260305.xlsx (312 rows)
 Output: sabi_leads.csv

 Parsing SABI export...
  ✓ 312 rows read
  ✗ 48 excluded (revenue outside €5M–€20M)
  ✗ 12 excluded (inactive / dissolved)
  ✗ 7 excluded (holding company heuristic)
  ✗ 89 excluded (CNAE code not in target verticals)
  ✗ 3 duplicates removed (same NIF)
  ✓ 153 leads extracted

 ┌─ Vertical Distribution ────────────────────┐
 │ Logistics:             67 (44%)             │
 │ Construction Materials: 86 (56%)            │
 └─────────────────────────────────────────────┘

 ┌─ Revenue Distribution ─────────────────────┐
 │ €5M–€8M:              41 (27%)              │
 │ €8M–€12M:             52 (34%)              │
 │ €12M–€16M:            38 (25%)              │
 │ €16M–€20M:            22 (14%)              │
 └─────────────────────────────────────────────┘

 ┌─ Data Quality ─────────────────────────────┐
 │ Website available:     112 / 153 (73%)      │
 │ EBITDA available:      119 / 153 (78%)      │
 │ Phone available:       131 / 153 (86%)      │
 │ Trade name available:  98 / 153 (64%)       │
 └─────────────────────────────────────────────┘

 ⚠ 41 leads have no website — manual enrichment required
 ✓ Wrote 153 leads to ./sabi_leads.csv
 Elapsed: 1.2s
```

---

#### `enrich`

**Purpose:** Add contact-level data (name, email, confidence score) to an existing leads CSV via Hunter.io.

```
yellowbird-leads enrich [OPTIONS] INPUT_CSV

Arguments:
  INPUT_CSV          Path to leads CSV (from any source) [required]

Options:
  --output PATH      Output CSV path [default: {input}_enriched.csv]
  --mode verifier|finder|domain  Hunter endpoint to use [default: verifier]
  --limit N          Max API calls [default: 25]
  --min-score N      Skip leads already above this score [default: 0]
  --resume           Resume from last checkpoint
  --dry-run          Show what would be enriched without API calls
  --help             Show help and exit
```

**Modes:**
- `verifier` — Verify existing email addresses (Apollo pipeline)
- `domain` — Search for contacts by company domain (SABI pipeline)
- `finder` — Find email by name + domain (LinkedIn enrichment)

**Console output while running:**

```
 Yellowbird Leads — Enrichment
 ─────────────────────────────
 Input:    sabi_leads.csv (153 leads)
 Mode:     domain (Hunter domain-search)
 Budget:   25 API calls

 Enriching...
  [████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 12/25
  ├── Lead 12: Transportes Marín SL
  │   └── Found: Juan Marín (CEO) → j.marin@transportesmarin.com [91]
  ...

  ✓ 18 contacts found
  ⚠ 4 domains returned no executive contacts
  ✗ 3 domains not found in Hunter

 ✓ Checkpoint saved → .yellowbird_enrich_checkpoint.json
 ✓ Wrote 153 leads to sabi_leads_enriched.csv
```

---

#### `score`

**Purpose:** Recalculate ICP scores and tier assignments on an existing leads CSV.

```
yellowbird-leads score [OPTIONS] INPUT_CSV

Arguments:
  INPUT_CSV          Path to leads CSV [required]

Options:
  --output PATH      Output CSV path [default: overwrites input]
  --weights PATH     Custom scoring weights JSON
  --help             Show help and exit
```

---

#### `research`

**Purpose:** Generate AI-powered prospect research notes per lead. Uses the Anthropic API (Claude) to produce a personalized research brief for each prospect, including talking points for the cold email.

```
yellowbird-leads research [OPTIONS] INPUT_CSV

Arguments:
  INPUT_CSV          Path to leads CSV [required]

Options:
  --output PATH      Output CSV path [default: {input}_researched.csv]
  --limit N          Max leads to research [default: 10]
  --model TEXT       Claude model to use [default: claude-sonnet-4-5-20250929]
  --dry-run          Show prompts without calling API
  --help             Show help and exit
```

**Output:** Adds a `research_notes` column to the CSV with a structured brief per lead containing: company summary (2 sentences), likely data pain points based on vertical, personalization hooks for Email #1, and suggested subject line variant.

---

#### `report`

**Purpose:** Display a rich terminal report summarizing a leads CSV.

```
yellowbird-leads report [OPTIONS] INPUT_CSV

Arguments:
  INPUT_CSV          Path to leads CSV [required]

Options:
  --sort FIELD       Sort by: score|company|vertical|confidence [default: score]
  --tier N           Show only leads in this tier (1–4)
  --vertical TEXT    Filter by vertical name
  --top N            Show only top N leads [default: all]
  --export PATH      Export report as HTML file
  --help             Show help and exit
```

**Example terminal output:**

```
 ╔══════════════════════════════════════════════════════════════════════════════╗
 ║  YELLOWBIRD LEADS — Pipeline Report                                        ║
 ║  Source: yellowbird_leads_final.csv  |  Generated: 2026-03-05 09:30        ║
 ╚══════════════════════════════════════════════════════════════════════════════╝

 ┌─ Tier Distribution ──────────────────────┐
 │ ██████████████████████  Tier 1:  12 (24%) │ ← green
 │ ████████████████       Tier 2:  18 (36%) │ ← yellow
 │ ██████████             Tier 3:  14 (28%) │ ← orange
 │ ██████                 Tier 4:   6 (12%) │ ← red
 └──────────────────────────────────────────┘

 ┌──────────────────────────────────────────────────────────────────────────────┐
 │ #  │ Company              │ Contact          │ Email              │ Score │ T │
 ├──────────────────────────────────────────────────────────────────────────────┤
 │  1 │ Transportes Marín    │ Juan Marín       │ j.marin@tmar...    │   94  │ 1 │ ← green
 │  2 │ Ciments Molins       │ Pere Molins      │ p.molins@cim...    │   91  │ 1 │ ← green
 │  3 │ Grup Vilar           │ Marta Vilar      │ m.vilar@grup...    │   88  │ 1 │ ← green
 │ ...│                      │                  │                    │       │   │
 │ 48 │ Ferrallados BCN      │ —                │ —                  │   32  │ 4 │ ← red
 │ 49 │ Vidriería Costa      │ —                │ —                  │   28  │ 4 │ ← red
 │ 50 │ Hormigones del Ter   │ —                │ —                  │   21  │ 4 │ ← red
 └──────────────────────────────────────────────────────────────────────────────┘

 ┌─ Summary ──────────────────────────────────────────────────┐
 │ Total leads:        50                                      │
 │ With email:         38 (76%)                                │
 │ Avg ICP score:      64.2                                    │
 │ Logistics:          22 (44%)  │  Construction:  28 (56%)    │
 │ Revenue verified:   50 (100%) ← SABI source                │
 │ Ready for Email #1: 30 (Tier 1 + Tier 2 with email)        │
 └─────────────────────────────────────────────────────────────┘
```

---

#### `validate`

**Purpose:** Check a leads CSV for data quality issues before sending any outreach.

```
yellowbird-leads validate [OPTIONS] INPUT_CSV

Arguments:
  INPUT_CSV          Path to leads CSV [required]

Options:
  --fix              Attempt automatic fixes and write corrected file
  --help             Show help and exit
```

**Example terminal output:**

```
 Yellowbird Leads — Data Quality Validation
 ───────────────────────────────────────────
 Input: yellowbird_leads.csv (20 leads)

 ⚠ WARNINGS (5):
  Row  4: Company "Directora" looks like a job title, not a company name
  Row  7: Flowbox — CNAE/keyword suggests tech platform, not construction
  Row  9: Hutchison Ports — port terminal operator, not road freight
  Row 16: Welivery domain .com.ar — possible non-Spain contact
  Row 19: Company name has leading artifact: "'-Pentrilo | Painting tools"

 ✗ ERRORS (2):
  Row 20: dasso Group — Hunter confidence score is 0 (undeliverable)
  Row  3: Email field is empty

 ✓ PASSED (13 leads clean)

 Quality score: 65% (13/20 clean)
 Recommendation: Fix 5 warnings + 2 errors before sending Email #1.
```

---

## 7. Rich Terminal Output Design

### 7.1 Library: Rich

All terminal output uses the `rich` library (already available via `pip install rich`). Specific components:

| Component | Where Used |
|-----------|-----------|
| `rich.progress.Progress` | `enrich` command — API call progress bar |
| `rich.table.Table` | `report` command — leads table |
| `rich.panel.Panel` | Summary panels in all commands |
| `rich.console.Console` | All formatted output |
| `rich.text.Text` | Tier colour coding |
| `rich.live.Live` | Live-updating progress during enrichment |

### 7.2 Colour Coding

```python
TIER_COLORS = {
    1: "green",
    2: "yellow",
    3: "dark_orange",
    4: "red",
}

TIER_LABELS = {
    1: "[bold green]T1[/]",
    2: "[bold yellow]T2[/]",
    3: "[bold dark_orange]T3[/]",
    4: "[bold red]T4[/]",
}
```

### 7.3 Progress Bar (Enrich Command)

```python
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

with Progress(
    SpinnerColumn(),
    TextColumn("[bold blue]{task.description}"),
    BarColumn(),
    TextColumn("{task.completed}/{task.total}"),
    console=console,
) as progress:
    task = progress.add_task("Enriching leads...", total=len(leads))
    for lead in leads:
        # ... API call ...
        progress.update(task, advance=1, description=f"Verifying {lead.email}")
```

---

## 8. Configuration File Design

### 8.1 Full `.yellowbird.toml` Schema

```toml
# ══════════════════════════════════════════════════════════
# Yellowbird Telemetry — Lead Generation Configuration
# ══════════════════════════════════════════════════════════
# Place this file at the project root as .yellowbird.toml
# or pass --config PATH to override.
#
# API keys can also be set via environment variables:
#   HUNTER_API_KEY, APOLLO_API_KEY, ANTHROPIC_API_KEY
# Environment variables take precedence over this file.

[api_keys]
# Hunter.io API key — used for email verification and domain search.
# Free tier: 25 verifications + 25 searches + 25 finds per month.
# Get yours at: https://hunter.io/api-keys
hunter = ""

# Apollo.io API key — currently unused (API is paywalled).
# Reserved for future use if Apollo re-opens free-tier API access.
apollo = ""

# Anthropic API key — used by the `research` command for
# LLM-powered prospect research notes.
anthropic = ""

[output]
# Default output directory for generated CSV files.
# Relative paths are resolved from the current working directory.
directory = "./leads"

# File naming template. Available variables:
#   {source}  — "apollo" or "sabi"
#   {date}    — YYYY-MM-DD
#   {batch}   — auto-incrementing batch number
filename_template = "yellowbird_{source}_{date}.csv"

[scoring]
# ICP scoring weights — must sum to 100.
# Tune these based on which factors best predict conversion.
revenue_fit_weight = 30        # How close to the €10M sweet spot
email_confidence_weight = 25   # Hunter.io verification score
data_completeness_weight = 20  # How many fields are populated
vertical_match_weight = 15     # Primary vs secondary CNAE match
financial_health_weight = 10   # Positive EBITDA bonus

# Revenue sweet spot — the ideal company size.
# Companies at this revenue get maximum revenue_fit score.
# Score decreases linearly toward min/max bounds.
revenue_sweet_spot_eur = 10_000_000

# SABI verification bonus — added to the ICP score when
# the lead source is SABI (revenue is from official filings,
# not estimated). Set to 0 to disable.
sabi_verified_bonus = 10

# Tier thresholds — ICP score cutoffs for each tier.
tier_1_min = 80
tier_2_min = 60
tier_3_min = 40
# Below tier_3_min = Tier 4

[rate_limits]
# Delay in seconds between Hunter.io API calls.
# Free tier recommendation: 2.0s minimum.
hunter_delay_seconds = 2.0

# Delay in seconds between Apollo API calls (if API is available).
apollo_delay_seconds = 1.5

# Maximum Hunter verifications per run.
# Set this to stay within your monthly budget.
hunter_max_per_run = 25

# Maximum Anthropic API calls per run (research command).
anthropic_max_per_run = 10

[logging]
# Logging level: DEBUG, INFO, WARNING, ERROR
level = "INFO"

# Log file path. Set to "" to disable file logging.
log_file = "./leads/yellowbird.log"

[sabi]
# Default SABI export filters (used by from-sabi command).
min_revenue_eur = 5_000_000
max_revenue_eur = 20_000_000
min_employees = 3
include_null_revenue = false
```

### 8.2 Config Loading Priority

1. CLI flags (highest priority)
2. Environment variables (`HUNTER_API_KEY`, etc.)
3. `.yellowbird.toml` in current directory
4. `~/.yellowbird.toml` in home directory
5. Built-in defaults (lowest priority)

Implementation: use `tomllib` (Python 3.11+ stdlib) to parse, merge with `os.environ`, then override with Typer callback parameters.

---

## 9. Error Handling Philosophy

### 9.1 Error Classification

| Category | Behaviour | Example |
|----------|-----------|---------|
| **Fatal — crash with clear message** | Print a single sentence explaining what went wrong and how to fix it. Exit code 1. | Input file not found, invalid file format, no API key when API is required |
| **Recoverable — warn and continue** | Print a yellow warning, skip the affected item, and continue processing. Include the affected item in a `_rejected.csv` sidecar file. | Single Hunter verification fails (network timeout), one row has malformed data, a CNAE code not found in the mapping |
| **Advisory — note at the end** | Collect all advisory notices and display them in the summary panel after the run completes. | Low average confidence score, high null rate in a SABI export, many leads without websites |

### 9.2 Partial Failure Handling

**Scenario:** 10 of 20 Hunter verifications fail mid-run (network drops, API outage).

**Behaviour:**

1. Each failed verification is logged as a warning with the specific error.
2. The lead's `confidence_score` is set to `0` and `next_action` is set to `"Re-verify email"`.
3. Processing continues to the next lead.
4. The output CSV is written with all 20 leads — 10 verified, 10 unverified.
5. A checkpoint file (`.yellowbird_enrich_checkpoint.json`) is written after each successful verification, recording which lead indices have been processed.
6. The summary panel shows: `"⚠ 10 of 20 verifications failed — run with --resume to retry"`.

### 9.3 `--dry-run` Flag

Every command that writes files or calls external APIs accepts `--dry-run`. Behaviour:

- **File reads:** Performed normally (parsing, validation).
- **API calls:** Skipped. Where an API result would be used, a placeholder is inserted (e.g., `confidence_score = -1` meaning "not checked").
- **File writes:** Skipped. The output that *would* have been written is displayed in the terminal.
- **Console output:** Identical to a real run but prefixed with `[DRY RUN]` and all API-dependent values shown as `?`.

### 9.4 Resumability

The `enrich` command (the only long-running, API-dependent command) implements checkpointing:

**Checkpoint file:** `.yellowbird_enrich_checkpoint.json`

```json
{
  "input_file": "sabi_leads.csv",
  "input_hash": "sha256:abc123...",
  "mode": "domain",
  "completed_indices": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
  "results": {
    "0": {"email": "j.marin@tm.com", "score": 91, "contact": "Juan Marín"},
    "1": {"email": "p.molins@cm.com", "score": 88, "contact": "Pere Molins"},
    ...
  },
  "timestamp": "2026-03-05T09:30:00"
}
```

**Resume logic:**

1. `yellowbird-leads enrich leads.csv --resume`
2. Check for `.yellowbird_enrich_checkpoint.json`.
3. Verify `input_hash` matches the current file (if file changed, warn and ask to confirm).
4. Load `completed_indices` — skip these leads.
5. Continue from the first non-completed index.
6. Merge checkpoint results with new results.
7. Write the complete output file.

---

## 10. Implementation Roadmap

### 10.1 Milestone 1 — Minimum Viable CLI (This Week)

**Goal:** Replace `process_leads.py` and the manual workflow with a proper CLI that a founder can run confidently every Tuesday.

**Commands to implement:**
- `from-apollo` — full implementation including Hunter verification
- `report` — basic table view of any leads CSV
- `validate` — data quality checks

**Estimated implementation time:** 12–16 hours

| Task | Hours | Notes |
|------|-------|-------|
| Project scaffolding (Typer app, config loader, models) | 2 | Reuse `Lead` dataclass from `lead_generator.py` |
| `from-apollo` command (parsing + cleaning) | 3 | Port logic from `process_leads.py` but with `csv.reader`, proper error handling, and logging |
| Hunter.io `verify_email` integration | 2 | Port from `lead_generator.py` `HunterClient` |
| `report` command (Rich table) | 2 | Read any 14-column CSV and display formatted table |
| `validate` command | 2 | Rule-based checks: empty fields, score thresholds, name heuristics |
| `.yellowbird.toml` config loading | 1.5 | `tomllib` parser + env var merge |
| Testing (pytest) | 2 | Test CSV parsing with known Apollo export quirks, test scoring, test config loading |

**Definition of done:**
- `yellowbird-leads from-apollo apollo_raw.csv` produces identical output to current `process_leads.py` (regression test against existing `yellowbird_leads.csv`)
- `yellowbird-leads report yellowbird_leads.csv` displays a formatted table with tier colours
- `yellowbird-leads validate yellowbird_leads.csv` catches the 4 known issues from Day 1 (Directora, Flowbox, Hutchison, Pentrilo)
- All commands run with `--dry-run` without side effects
- `pytest tests/` passes with 15+ tests covering parsing edge cases

### 10.2 Milestone 2 — Enrichment & Scoring (Next 2 Weeks)

**Goal:** Make the weekly lead batching workflow efficient. Score leads automatically. Enable SABI as a data source.

**Commands to implement:**
- `enrich` — Hunter.io integration with all three modes (verifier, domain, finder)
- `score` — ICP scoring engine with configurable weights
- `from-sabi` — SABI XLSX parser (full implementation of Section 4)

**Estimated implementation time:** 20–25 hours

| Task | Hours | Notes |
|------|-------|-------|
| `enrich` command — verifier mode | 3 | Extend existing Hunter integration |
| `enrich` command — domain search mode | 3 | New Hunter endpoint integration |
| `enrich` command — email finder mode | 2 | New Hunter endpoint |
| Checkpoint/resume system | 3 | JSON checkpoint file, hash verification |
| `score` command | 3 | ICP scoring algorithm, tier assignment, config-driven weights |
| `from-sabi` command | 5 | XLSX parsing with openpyxl, CNAE mapping, revenue parsing, all edge cases |
| Progress bars and Rich output for all commands | 2 | Consistent UX across all commands |
| Testing | 4 | SABI parsing tests (mock XLSX), scoring tests, enrichment tests (mocked API) |

**Definition of done:**
- `yellowbird-leads from-sabi export.xlsx` correctly parses a real SABI export with 100+ rows
- `yellowbird-leads enrich sabi_leads.csv --mode domain` finds contacts for ≥60% of leads with websites
- `yellowbird-leads enrich leads.csv --resume` correctly resumes from a checkpoint
- `yellowbird-leads score leads.csv` produces tiered output with Tier 1–4 distribution visible in `report`
- `--dry-run` works for all commands
- `pytest tests/` passes with 35+ tests

### 10.3 Milestone 3 — Intelligence Layer (Post-Revenue)

**Goal:** Add LLM-powered research and reporting capabilities that make the outreach preparation phase faster and more effective.

**Commands to implement:**
- `research` — AI-powered prospect research notes

**Estimated implementation time:** 10–15 hours

| Task | Hours | Notes |
|------|-------|-------|
| Anthropic API integration | 2 | Claude API client with retry logic |
| Research prompt engineering | 3 | Design prompts that produce usable 3-sentence briefs per prospect |
| `research` command implementation | 3 | Batch API calls, CSV column addition, rate limiting |
| HTML report export from `report --export` | 2 | Branded HTML output matching Yellowbird's navy/gold palette |
| Testing and prompt iteration | 3 | Test with real lead data, iterate on prompt quality |

**Definition of done:**
- `yellowbird-leads research leads.csv --limit 5` produces research notes for 5 leads that include: company summary, pain point hypothesis, and personalization hook
- Research notes are usable directly in the Cold Email Playbook personalization step (replacing the current 15 min manual research per prospect)
- `yellowbird-leads report leads.csv --export report.html` generates a shareable HTML file
- `pytest tests/` passes with 45+ tests

---

## Appendix A — Existing Code Migration Map

The following table maps existing code to its destination in the refactored package:

| Current File | Current Function | New Location | Notes |
|-------------|-----------------|--------------|-------|
| `process_leads.py` | `process_csv()` | `leadgen/io.py` → `from_apollo_csv()` | Replace raw `split(",")` with `csv.reader`. Keep email scanner logic. |
| `process_leads.py` | `clean_value()` | `leadgen/normalize.py` → `clean_apollo_value()` | Preserve markdown link stripping |
| `process_leads.py` | `verify_hunter()` | `leadgen/verify.py` → `HunterClient.verify_email()` | Already exists in `lead_generator.py` — use that version |
| `lead_generator.py` | `Lead` dataclass | `leadgen/models.py` → `Lead` | Extend with: `nif`, `revenue_eur`, `revenue_verified`, `source`, `icp_score`, `tier` |
| `lead_generator.py` | `HunterClient` | `leadgen/verify.py` → `HunterClient` | Add `domain_search()` method. Rename `find_email()` params. |
| `lead_generator.py` | `ApolloClient` | `leadgen/apollo.py` → `ApolloClient` | Preserve for future use. Currently non-functional (403). |
| `lead_generator.py` | `deduplicate_leads()` | `leadgen/normalize.py` → `deduplicate()` | Generalize: dedupe by NIF (SABI) or by (company, email) (Apollo) |
| `lead_generator.py` | `write_csv()` | `leadgen/io.py` → `write_leads_csv()` | Already in the refactored module layout |
| NEW | — | `leadgen/sabi.py` → `from_sabi_xlsx()` | Full implementation per Section 4 |
| NEW | — | `leadgen/scoring.py` → `compute_icp_score()` | Configurable weights from `.yellowbird.toml` |
| NEW | — | `leadgen/cli.py` → Typer app | Full CLI per Section 6 |

## Appendix B — Package Structure

```
project-nexus-core/
├── src/
│   ├── leadgen/
│   │   ├── __init__.py
│   │   ├── models.py          # Lead dataclass, Vertical enum, Tier enum
│   │   ├── io.py              # from_apollo_csv, from_sabi_xlsx, write_leads_csv
│   │   ├── normalize.py       # clean_apollo_value, deduplicate, strip_legal_suffix
│   │   ├── verify.py          # HunterClient (verify, domain_search, find_email)
│   │   ├── scoring.py         # compute_icp_score, assign_tier
│   │   ├── research.py        # AnthropicResearchClient (Milestone 3)
│   │   ├── sabi.py            # SABI-specific parsing, CNAE map, revenue parser
│   │   ├── config.py          # .yellowbird.toml loader, env var merge
│   │   ├── cli.py             # Typer CLI app (all commands)
│   │   └── exceptions.py      # InvalidSABIFormatError, EmptyExportError, etc.
│   └── etl/
│       └── profilers/
│           └── excel_profiler.py  # Existing — untouched
├── tests/
│   ├── unit/
│   │   ├── leadgen/
│   │   │   ├── test_io.py
│   │   │   ├── test_normalize.py
│   │   │   ├── test_scoring.py
│   │   │   ├── test_sabi.py
│   │   │   └── test_cli.py
│   │   └── etl/
│   │       └── test_excel_profiler.py  # Existing — untouched
│   └── fixtures/
│       ├── apollo_raw_sample.csv
│       ├── sabi_export_sample.xlsx
│       └── .yellowbird.toml
├── .yellowbird.toml.example
├── pyproject.toml
└── README.md
```

---

**END OF LEADGEN_ARCHITECTURE.md**

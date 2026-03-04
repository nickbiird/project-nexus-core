# YELLOWBIRD TELEMETRY — Next Steps Execution Roadmap

**Date:** March 4, 2026  
**Status:** Day 1 Complete → Entering Day 2  
**Context:** DNS propagation in progress, GitHub repo live, synthetic data generated

---

## 1. LANDING PAGE SEO & MOBILE AUDIT (Recommendations)

> **Note:** The `index.html` file was not included in this upload session. The following recommendations are based on your described implementation. Upload the HTML in a follow-up and I can audit the actual code line-by-line.

### 1.1 Critical SEO Tags to Add

Add these inside the `<head>` tag if not already present:

```html
<!-- Primary Meta Tags -->
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Yellowbird Telemetry | Recuperación de Margen Operativo para Logística y Construcción</title>
<meta name="description" content="Auditorías de margen operativo para empresas de logística y materiales de construcción (€5M–€20M). Identificamos fugas de margen invisibles. Un archivo. 24 horas. Hallazgos en euros.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://yellowbirdtelemetry.es/">
<html lang="es">

<!-- Open Graph (LinkedIn/Social Sharing) -->
<meta property="og:type" content="website">
<meta property="og:url" content="https://yellowbirdtelemetry.es/">
<meta property="og:title" content="Yellowbird Telemetry | Recuperación de Margen Operativo">
<meta property="og:description" content="Identificamos entre un 3% y un 8% de fugas de margen invisibles en logística y materiales de construcción. Auditoría gratuita en 24 horas.">
<meta property="og:image" content="https://yellowbirdtelemetry.es/og-image.png">
<meta property="og:locale" content="es_ES">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Yellowbird Telemetry | Recuperación de Margen Operativo">
<meta name="twitter:description" content="Auditorías de margen para pymes industriales. Un archivo. 24 horas. Hallazgos en euros.">

<!-- Favicon (create a simple .ico from your logo) -->
<link rel="icon" type="image/png" href="/favicon.png">

<!-- Structured Data (LocalBusiness Schema) -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "ProfessionalService",
  "name": "Yellowbird Telemetry",
  "description": "Auditorías de margen operativo para empresas de logística y materiales de construcción",
  "url": "https://yellowbirdtelemetry.es",
  "areaServed": "ES",
  "address": {
    "@type": "PostalAddress",
    "addressLocality": "Barcelona",
    "addressRegion": "Cataluña",
    "addressCountry": "ES"
  },
  "serviceType": ["Auditoría de datos", "Recuperación de margen operativo"]
}
</script>
```

### 1.2 Mobile Responsiveness Checks

Verify these are in your CSS:

```css
/* Ensure touch targets are at least 44x44px */
.cta-button { min-height: 48px; padding: 14px 28px; }

/* Stack 2x2 grid to single column on mobile */
@media (max-width: 768px) {
  .card-grid { grid-template-columns: 1fr; }
  .hero h1 { font-size: 1.8rem; }
  .sticky-header { position: sticky; top: 0; z-index: 100; }
}

/* Prevent horizontal scroll on mobile */
html, body { overflow-x: hidden; }
img { max-width: 100%; height: auto; }
```

### 1.3 Performance Quick Wins

- Add `loading="lazy"` to any images below the fold.
- If your logo PNG is >50KB, compress it via TinyPNG or convert to WebP.
- Add `<meta name="theme-color" content="#0B1D3A">` for mobile browser chrome color.
- Ensure the contact/audit form section has `id="solicitar-auditoria"` for the smooth-scroll anchor.

### 1.4 OG Image

Create a 1200×630px image for social sharing (this is what shows when someone shares your link on LinkedIn). Navy background, gold eagle logo, "Recuperación de Margen Operativo" in white. Save as `og-image.png` in the site root.

---

## 2. POST-DNS PROPAGATION CHECKLIST (Execute Tomorrow)

### 2.1 Verify DNS Has Propagated

```bash
# Run from terminal — check that your domain resolves to Netlify
dig yellowbirdtelemetry.es +short
# Expected: 75.2.60.5 (Netlify's LB) or a CNAME to netlify

nslookup yellowbirdtelemetry.es
# Should return Netlify IP addresses

# Quick browser test
# Navigate to http://yellowbirdtelemetry.es — should load your page
```

If it hasn't propagated yet, check the nameservers:
```bash
dig yellowbirdtelemetry.es NS +short
# Should show: dns1.p01.nsone.net, dns2.p01.nsone.net, etc.
```

### 2.2 Netlify SSL/HTTPS (Step-by-step)

1. **Log into Netlify** → Open your site dashboard
2. Go to **Site configuration → Domain management**
3. Confirm `yellowbirdtelemetry.es` shows as "Primary domain" with a green checkmark
4. If it says "Awaiting external DNS" → the nameservers haven't propagated. Wait.
5. Once verified, go to **Site configuration → Domain management → HTTPS**
6. Click **"Verify DNS configuration"**
7. Click **"Provision certificate"** — Netlify auto-provisions a free Let's Encrypt cert
8. Wait 2–10 minutes. The status should change to "Your site has HTTPS enabled"
9. Enable **"Force HTTPS"** toggle — this redirects all http:// to https://
10. Test: visit `https://yellowbirdtelemetry.es` — padlock icon should appear

**If SSL provisioning fails:** Netlify needs to see the DNS pointing to them. Ensure you haven't left old A/CNAME records from DonDominio conflicting with Netlify's nameservers. If you delegated nameservers to Netlify, they handle everything.

### 2.3 Zoho Mail Setup (After DNS is confirmed)

Since you delegated nameservers to Netlify, you'll add all Zoho DNS records **in Netlify's DNS panel** (not DonDominio).

**Step-by-step:**

1. **Log into Netlify** → Site → Domain management → **DNS panel** (click your domain)

2. **Add Zoho domain verification TXT record:**
   - Type: `TXT`
   - Name: `@`
   - Value: `zoho-verification=zb########.zmverify.zoho.eu` (Zoho gives you the exact string)
   - TTL: 3600

3. **Go back to Zoho Mail** → Click "Verify" → Should succeed

4. **Add MX records (for receiving email):**
   - `MX` | Name: `@` | Value: `mx.zoho.eu` | Priority: `10`
   - `MX` | Name: `@` | Value: `mx2.zoho.eu` | Priority: `20`
   - `MX` | Name: `@` | Value: `mx3.zoho.eu` | Priority: `50`

5. **Add SPF record (prevents your emails from going to spam):**
   - Type: `TXT`
   - Name: `@`
   - Value: `v=spf1 include:zoho.eu ~all`

6. **Add DKIM record (email authentication signature):**
   - Type: `TXT`
   - Name: `zmail._domainkey` (Zoho specifies the exact selector)
   - Value: (Zoho provides a long DKIM key string — paste it exactly)

7. **Add DMARC record (optional but recommended):**
   - Type: `TXT`
   - Name: `_dmarc`
   - Value: `v=DMARC1; p=none; rua=mailto:audit@yellowbirdtelemetry.es`

8. **Create your mailbox in Zoho:**
   - Primary: `audit@yellowbirdtelemetry.es` (this is what goes on all outreach)
   - Optional: `n.bird@yellowbirdtelemetry.es` (personal founder address)

9. **Test deliverability:**
   - Send a test email from `audit@yellowbirdtelemetry.es` to a personal Gmail
   - Check it doesn't land in spam
   - Reply to confirm two-way delivery works
   - Use [mail-tester.com](https://www.mail-tester.com) — aim for 8+/10 score

**DNS records will take 15–60 minutes to propagate within Netlify's nameservers.**

### 2.4 Post-Launch Verification Checklist

```
[ ] https://yellowbirdtelemetry.es loads with padlock (SSL active)
[ ] http://yellowbirdtelemetry.es auto-redirects to https://
[ ] www.yellowbirdtelemetry.es redirects to yellowbirdtelemetry.es (or vice versa)
[ ] OG meta tags work (paste URL into LinkedIn post composer — preview should render)
[ ] Smooth scroll works on "Solicitar Auditoría" button
[ ] All sections fade in properly on scroll (Intersection Observer)
[ ] Page loads in <3 seconds on mobile (test via PageSpeed Insights)
[ ] audit@yellowbirdtelemetry.es can send AND receive emails
[ ] SPF/DKIM pass (check via mail-tester.com)
[ ] Google Search Console: submit sitemap (optional, low priority for now)
```

---

## 3. STRATEGIC NEXT STEPS: THE 14-DAY SPRINT (Days 2–14)

### Current Status Assessment

| Day | Deliverable | Status |
|-----|-------------|--------|
| 1 | Synthetic messy datasets + repo scaffold | ✅ COMPLETE |
| 1+ | Domain, hosting, landing page, GitHub | ✅ COMPLETE |
| 1+ | DNS propagation + Zoho Mail | ⏳ IN PROGRESS (24h wait) |

### Day 2 (TODAY/TOMORROW): Python Profiling Engine

**File:** `src/etl/profilers/excel_profiler.py`  
**This is the most critical deliverable in the entire sprint** — it powers the Free Audit Hook.

The profiling engine is provided as a separate file in this delivery. Here's what it does:

- Accepts any `.xlsx` or `.csv` file via CLI
- Auto-detects column types (numeric, date, text, entity, financial)
- Computes per-column quality metrics (null %, format inconsistencies, outliers)
- Runs rapidfuzz entity clustering (82% similarity threshold)
- Flags financial anomalies via IQR method
- Generates "Surprise Findings" with estimated € impact
- Outputs a typed `ProfilingReport` with `.to_json()` and `.to_summary_str()`
- Must complete in <60 seconds on 50,000 rows

**Git commit after completion:**
```bash
git add src/etl/profilers/excel_profiler.py tests/unit/etl/test_excel_profiler.py
git commit -m "feat: Day 2 — data profiling engine with entity clustering and financial anomaly detection

- Schema-less ingestion: auto-detects column types from any Excel/CSV
- Data Health Score (0-100): completeness × consistency × uniqueness
- rapidfuzz entity clustering at 82% threshold for supplier/customer dedup
- IQR-based anomaly detection on financial columns with € impact estimates
- Surprise Findings generator: duplicate charges, pricing spread, concentration risk
- CLI interface: python -m src.etl.profilers.excel_profiler <path>
- Completes in <60s on 50K rows
- Full test coverage against synthetic logistics dataset"
```

### Day 3: Streamlit Audit Dashboard

**File:** `dashboard/app.py` + `dashboard/pages/`  
Build the single-page Streamlit visualization of the profiling output:

- **Section 1:** Data Health Score gauge (0–100, color-coded)
- **Section 2:** Entity Duplicate Map (cluster visualization)
- **Section 3:** Top 10 Anomaly Highlights with € amounts
- **Section 4:** Missing Data Heatmap (Plotly)
- **Section 5:** Auto-generated Executive Summary (3 sentences)

Design constraints: Navy/white/amber branding. No feature bloat. Owner understands everything in <30 seconds.

### Day 4: LLM Entity Resolution Module

**File:** `src/llm/entity_resolution/resolver.py`

- Hybrid approach: rapidfuzz pre-filter (fast) → LLM confirmation (accurate)
- Batch entity columns to LLM with Spanish logistics/construction context
- Output: canonical mapping table (original_value → canonical_entity)
- Caching layer (SQLite or JSON) to avoid redundant API calls
- Confidence scoring (high/medium/low) for human review flags

### Day 5: PostgreSQL Schema + Loader

**Files:** `data/schemas/logistics.sql`, `data/schemas/construction.sql`, `src/etl/loaders/postgres_loader.py`

- Normalized star schema: fact_invoices, fact_routes, dim_customers, dim_suppliers, etc.
- SQLAlchemy ORM models with FK constraints
- End-to-end test: Messy Excel → Profile → Clean → Load → Query

### Days 6–8: WhatsApp + NL-to-SQL + Integration

- WhatsApp Business API webhook (Twilio or Meta Cloud API)
- NL-to-SQL engine with Anti-Hallucination Protocol
- Full integration test with 30+ Spanish queries

### Days 9–11: Sales Pipeline & Collateral

- 50-target prospect list (25 logistics, 25 construction, Catalonia)
- 5-touch Challenger outreach sequence
- 4 sales assets (2 vertical PDFs, case study template, ROI calculator)

### Days 12–14: Launch Outreach

- Batch 1: 20 targets via LinkedIn
- Batch 2: 30 targets
- 3 gestoría referral relationships
- First real data through the pipeline

---

## 4. LINKEDIN CONTENT CALENDAR (Parallel Track)

Per the Brand Legitimacy Package, this runs alongside the technical sprint:

| When | Action |
|------|--------|
| Today | Update personal LinkedIn profile + create company page (DO NOT post yet) |
| Tomorrow | Send 20–30 connection requests (no pitch, just connect) |
| Day After (Tuesday) | Publish Post #1: "The 1-10-100 Rule" at 09:00 CET |
| Thursday | Publish Post #2: "The Gut-Feeling Tax" at 09:00 CET |
| Next Tuesday | Publish Post #3: "The Accountant Reframe" (includes audit@ CTA) |

---

**END OF ROADMAP**

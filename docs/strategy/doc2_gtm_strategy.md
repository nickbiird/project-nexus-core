# Yellowbird Telemetry — Go-To-Market Strategy & Network Activation Playbook

**Classification:** Internal — Commercial Strategy  
**Prepared for:** Lucas (Commercial Co-Founder) & Nicholas (Technical Co-Founder)  
**Date:** March 6, 2026  
**Author:** Independent Strategic Review  

---

## 1. The Audit Report as a Challenger Sale Weapon

I have studied the HTML audit report produced on the 60-row test dataset. Here is the honest assessment.

### What Works

The report is beautiful. That is not a throwaway compliment — aesthetics matter enormously with this buyer profile. The DM Serif Display headings, the warm parchment background, the gold accent line, the "Confidencial — Preparado exclusivamente para el cliente" header — all of these signal exclusivity, seriousness, and craftsmanship. A 57-year-old logistics owner who receives this report will register, subconsciously, that this is not a free trial printout from a SaaS dashboard. This feels like a document prepared by a premium consultancy. That perception is worth more than any feature.

The financial quantification is the centrepiece, and it lands correctly. The €122,415 estimated annual impact is presented in a red box with a large serif font — it is literally the most visually prominent element on the page. The individual findings are ranked by impact (€97,715 → €19,232 → €4,814 → €490 → €164), which creates a natural reading hierarchy: the client's eyes go to the biggest number first. The "Pricing inconsistency: 4 entities show >10% price variation" finding is precisely the kind of insight that makes a business owner lean forward. It is specific (4 entities, not "some"), it is actionable (which entities? which invoices?), and it implies knowledge the owner does not have (they did not know their suppliers were charging inconsistent prices).

The health score of 82/100 is the correct commercial choice, as discussed in the technical review. It tells the client: "You're not failing — but there is a gap, and that gap has a euro value." The score would be less effective at 92 (no urgency) or at 62 (too alarming, triggers defensiveness).

### What Does Not Work — And How to Fix It

**The report is in English.** The findings descriptions are in English ("Pricing inconsistency: 4 entities in 'proveedor' show >10% price variation in 'importe_total'"), while the section headers, labels, and metadata are in Spanish. For a product targeting traditional Spanish SME owners — many of whom are not comfortable reading English — this inconsistency is a conversion killer. Every finding description, every label, every tooltip must be in Spanish. "Inconsistencia de precios: 4 entidades en 'proveedor' muestran variación de precios superior al 10% en 'importe_total'" is what the client needs to read.

**The executive summary is bland.** "We analyzed 60 records across 7 columns. We found 3 probable duplicate entities and 6 financial anomalies." This reads like a data dictionary, not a Challenger Sale insight. Compare with: "En su fichero de 60 facturas, hemos identificado €122.415 en fugas de margen anuales. El hallazgo principal: 4 de sus proveedores le están facturando precios inconsistentes en la misma ruta — la variación supera el 10%. Esto por sí solo representa €97.715 al año que se pierde sin que nadie lo robe." That version leads with the money, names the specific problem, and uses the "nobody stole it — it just leaked" language from your sales manifesto. The summary must be rewritten as a Challenger narrative, not a statistical summary.

**The report does not tell the client what to do next.** After the findings, the report ends with column structure and quality metrics — which are interesting to an engineer but meaningless to a business owner. The report needs a "Próximos Pasos" section at the bottom that says: "Para recuperar este margen, recomendamos una revisión operativa completa de sus datos de facturación de los últimos 12 meses. Contacte a [name] para programar una sesión de 30 minutos." This is the call to action that converts a report reader into a sales meeting.

**The confidence levels are confusing.** "Confianza: Medium" and "Confianza: Low" appear next to findings without explanation. A logistics owner does not know what "medium confidence" means in a statistical context. Either remove the confidence labels from the client-facing report (keep them in the internal version) or translate them into business language: "Hallazgo confirmado" (high), "Requiere verificación con datos adicionales" (medium), "Indicador — recomendamos análisis más profundo" (low).

### Objections the Report Pre-empts

The report pre-empts the "my data is fine" objection by showing specific, quantified problems in the client's own data. It pre-empts the "this is too abstract" objection by naming the exact columns, entities, and row counts. It pre-empts the "I don't trust AI" objection by never mentioning AI, algorithms, or machine learning — the language is "análisis," "detección," "revisión sistemática."

### Objections the Report Does Not Pre-empt

The report does not pre-empt the "these numbers seem inflated" objection. The €97,715 finding is extrapolated from 60 rows of test data — the methodology for annualising is not explained. A skeptical CFO will immediately ask: "Where does €97,715 come from on a 60-row file?" The report must include a brief methodology note: "Impacto estimado basado en la proyección del volumen anual de transacciones a partir de la muestra proporcionada." Even better: ask the client for their annual transaction volume during the upload process and use that for the projection.

The report does not pre-empt the "what if this is normal for my industry?" objection. The pricing variation finding shows >10% price variation, but in logistics, fuel surcharges can legitimately cause 10–15% price variation on the same route in different months. The report should contextualise: "Variación de precios ajustada por temporalidad — la variación detectada supera los patrones estacionales esperados." This requires the profiler to control for date-based seasonality, which is a meaningful product enhancement.

---

## 2. Beachhead Market Evaluation

### Spanish SMEs in Logistics and Construction Materials

This is the correct beachhead. The reasoning has three layers.

**Layer 1: The pain is acute and quantifiable.** Logistics companies operating at 2–3% net margins have no room for hidden leakage. A finding of 3% leakage on a €10M business is equivalent to the entire net profit. That is not a nice-to-have insight — it is an existential one. Construction materials suppliers face a parallel challenge with pricing complexity across thousands of SKUs and input cost volatility. Both verticals share the same characteristic: the data exists (invoices, cost records, supplier lists), it is messy (Excel, WhatsApp, paper), and the owner knows it is messy but does not know how to fix it or what it is costing them.

**Layer 2: The buyer profile is homogeneous.** Your sales manifesto describes the buyer accurately — 55-year-old owner-operator, 25 years in business, makes decisions with gut instinct, deeply skeptical of technology, influenced by accountant and peers. This homogeneity means the Challenger script works without significant customisation across the beachhead. You do not need ten different sales narratives for ten different buyer personas. You need one narrative, refined through repetition.

**Layer 3: The network is pre-built.** The Cushman & Wakefield, Garrigues, and EY connections provide warm access to exactly this buyer profile. More on this in the network activation section.

### Realistic Sales Cycle Length

For a first-time purchase of a data auditing product by a traditional SME owner, the realistic sales cycle is 2–4 months from first meaningful contact to signed contract. This is compressed from the industry average of 6–18 months by three factors: (1) the free audit eliminates the "show me it works" objection upfront, (2) the network provides trust acceleration (peer validation from the first contact, not the fifth), and (3) the price point (€1,500–€3,500 setup + €300/month) is within the owner's discretionary spending authority — no procurement committee, no board approval.

However, the cycle has a long tail. Expect 30% of prospects to take 6+ months. These are the "I'll think about it" cases described in the sales manifesto. The discipline is to maintain follow-up cadence without becoming annoying. The free audit report is the asset that does the selling in the background — the owner will re-read it, show it to their accountant, and discuss it with their son/daughter who "knows about technology."

### Realistic ACV

At the stated pricing (€1,500–€3,500 setup + €300/month retainer), the ACV is €5,100–€7,100 in Year 1 and €3,600 in Year 2+. This is the right price point for the target market. Lower than €3,600/year and the product is perceived as unserious — "if it were really worth €200K in margin recovery, why does it cost less than my Vodafone bill?" Higher than €10,000/year and you hit procurement friction and formal vendor evaluation processes.

The realistic revenue target for a solo founder with 10 clients by end of Year 1 is €51,000–€71,000 in first-year revenue, declining to €36,000/year in recurring revenue. This is not a venture-scale number. It is a validation number. It proves the model works, generates case studies, and provides the foundation for either raising capital or scaling to 50 clients with a hired sales rep.

### When to Expand Beyond Spain/Logistics

The product needs to expand beyond the initial beachhead when one of two conditions is met: either the addressable market within Catalonia/Spain is saturated (unlikely within 3 years — there are thousands of qualifying SMEs), or the unit economics require a higher ACV that the current market cannot support (possible if the cost of sales exceeds 50% of first-year revenue, which would happen if the sales cycle lengthens beyond 6 months on average).

The natural expansion path is geographic before vertical: from Catalonia to broader Spain, then to Portugal (similar market structure, regulatory environment, and business culture). Vertical expansion (into real estate, manufacturing, agriculture) is the second axis — and notably, the network connections (Cushman & Wakefield for real estate, Garrigues for any commercial sector) support this expansion naturally.

---

## 3. Network Activation Strategy — Tiered Sequence

This section is the most sensitive in the entire document. The relationships described are not professional connections — they are family. Activating them incorrectly burns social capital that took decades to build and cannot be rebuilt. The sequencing must be precise.

### Tier 0: Internal Proof (Weeks 1–3) — Before Any External Activation

**What happens first.** Before any network relationship is activated, the product must work flawlessly on real data. Not synthetic test data — actual operational data from a company that resembles the target client. The product must be deployed on a live URL (not localhost), accessible via a browser, and capable of producing the audit report within 60 seconds of file upload. The report must be fully in Spanish. The PDF export must work. The call-to-action at the bottom must include a real phone number and email.

**Why this matters.** Lucas's network connections are high-trust, high-scrutiny individuals. A Garrigues partner's professional reputation is built on recommending things that work. If Lucas's father mentions Yellowbird to a client and the product fails, stutters, or produces a confusing report, the partner does not lose faith in the product — he loses willingness to risk his reputation again. That door closes permanently.

**The test:** Nicholas and Lucas should process their own fictional company data through the system. Then process a real dataset from a friendly source (a university contact's small business, a friend's invoice spreadsheet — anything that is not synthetic). Fix every edge case. Only when the report on real data is indistinguishable from the test report in quality do you move to Tier 1.

### Tier 1: The Controlled Case Study — Vertix Grup Inmobiliari (Weeks 3–6)

**Why Vertix is first.** Lucas has a personal friendship with the CEO. This is not a cold introduction mediated by a parent — it is a direct peer relationship. The risk of burning this connection is lower than any parent-mediated introduction because the social dynamics are different: a friend's failed product recommendation is forgiven; a father's failed professional recommendation is remembered.

**The exact conversation.** Lucas should approach the Vertix CEO with this framing: "We've built a tool that analyses operational data — invoices, costs, supplier records — and finds money that's leaking through pricing inconsistencies and data quality issues. We've tested it extensively, but we need to prove it works on real-world data before we launch commercially. Would you be willing to let us run a complimentary audit on a sample of your operational data? We're talking about one Excel file — 6 months of invoices or cost records. We'd present the findings to you privately. If the findings are useful, we'd love to use Vertix as our first case study. If not, you get a free data health check and we learn what we need to improve."

**What data Vertix should upload.** Real estate operational data will differ from logistics invoices. The profiler should receive: supplier invoices (maintenance contractors, cleaning services, property management costs), rental income records (tenant payments, vacancy tracking), or construction/renovation cost logs. The profiler's column type inference will need to handle real estate-specific patterns — property addresses as entity columns, monthly rents as financial columns, m² as numeric columns. This is a valuable test of the profiler's domain-agnostic claims.

**What findings the engine is likely to surface on real estate data.** Pricing inconsistency across maintenance contractors (different contractors charging significantly different rates for the same service type). Revenue concentration risk (one or two major tenants representing a disproportionate share of rental income — a genuine risk for a real estate company). Potentially: duplicate supplier entries (the same contractor listed under variations of their name). The financial impact will be smaller in absolute terms than in logistics (real estate margins are wider), but the insights are equally actionable.

**How the case study is structured.** After presenting the findings to the Vertix CEO: "Based on your audit, we found [specific findings]. Would you be comfortable with us writing a brief case study — anonymised if you prefer — that describes the type of findings we uncovered and the estimated impact? We would share it only with prospective clients, not publicly." The case study format follows the sales manifesto: Situation → Data Surgery Findings → Financial Recovery → Owner Quote. A case study from a 50+ year-old Barcelona real estate company carries significant weight with the target buyer profile.

### Tier 2: The Accountant Channel — Cushman & Wakefield and EY Adjacent (Weeks 6–10)

**Why this tier is second, not first.** The sales manifesto correctly identifies that "the accountant is the de facto technology advisor" for traditional SME owners. The most powerful channel for this product is not direct sales — it is accountant referrals. Nicholas's father (Cushman & Wakefield) and Lucas's mother (EY) operate in advisory ecosystems where accountants and financial advisors recommend services to their clients. However, activating this channel requires proof: you need the Vertix case study (or an equivalent) before asking anyone to put their professional reputation behind a recommendation.

**The activation sequence.** Nicholas's father is asked to make a low-pressure introduction: "There is a company run by my son and his partner that does data quality audits for SMEs. They found [specific finding] for a real estate client recently. If any of your clients in logistics or construction ever mention data quality issues or margin pressure, it might be worth connecting them." This is not a sales pitch through the parent — it is a referral seed. The parent is not selling the product; they are creating awareness within their professional network that this product exists.

Similarly, Lucas's mother (EY Spain Tax Partner) has direct exposure to SME clients who are filing tax returns with data that may contain the exact inconsistencies Yellowbird detects. The introduction is: "When you see a client whose financial data has quality issues — inconsistent supplier naming, pricing anomalies, duplicate entries — there is a service that audits this and quantifies the impact. It might be useful to mention to clients who you think could benefit."

**The critical constraint.** Neither parent should be asked to make direct introductions to specific clients at this stage. The ask is awareness, not action. "Mention it if it comes up naturally" is the correct framing. "Can you introduce me to the CFO of [specific company]" is too aggressive and puts the parent in an uncomfortable position. That level of activation is Tier 3, and it requires 3+ successful case studies.

### Tier 3: Direct Introductions — Garrigues, Don Piso, and Targeted Referrals (Months 3–4)

**Prerequisites before activating Tier 3:** At least 3 completed audits with positive client feedback. At least 1 written case study (anonymised is fine). A product that is deployed, stable, and has handled real-world data without failures. The PDF report export is working. The Spanish-language UX is complete.

**Lucas's father (Garrigues M&A Partner).** The ask at this tier changes from awareness to targeted introduction: "We've completed audits for [number] companies and consistently found [pattern]. There is a specific client profile that benefits most: logistics or construction companies in the €5M–€20M range with operational data in Excel. If there is a client you're working with on a transaction where data quality is relevant — an M&A due diligence, a restructuring, a valuation — we could offer a complimentary audit as part of the advisory process." This framing positions Yellowbird as a complement to the Garrigues advisory service, not as a separate sales pitch. The Garrigues partner is not selling a product — they are enhancing their own service offering.

**Don Piso.** The university friend's father owns a real estate franchise network. The activation here is through Lucas's friend, not through the parents: "Your father's company processes thousands of invoices across franchisees. We built a tool that finds money hiding in that data. Can you ask your father if he would be open to a 30-minute demo?" The franchise model is particularly interesting because a successful audit at Don Piso creates a replicable playbook across all franchisees — each franchisee is a potential client.

### Tier 4: Garrigues/EY Formal Partnership (Month 6+)

This tier is aspirational and should not be planned in detail yet. The concept: position Yellowbird as a "data quality audit" offering within Garrigues's or EY's advisory toolkit. This requires a formalised service agreement, professional liability considerations, and a product that can withstand enterprise scrutiny. It also requires the founders to have incorporated the company (see Document 3). Do not pursue this before the company is a registered S.L. with professional liability insurance.

---

## 4. The 10–20 Client Target: March to June 26th

### Is It Realistic?

No. Not as traditionally defined.

Twenty paying contracts between now and June 26th is not achievable for a solo founder who is also completing a university semester, finishing Phase 4 engineering work, deploying to production, and preparing for a Gartner internship. The sales cycle alone is 2–4 months, which means prospects contacted in March will not sign until May or June at earliest.

However, the target is achievable if "client" is redefined appropriately for this stage.

### What "Client" Should Mean

**5–8 completed free audits** where a real company has uploaded real data and received a report. These are not paying clients. They are proof points. Each one generates a case study, exposes edge cases in the profiler, and creates a relationship that can convert to a paying contract after the Gartner internship.

**2–3 signed pilot agreements** where the client agrees to a 90-day pilot at a reduced rate (€500 setup + €150/month, or even free for the first 90 days in exchange for a testimonial and case study rights). The pilot converts to full pricing after 90 days if the client sees value.

**1 paying client** — a full-price contract that validates willingness to pay. This is the most important number. Not because of the revenue (€7,100 is immaterial) but because it eliminates the biggest existential question: "Will anyone actually pay for this?" One paying client changes the founder's psychology, the co-founder's conviction, and the narrative with future investors.

### The Minimum Viable Pipeline to Enter Gartner with Credibility

By June 26th, you need:
- A live product on a public URL with SSL, authentication, and PDF export.
- 5+ completed audits on real company data (Vertix + 4 others from network).
- 1+ paying client (even at pilot pricing).
- 2+ written case studies.
- A 30-second demo script: open browser, show the dashboard, upload a file, show the report, point to the €X finding, say "we found this for a logistics company in Barcelona in 24 hours."

This pipeline gives you the right to say, during the Gartner internship, "I'm building a data auditing product for SMEs — we have paying clients and case studies." That sentence opens doors at Gartner that "I'm building a startup" does not.

---

## 5. 90-Day Commercial Sprint Plan (March 6 – June 5, 2026)

### Weeks 1–2 (March 6–19): Product Readiness

Nicholas: Deploy to production. Domain registration, SSL, VPS provisioning. Single-tenant deployment. Fix the Spanish-language issues in the report. Implement PDF export. This is the engineering sprint that unlocks everything else.

Lucas: Prepare the Vertix conversation. Draft the case study template. Write the pilot agreement template (a 1-page document, not a contract — the legal formalisation comes after incorporation). Identify 10 additional warm contacts in the network who could receive a free audit.

Milestone: The product is live at `https://app.yellowbird.es` (or equivalent) and produces a Spanish-language PDF report.

### Weeks 3–4 (March 20 – April 2): Vertix Engagement

Lucas: Approach the Vertix CEO. Deliver the pitch as described in Tier 1 above. Secure the data sample.

Nicholas: Run the Vertix audit. Fix any edge cases in the profiler. Produce the report. Prepare the presentation.

Milestone: Vertix audit completed. First real-world data processed. Findings presented to the Vertix CEO.

### Weeks 5–6 (April 3–16): Case Study and Tier 2 Activation

Lucas: Write the Vertix case study (with CEO approval). Begin Tier 2 activation — the low-pressure awareness seeding with parents' networks.

Nicholas: Implement Phase 4 (auth and multi-tenancy) — the product must support multiple clients before the second audit. Begin profiler improvements based on Vertix edge cases.

Milestone: Vertix case study written. Tier 2 conversations initiated. Multi-tenancy deployed.

### Weeks 7–8 (April 17–30): Pipeline Expansion

Lucas: Activate the 10 warm contacts identified in Week 1. Use the Vertix case study as the opening asset. Target: 5 free audit conversations.

Nicholas: Process incoming audit requests. Fix profiler issues. Improve report quality based on client feedback.

Milestone: 3+ additional free audits completed or in progress. Pipeline of 10+ warm prospects.

### Weeks 9–10 (May 1–14): Conversion Push

Lucas: Convert the most engaged free audit recipients to pilot agreements. The pitch: "You've seen the findings. For €500 setup and €150/month for 90 days, we'll run a continuous audit of your operational data and produce a monthly report. If you don't see value in 90 days, you owe nothing more."

Nicholas: Build the automated monthly report capability (scheduled profiling runs). Implement email delivery of reports.

Milestone: 1–2 signed pilot agreements. Revenue begins (even at reduced rates).

### Weeks 11–12 (May 15–31): Stabilisation and Handover

Lucas: Continue pipeline management. Attempt to close 1 full-price contract.

Nicholas: Stabilisation sprint. Fix all known bugs. Write the operational runbook for the Gartner period. Ensure automated monitoring is in place. Document the deployment and incident response procedures so Lucas can handle basic operations.

Milestone: 1 paying client (or strong pipeline commitment). Product stable. Runbook documented. Ready for the founder to step back during the Gartner internship.

### Week 13 (June 1–5): Pre-Gartner Buffer

Both: Review all active clients and prospects. Ensure no open commitments that require Nicholas's daily involvement. Set expectations with pilot clients that response times may increase during June–August. Establish a weekly check-in schedule between Nicholas and Lucas.

Milestone: Clean handover. Lucas is primary client contact. Nicholas is available for critical engineering issues only.

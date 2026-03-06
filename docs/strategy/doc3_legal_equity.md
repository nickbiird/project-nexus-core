# Project Nexus Core — Corporate Formation, Equity Design & Legal Strategy

**Classification:** Confidential — Founders Only  
**Prepared for:** Nicholas, Lucas, and their legal/tax advisors  
**Date:** March 6, 2026  
**Author:** Independent Strategic Review  
**Disclaimer:** This document provides strategic framing for discussion with qualified legal and tax professionals. It is not legal advice. The founders should engage a corporate lawyer (ideally from Garrigues's startup practice, not the partner-father's M&A group — see Section 6) and a tax advisor to formalise the structure.

---

## 1. Incorporation Timing

**Recommendation: Incorporate before the first paying client. Specifically, incorporate before any client data is processed under a formal agreement.**

The reasoning is threefold.

First, GDPR. Article 4(7) defines the "controller" as the natural or legal person that determines the purposes and means of processing personal data. If you process a client's operational data as two unincorporated individuals, Nicholas and Lucas are personally the data controllers. If a data breach occurs, personal liability attaches to each individual. An S.L. (Sociedad Limitada) creates a legal entity that is the controller, and limited liability protects the founders' personal assets. This is not theoretical — the AEPD (Agencia Española de Protección de Datos) has imposed fines on individual controllers, and the personal liability exposure is unlimited under GDPR.

Second, client trust. A traditional Spanish business owner will not sign a contract — even a pilot agreement — with two university-age individuals operating without a legal entity. The S.L. provides a CIF (Código de Identificación Fiscal), which is required on every invoice, contract, and DPA. More importantly, it signals permanence. "Yellowbird Telemetry S.L." on a contract carries different psychological weight than "Nicholas [surname] y Lucas [surname], autónomos."

Third, tax structure. Two individuals receiving pilot payments without a corporate entity must register as autónomos (self-employed). The autónomo social security contribution is a fixed monthly cost (~€300/month minimum in 2026), regardless of income. This is disproportionately expensive when revenue is €500/month from one pilot client. An S.L. allows the founders to defer salary payments until the company has meaningful revenue, and the corporate tax rate (25% general, 15% for new entities in their first two profitable fiscal years) is more favourable for reinvesting early revenue into product development.

**Timeline: Incorporate by April 15, 2026.** This gives two weeks to prepare the documentation and two weeks for the Registro Mercantil to process the filing. The first pilot agreement (targeted for Weeks 9–10 of the commercial sprint) should be signed by the S.L., not by the individuals.

---

## 2. Entity Type: S.L. vs. S.A. vs. International Structures

### The Recommendation: Sociedad Limitada (S.L.)

An S.L. is the correct entity for this stage. The reasoning:

**S.L. vs. S.A.** A Sociedad Anónima (S.A.) requires €60,000 in share capital (€15,000 minimum fully paid up), formal board structures, and more onerous reporting requirements. An S.L. requires €3,000 in share capital (fully paid at incorporation, or €1 via the S.L. de Formación Sucesiva route) and allows governance by a single administrator or joint administrators. For two co-founders at pre-revenue stage, the S.L. is the only rational choice. The S.A. becomes relevant only if the company raises institutional equity capital or exceeds the thresholds that mandate S.A. conversion (which are high enough to be irrelevant for years).

### International Holding Structures

Given that Lucas's parents are a Garrigues M&A partner and an EY Tax Partner, the founders have access to sophisticated structuring advice. The question is whether the access should be used at this stage.

**Dutch BV holding.** The classic Dutch structure provides participation exemption on dividends and capital gains, which is valuable when distributing profits from an operating subsidiary to a holding company. However, it requires a Dutch-registered entity with substance requirements (real office, board meetings in the Netherlands), annual filing costs (~€3,000–€5,000), and a Dutch tax advisor. For a pre-revenue startup, this is a cost centre with no current benefit. The participation exemption becomes relevant only when the S.L. distributes dividends exceeding approximately €20,000/year — which is not imminent.

**Delaware C-Corp with Spanish subsidiary.** This is the standard structure for startups intending to raise US venture capital. It provides access to US institutional investors, standard SAFE/convertible note instruments, and a legal framework that VCs and angels are comfortable with. However: the founders are not currently raising US capital, the product is sold exclusively in Spain, the clients are Spanish SMEs, and the operational complexity of maintaining a Delaware entity from Barcelona is non-trivial (annual franchise tax, registered agent fees, dual tax filings, transfer pricing documentation between the US parent and Spanish subsidiary). This structure is worth implementing if and when the founders raise a seed round from US or international investors. It should not be implemented at incorporation.

**UK Ltd.** Post-Brexit, a UK limited company provides no meaningful advantage over an S.L. for a Spain-based, Spain-targeting business. The UK's dividend tax treatment is less favourable than Spain's for small companies, and the regulatory burden of maintaining a UK entity from Spain creates unnecessary complexity.

**The call: Incorporate a Spanish S.L. now. Restructure later if the business scales internationally or raises foreign capital.** The restructuring (e.g., creating a Dutch BV or Delaware C-Corp as a holding entity above the S.L.) can be done retroactively with minimal friction. It is a five-figure transaction when the time comes. It is not worth the complexity or cost at the current stage.

**What to ask Lucas's parents at this stage.** Ask Lucas's mother (EY Tax Partner) one specific question: "Given two co-founders, both Spanish tax residents, incorporating an S.L. in Barcelona with the intention of potentially raising international capital in 12–18 months, is there any structural decision we should make at incorporation that would be expensive to undo later?" This is a narrow, answerable question that leverages her expertise without asking for ongoing advisory work. The likely answer: ensure the statutos (articles of association) include flexible share class provisions and do not restrict share transfers in ways that would complicate a future funding round.

---

## 3. Equity Split Framework

This is the most consequential decision the founders will make, and it must be made with care, fairness, and clear reasoning.

### The Contribution Assessment

**Nicholas's contributions:**
- Sole technical architect and developer of the entire platform — approximately 3+ months of full-time equivalent engineering work.
- The profiling engine, which is the core intellectual property.
- The leadgen pipeline (190+ unit tests, SABI integration).
- The infrastructure (Docker, CI/CD, PostgreSQL, structured logging).
- Ongoing technical maintenance, bug fixes, and feature development.
- ML research and development (Tsinghua period).

**Lucas's contributions:**
- Co-authored the Challenger Sale strategy and commercial positioning.
- Network access: personal friendship with Vertix CEO, university connection to Don Piso.
- Family network access: Garrigues M&A partner (father), EY Tax Partner (mother).
- Commercial execution: client conversations, pilot sales, relationship management.
- Primary client-facing role during Gartner and Tsinghua periods.

### The Framework

**Recommendation: 55/45 in favour of Nicholas, with a 4-year vesting schedule and 1-year cliff for both founders.**

The reasoning for 55/45 rather than 50/50: Nicholas has built the entire technical platform alone over 3+ months. The IP — the profiling engine, the entity resolution logic, the health score model, the leadgen pipeline — is entirely his creation. In standard startup equity frameworks (Y Combinator, Carta), the founder who has contributed the IP prior to incorporation receives a premium. However, the premium is modest (not 70/30) because Lucas's network is genuinely material — the Garrigues, EY, Cushman & Wakefield, Vertix, and Don Piso connections are not aspirational; they are immediate and actionable. A 55/45 split acknowledges both the IP contribution and the network contribution while remaining close enough to equal that neither founder feels undervalued.

The argument against 60/40 or more aggressive splits: Lucas's continued engagement is essential for the commercial success of the product. If Lucas feels the split is unfair, his motivation to activate his network and manage client relationships decreases. The network is not a one-time asset — it requires ongoing relationship maintenance, and Lucas's willingness to leverage it is proportional to his perceived stake. A 5-point premium for IP is fair. A 15-point premium risks the commercial partnership.

### Vesting Schedule

**4-year vesting with 1-year cliff, monthly vesting thereafter.**

Both founders vest on the same schedule. At incorporation, all shares are issued but subject to a reverse vesting agreement (pacto de restricción de transmisión with buyback right). If either founder leaves before the 1-year cliff, the departing founder's unvested shares are repurchased by the company at nominal value. After the cliff, shares vest monthly (1/48th per month for the remaining 36 months).

**Acceleration clause.** Single-trigger acceleration on a change of control (acquisition): if the company is acquired, all unvested shares accelerate to fully vested. This protects both founders from a scenario where the company is sold and a founder is terminated, losing their unvested equity.

**The Lucas network complexity.** Lucas's family network is a material asset. The question is whether this asset should be reflected in the equity split or in a separate arrangement. The recommendation: it is already reflected in the 45% allocation. Do not create a separate "network contribution agreement" or "advisory share pool" for the network — this creates legal complexity without proportional benefit. The network is Lucas's contribution as a co-founder, just as the codebase is Nicholas's contribution. It vests on the same schedule because both contributions are ongoing.

### Pre-Incorporation Profit Sharing

Between now and formal S.L. formation (target: April 15), any revenue received (e.g., a pilot payment from Vertix) should be handled as follows: the payment is received by one founder (whichever is registered as autónomo, if applicable, or via a simple invoice from one individual to the client). The revenue is split 55/45 after expenses. This is documented in a simple written agreement between the founders — a one-page document signed by both, stating the revenue-sharing ratio, the expense policy (all product-related expenses are shared 55/45), and the understanding that this arrangement terminates upon S.L. incorporation, at which point all revenue and expenses flow through the company.

---

## 4. GDPR Compliance Posture at Incorporation

Before the first client data is processed, the S.L. must have the following in place:

### 4.1 Data Processing Agreement (DPA)

A DPA (Contrato de Encargado de Tratamiento under Spanish LOPDGDD) must be signed with every client before their data is uploaded. The DPA specifies:
- The legal basis for processing: contract performance (Article 6(1)(b) GDPR — the processing is necessary for the performance of the data auditing service contracted by the client).
- The categories of data processed: commercial operational data (invoices, cost records, supplier names, transaction amounts). Explicitly exclude personal data of natural persons unless the client certifies that the data has been anonymised.
- The retention period: data is retained for the duration of the service agreement plus 30 days. After contract termination, all data is deleted within 30 days.
- The technical and organisational measures (TOMs): encryption in transit (HTTPS/TLS), encryption at rest (PostgreSQL with disk-level encryption on the VPS), access controls (authentication, tenant isolation), backup and recovery procedures, and incident response procedure.
- Sub-processors: list Supabase (authentication), the VPS provider (hosting), and Sentry (error tracking — note that Sentry receives stack traces that may contain fragments of data values, so the DPA must address this).

### 4.2 Privacy Policy and Cookie Notice

A privacy policy must be published on the website (`yellowbird.es`) before any client data is collected. It must describe: the controller identity (Yellowbird Telemetry S.L., CIF, registered address), the DPO contact (for a company this size, a DPO is not legally required, but a contact point for data subject requests must be provided), the categories of data, the legal basis, the retention period, and the data subject rights (access, rectification, erasure, portability, objection).

### 4.3 Registro de Actividades de Tratamiento (RAT)

Under Article 30 GDPR, data controllers must maintain a record of processing activities. For a company below 250 employees processing non-sensitive data, this is technically not required — but the AEPD recommends it for all controllers, and it is trivial to maintain. Create a simple document listing each processing activity (data auditing service), the categories of data, the categories of data subjects (client employees whose data appears in invoices), the recipients (sub-processors), and the retention period.

### 4.4 The Sentry Sub-Processor Issue

Sentry captures exception stack traces, which may include variable values from the Python call stack at the time of the error. If the profiling engine crashes while processing a client's invoice data, the Sentry event may contain fragments of that data (supplier names, invoice amounts, dates). This must be addressed in the DPA. The mitigation: configure Sentry's `before_send` hook to scrub sensitive data from events before they are transmitted. The minimum: strip any key containing "name," "amount," "total," "invoice," or "factura" from the event context.

---

## 5. What Garrigues and EY Should Be Asked — And What Should Not

### What to Ask

Ask Lucas's mother (EY Tax Partner): "What is the optimal tax structure for an S.L. with two founders, initial revenue under €50,000/year, and the intention to reinvest all early revenue? Should we elect the new entity reduced tax rate (tipo reducido para empresas de nueva creación)? Are there any Catalan or Barcelona-specific fiscal incentives for technology startups that we should claim?"

Ask a junior associate (not the partner-father) at Garrigues's startup/venture practice: "We need standard incorporation documents for an S.L. with two founders, a reverse vesting agreement, and a data processing agreement template compliant with GDPR/LOPDGDD. Can you recommend a Garrigues associate or an external firm that specialises in startup formation?" This routes the work to the appropriate practice group without burdening the M&A partner with work that is below his level.

### What Not to Ask

Do not ask Lucas's father (Garrigues M&A Partner) to handle the incorporation. An M&A partner's hourly rate is €400–€800. Startup incorporation is a €1,500–€3,000 fixed-fee engagement at a generalist firm or a specialist startup law firm (such as Rousaud Costas Duran, Cuatrecasas's startup practice, or one of Barcelona's boutique tech law firms). Using a senior M&A partner for this work is financially irrational and socially awkward — it puts the partner in the position of either charging his son's friend full rate (uncomfortable) or doing pro bono work that is beneath his expertise (also uncomfortable).

Do not ask either parent to be listed as a director, advisor, or shareholder. Their professional positions at Garrigues and EY create potential conflicts of interest if they have formal roles in a client-facing technology company. Keep the family network as an informal asset, not a formal governance arrangement.

Do not ask Garrigues or EY to be the company's ongoing legal or tax advisor on a retained basis. This creates dependency, obligation, and the perception that the founders are leveraging family connections for free professional services. Engage an independent firm for ongoing legal and tax work. Use the family network for introductions and one-time strategic questions only.

---

## 6. Legal Milestones Before the First Paying Contract

The following must occur in sequence:

**Week 1 (March 6–12):** Draft the founders' agreement. This is a pre-incorporation document signed by Nicholas and Lucas that specifies: the equity split (55/45), the vesting terms, the roles (Nicholas as CTO/sole administrator, Lucas as commercial director), the pre-incorporation profit-sharing arrangement, and the commitment to incorporate by April 15.

**Week 2 (March 13–19):** Engage a startup lawyer. Obtain a quote for S.L. incorporation including: drafting the estatutos (articles of association), the share issuance, the reverse vesting agreement (pacto de socios), and a template DPA. The total cost should be €2,000–€4,000 for a reputable Barcelona startup firm.

**Weeks 3–4 (March 20 – April 2):** The lawyer drafts the estatutos and pacto de socios. The founders review, negotiate any points of disagreement (this is the moment to resolve any tension about the equity split, not later), and sign.

**Week 5 (April 3–9):** Incorporation at notary. The S.L. is constituted with €3,000 share capital (€1,650 from Nicholas, €1,350 from Lucas, reflecting the 55/45 split). The notary submits the escritura pública to the Registro Mercantil.

**Week 6 (April 10–16):** Obtain the CIF provisional. Register for AEAT (tax obligations). Open a corporate bank account. Register the DPA template. Publish the privacy policy on the website. The company is now legally operational.

**Weeks 7–8 (April 17–30):** The first pilot agreement is signed by Yellowbird Telemetry S.L. with the first client. The DPA is countersigned. Client data processing begins under the legal entity.

Any pilot agreements signed before Week 6 should be conditional: "This agreement becomes effective upon the incorporation of Yellowbird Telemetry S.L., expected by [date]." This avoids processing client data under personal liability.

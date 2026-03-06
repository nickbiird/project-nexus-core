# Nicholas — 18-Month Strategic Execution Plan: March 2026 to September 2027

**Classification:** Personal — Founder Eyes Only  
**Date:** March 6, 2026  
**Author:** Independent Strategic Review  

---

## Phase 1: The Pre-Gartner Sprint (March 6 – June 26, 2026)

### What Is Achievable

You have 112 days. You are finishing a university semester. You are simultaneously building Phase 4 (auth, multi-tenancy), deploying to production, incorporating a company, and attempting to sign your first clients. This is an aggressive agenda. Here is the honest assessment of what can be accomplished.

**Production deployment: Yes.** You can have the product live on a VPS with a domain, SSL, and CI/CD auto-deploy within 2 weeks. The Docker infrastructure is already built. The deployment is a weekend of DevOps work: provision a €20/month Hetzner VPS (they have a Falkenstein data centre with excellent EU latency), install Docker, configure a reverse proxy with Let's Encrypt, set up GitHub Actions to SSH-deploy on merge to main. This is the single highest-priority technical task.

**PDF report generation: Yes.** This is a 3–5 day engineering task. Use WeasyPrint (Python library, generates PDF from HTML/CSS). Your existing HTML report template is already the input. The output is a branded PDF that the client can email to their accountant. This is the artefact that travels through the client's organisation and generates inbound referrals. It is the second highest-priority technical task.

**Supabase Auth and multi-tenancy: Partially.** The full implementation described in Document 1 is a 3–4 week engineering sprint. You may not complete it before June 26. The question is whether you need it for the first 5 clients. The answer: no. For the first 5 clients, you are hand-delivering the product. You know who each client is. You can manage tenant isolation manually (separate database schemas, or even separate VPS instances at €20/month each). The multi-tenancy architecture is essential for scaling past 10 clients but is not a blocker for the first 5. Implement a basic login (Supabase email/password, no multi-tenancy — just a single-tenant auth layer that prevents anonymous access) and defer the full multi-tenancy implementation to the stabilisation period or the post-Gartner window.

**5–8 completed free audits: Achievable with Lucas's full engagement.** Nicholas's role is to process the data and fix edge cases. Lucas's role is to secure the data samples. The Vertix engagement alone should yield 1 audit by Week 4. The remaining 4–7 require Lucas to activate his warm contacts aggressively from Week 5 onwards.

**1 paying client: Achievable but not guaranteed.** This depends on whether the free audit recipients are sufficiently impressed to convert, and on the founders' ability to close. The 90-day pilot at reduced pricing is the correct conversion vehicle. If the Vertix audit surfaces €50,000+ in estimated impact, the conversation becomes: "We found €50K in leakage. For €500, we'll monitor this continuously for 90 days." That is a trivially easy close.

**S.L. incorporation: Yes.** This is a bureaucratic task that runs in parallel with the engineering and commercial work. Lucas should own this workstream entirely, with the lawyer doing the heavy lifting.

### The Primary Risk in This Phase

The primary risk is not technical failure. The product works. The primary risk is attention fragmentation. You are simultaneously an engineering lead, a DevOps engineer, a founder, and a student. The university semester will demand attention at unpredictable times (exams, group projects, deadlines). The temptation will be to work on the product instead of studying, or to study instead of deploying. Neither choice is correct.

The mitigation: block your calendar. Engineering work happens Monday/Wednesday/Friday mornings. University work happens Tuesday/Thursday. Client work happens in the evenings and weekends, because that is when traditional business owners are available for informal conversations. Lucas handles all client-facing communication during weekdays. You handle all engineering. Neither of you touches the other's domain without discussion. Role clarity is the antidote to attention fragmentation.

---

## Phase 2: The Gartner Internship (June 26 – August 28, 2026)

### The Conflict of Interest Question — A Direct Answer

**There is a meaningful conflict of interest risk, and you must manage it proactively.**

Gartner operates as a technology research and advisory firm. Their revenue comes from enterprise clients paying for market intelligence, vendor evaluations, and strategic technology advice. Their Account Managers sell advisory subscriptions to C-level executives — the same audience your product targets (CFOs and owners of SMEs making technology purchasing decisions).

Your product, Yellowbird Telemetry, is a data auditing tool sold to SMEs. It is not a direct competitor to Gartner (Gartner sells advisory, you sell software), but there is overlap in the client universe: a logistics CFO who buys a Gartner subscription might also be a Yellowbird prospect. More importantly, the skills you will develop at Gartner — C-level prospecting, value-based selling, constructing "Mission Critical Priority" narratives — are directly transferable to and developed for selling Yellowbird.

**What to do:**

First, read the internship contract before signing (if you have not already signed). Look for the following clauses: (a) an IP assignment clause — does Gartner claim ownership of intellectual property created during the employment period, even if created outside of work hours? If yes, this is a serious problem because any code you write for Yellowbird during the internship could be claimed by Gartner. (b) A non-compete clause — does it restrict you from working in "research," "advisory," "data analytics," or "technology sales" for a period after the internship? (c) A moonlighting/outside employment clause — does it prohibit or restrict concurrent business activities?

Second, disclose proactively. Before the internship starts, send an email to your Gartner manager and HR contact: "I want to let you know that I am a co-founder of an early-stage company called Yellowbird Telemetry, which provides data quality auditing services to Spanish SMEs. The company is pre-revenue [or: has a small number of pilot clients]. I want to ensure full transparency and compliance with Gartner's policies on outside business activities. Please let me know if any adjustments are needed." This disclosure protects you legally. If you do not disclose and Gartner discovers the startup later, the consequences are severe (termination, potential legal action). If you disclose upfront, the most likely outcome is that Gartner sets boundaries (no client overlap, no use of Gartner resources for Yellowbird, no sales activity during work hours), which you can comply with.

Third, during the internship, do not sell Yellowbird. Do not prospect. Do not contact Yellowbird leads using Gartner tools, Gartner client lists, or knowledge gained from Gartner client interactions. Lucas manages all commercial activity. Your involvement is limited to critical engineering fixes and strategic decisions, communicated via personal devices outside work hours. Do not mention Yellowbird to Gartner clients or colleagues in any commercial context.

**The honest assessment of whether the internship is an accelerant or a distraction.** It is both, and the net effect depends on execution. The accelerant: two months of intensive training in C-level selling, value narrative construction, and enterprise account management — skills that are directly applicable to selling Yellowbird and that would take years to develop organically. The exposure to Gartner's methodology for evaluating technology vendors will sharpen your competitive positioning. The brand on your CV ("Gartner Sales Academy") signals seriousness to future investors and clients. The distraction: two months during which you cannot actively sell Yellowbird, cannot push major engineering features, and must maintain the product in maintenance mode. If client issues arise that require your attention, you will be stretched thin.

**The net assessment: take the internship.** The skills and credibility it provides are worth more than two months of additional Yellowbird development. But structure the pre-Gartner sprint to minimise the cost of the pause. The product must be stable and self-running before June 26. Lucas must be fully empowered to manage clients. The runbook must be written.

---

## Phase 3: Tsinghua University (September 2026 Onwards)

### The ML Integration Plan — Realistic Assessment

You completed ML and deep learning coursework. You will have access to Tsinghua faculty and research infrastructure. The question is whether this access translates into a meaningful product improvement for Yellowbird.

**The realistic uplift from ML for this specific product.**

The current profiling engine is entirely rule-based: IQR for outliers, `rapidfuzz` for entity matching, weighted scoring for health. On the target data (Spanish SME operational CSVs, 60–50,000 rows), these rules work well. The question is: what does ML add that rules cannot?

The answer is narrow but genuine. ML adds two things: (1) better entity resolution (as described in Document 1 — a fine-tuned sentence transformer on Spanish company names can distinguish semantic equivalences that edit distance misses), and (2) anomaly classification learning (a model that learns from labeled audit data which detected anomalies are true findings versus false positives, improving precision over time). Both of these require training data that you will only have after processing 50+ real client audits. Until then, ML is a research project, not a product feature.

**What can realistically be built in six months at Tsinghua.** A prototype entity resolution model trained on SABI company name data. This is achievable because (a) SABI provides ground truth (CIF numbers map name variants to legal entities), (b) the model architecture is standard (fine-tuned sentence transformer), and (c) the compute requirements are modest (this is a small model, trainable on a single GPU). The prototype should be benchmarked against the current `rapidfuzz` approach on a held-out test set. If the improvement in clustering accuracy is less than 5 percentage points, the ML approach is not worth the operational complexity and should be shelved.

**What cannot be built.** Predictive anomaly detection ("this transaction will become a problem next month") requires time-series data across multiple audit periods for the same client. You will not have this data until clients have been using the product for 6+ months. Automated report narrative generation (using an LLM to write the executive summary) is technically feasible but commercially risky — the Challenger Sale narrative must be carefully controlled, and an LLM that produces a bland or inaccurate summary undermines the premium positioning. Keep the narrative human-authored for now.

**Is ML a competitive advantage or a distraction?** At this stage, it is a distraction from the commercial fundamentals. The product's competitive advantage is not technical sophistication — it is the combination of domain-specific Spanish-market profiling, the Challenger Sale narrative, and the network-driven GTM. A competitor with an ML-powered profiler but no network access to Spanish SME owners is less competitive than you with a rule-based profiler and warm introductions to Vertix, Don Piso, and the Garrigues/EY orbit. Invest in ML at Tsinghua as a research hedge — something that deepens the moat over 12–24 months — not as a short-term competitive lever.

**The operational risk of running the company from Beijing.** The 7-hour time zone difference between Beijing and Barcelona means synchronous communication with Lucas and clients is limited to early morning (Beijing time) / late evening (Barcelona time) or late night (Beijing time) / afternoon (Barcelona time). Client issues that arise at 10 AM Barcelona time will not reach you until 5 PM Beijing time. This is manageable if (a) the product is stable (no daily crises), (b) Lucas is empowered to handle all client communication, and (c) engineering escalations are documented in a shared system (GitHub Issues, not WhatsApp — WhatsApp messages get lost in the timezone gap). Establish a daily async standup: Lucas posts client updates in a shared document by 6 PM Barcelona time. You review and respond by 8 AM Barcelona time the next day.

---

## The Question You Should Be Asking But Are Not

**"Am I building a company, or am I building a portfolio project?"**

This is the question that sits beneath every other question in this document, and you have not confronted it directly. Here is why it matters.

Your trajectory over the next 18 months is: build a startup → intern at Gartner → study at Tsinghua. Each of these is individually excellent. Together, they create an ambiguity that will eventually force a decision: are you a founder who happens to also be studying and interning, or are you a student/intern who happens to have a side project?

The answer to this question determines everything. If you are a founder, then the Gartner internship is a tactical asset (learn sales, return to the company), the Tsinghua period is a strategic asset (build ML capabilities, return to the company), and every decision is evaluated through the lens of "does this help Yellowbird succeed?" If you are a student with a side project, then the internship is a career stepping stone (potentially leading to a full-time Gartner offer or similar), Tsinghua is an academic experience (possibly leading to a research career or a Master's at a top US programme), and Yellowbird is a demonstration of capability rather than a lifelong commitment.

Both paths are legitimate. Both can be successful. But they require different decisions at every fork. A founder does not accept a Gartner return offer if the startup is gaining traction. A student does not turn down a Tsinghua research assistantship to debug a profiler for a Barcelona logistics company.

You are 20 years old. You have built something genuinely impressive. You have a network that most founders would trade a limb for. But you also have optionality that will narrow with every commitment you make. The honest advice: treat the next 6 months (March to August 2026) as the experiment that resolves this ambiguity. If, by the time you start at Tsinghua in September, the company has 5+ paying clients, positive client feedback, and a clear path to 20 clients — you are a founder. Commit fully. Treat Tsinghua as a resource for the company, not the other way around. If, by September, the product has not gained commercial traction — the free audits did not convert, the network did not activate, the sales cycle proved longer than expected — you are a student with an impressive project. Pivot gracefully. Use the Gartner experience and the Yellowbird case study to pursue whatever comes next.

The worst outcome is spending two years in a state of ambiguity — not fully committed to the startup, not fully committed to the academic/career path — and ending up with neither a successful company nor the credentials that come from fully pursuing the alternative.

---

## THE BOTTOM LINE

This project has a viable enterprise future. The evidence is structural, not speculative. The product works and produces output that is commercially compelling. The profiling engine is architecturally sound and will scale. The Challenger Sale positioning is well-executed and grounded in genuine market research. The target market (Spanish SMEs in logistics and construction) is large, underserved, and accessible through the founders' network. The unit economics (€7,100 Year 1 ACV against a cost of sale that is primarily the founders' time) are favourable for a pre-revenue startup. The network advantage — Garrigues, EY, Cushman & Wakefield, Vertix, Don Piso — is real, immediate, and nearly impossible for a competitor to replicate.

The risks are real but manageable: the founder's attention is split across too many commitments, the multi-tenancy and GDPR compliance work must be completed before scaling past pilot clients, and the commercial hypothesis (will traditional Spanish SME owners pay €300/month for a data auditing service?) remains unvalidated by a real transaction.

**The single most important thing to do in the next 30 days:** Deploy the product to a live URL, produce a PDF report on the Vertix dataset, and close the first pilot agreement. Not Phase 4. Not multi-tenancy. Not ML. Ship what you have to a real client, collect real money, and validate the commercial hypothesis. Everything else — the auth system, the ML research, the corporate structure, the Gartner internship — is downstream of one question: will a business owner look at your report, see the number, and write a cheque? You will not know the answer until you ask. Stop engineering. Start selling.

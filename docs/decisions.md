# Decision Records

Each record captures a decision with context, options, choice, and reasoning.
Format: `### DRN-XXX: Title`

---

### DRN-001: Assistant Voice

**Date:** 2026-10-23  
**Context:** The AI assistant needs a consistent voice. Options range from speaking *as* Aamir to speaking *about* him.  
**Options:**  
A. Third person — "Aamir built…" with "I'm Aamir's AI assistant" identity  
B. First person — AI speaks as Aamir ("I built…")  
C. Hybrid — introduces itself as assistant, then uses Aamir's name naturally  
**Choice:** A — Third person  
**Why:** Honest (recruiters know it's AI), matches the trust line, avoids uncanny valley of pretending to be a person. User's choice.

---

### DRN-002: LLM Model Selection

**Date:** 2026-10-23  
**Context:** Need to choose Groq models for main answers and utility calls.  
**Options:**  
A. `openai/gpt-oss-120b` for everything  
B. `openai/gpt-oss-120b` for answers, `openai/gpt-oss-20b` for utility  
**Choice:** B — Use 120b for main chat, 20b for utility (query rewriting, JD extraction)  
**Why:** Both have the same rate limits (30 RPM, 1K RPD, 8K TPM, 200K TPD), but the 20b model is cheaper per token. Using two models also provides failover: if one model's quota is hit, the other has its own limits. Model IDs in config.  
**Updated:** 2026-10-23 — user confirmed 20b also exists and works.

---

### DRN-003: External Postgres Provider

**Date:** 2026-10-23  
**Context:** Need a free-tier Postgres for Phase 9+.  
**Options:**  
A. Neon — 0.5 GB, pauses after 5 min idle  
B. Supabase — 500 MB, 2 free projects, good dashboard  
C. Defer decision  
**Choice:** B — Supabase, deferred to Phase 9  
**Why:** More storage, good DX. Not needed until Phase 9 (handoff, analytics). App designed DB-free until then.

---

### DRN-004: Monorepo Name

**Date:** 2026-10-23  
**Context:** Plan says `portfolio-assistant/`, workspace is `aamirmkh-portfolio/`.  
**Choice:** Keep `aamirmkh-portfolio` as-is.  
**Why:** Already set up, no reason to rename.

---

### DRN-005: Agent Instructions File

**Date:** 2026-10-23  
**Context:** Need a root instruction file for AI agents.  
**Options:** AGENTS.md vs CLAUDE.md  
**Choice:** AGENTS.md  
**Why:** Standard convention, read natively by the agent tools.


---

### DRN-006: CORS Configuration Architecture

**Date:** 2026-10-24  
**Context:** The frontend (hosted on Vercel) and backend (hosted on Render) reside on distinct origins. We need robust CORS handling without wildcard exposures.  
**Options:**  
A. Wildcard `allow_origins=["*"]`  
B. Explicit allowlist loaded via environment variables and parsed in `Settings`  
**Choice:** B — Explicit allowlist  
**Why:** Security best practice. Prevents unauthorized cross-origin requests while facilitating local development (`localhost:5173`) and production deployment (`*.vercel.app`).

---

### DRN-007: Request Tracing via X-Request-ID

**Date:** 2026-10-24  
**Context:** Need structured traceability across request lifecycles and error logs.  
**Choice:** Middleware generating UUIDv4 or propagating client-supplied `X-Request-ID`.  
**Why:** Enables end-to-end correlation between client errors, server logs, and frontend status reporting.

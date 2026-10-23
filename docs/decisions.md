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
A. `openai/gpt-oss-120b` for answers, `llama-3.1-8b-instant` for utility  
B. `openai/gpt-oss-120b` for everything  
C. `llama-3.3-70b-versatile` for answers, small model for utility  
**Choice:** B — Single model for now  
**Why:** User reports it's the only one working currently. Model IDs are in config so we can split later. Risk: utility calls eat from the same quota.

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

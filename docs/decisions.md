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

---

### DRN-008: Deep LLM Adapter Interface (Protocol Seam)

**Date:** 2026-10-26  
**Context:** Need an abstraction over the Groq API that decouples FastAPI endpoint logic from SDK internals, ensures deterministic test isolation without live API keys, and provides a clear extension point for tool loops and model failover.  
**Options:**  
A. Direct SDK calls inside endpoint handlers  
B. Generic multi-provider wrapper framework (e.g. LiteLLM, LangChain)  
C. Thin in-house protocol `LLMClient` with a single `complete()` method  
**Choice:** C — Thin in-house protocol `LLMClient`  
**Why:** Complies with no-LangChain hard rule and deep-module engineering standard. `GroqLLM` encapsulates `AsyncGroq`, timeout/retry, token counting, and error mapping. `FakeLLM` satisfies the identical protocol for sub-second, zero-cost CI tests. Injected via FastAPI `Depends`.

---

### DRN-009: Context-Stuffed System Prompt Baseline (Phase 1)

**Date:** 2026-10-26  
**Context:** Need to ground conversational responses in verified facts prior to building Phase 2 hybrid RAG.  
**Options:**  
A. Early RAG prototype with chunks and vector store  
B. Context stuffing full résumé markdown into the system prompt  
**Choice:** B — Context stuffing full résumé into system prompt  
**Why:** Résumé context is ~1,380 prompt tokens, fitting comfortably within Groq's 8,000 TPM limit for `openai/gpt-oss-120b`. Enables immediate end-to-end conversational capability and prompt verification (third-person persona, honest "I don't know" fallback) without adding retrieval complexity prematurely. Excludes phone number per hard safety rules.

---

### DRN-010: Native Starlette StreamingResponse for SSE over POST

**Date:** 2026-10-27  
**Context:** Need to stream token chunks from FastAPI to React via Server-Sent Events (SSE). The endpoint accepts JSON bodies via HTTP POST (`/api/chat/stream`).  
**Options:**  
A. Add third-party dependency `sse-starlette`  
B. Use built-in Starlette/FastAPI `StreamingResponse` formatted as SSE frames (`event: ...\ndata: ...\n\n`)  
**Choice:** B — Native `StreamingResponse`  
**Why:** Avoids adding unnecessary external dependencies to the pinned requirements. Provides 100% direct control over SSE framing, in-stream error events, and flush headers (`Cache-Control: no-cache, no-transform`, `Connection: keep-alive`, `X-Accel-Buffering: no`).

---

### DRN-011: Hand-Built Streams API SSE Client over POST

**Date:** 2026-10-27  
**Context:** Browser-native `EventSource` only supports GET requests and cannot send JSON payloads or custom headers. We need an SSE client that works over HTTP POST for conversation requests.  
**Options:**  
A. Pull in `@microsoft/fetch-event-source` or third-party client library  
B. Hand-built client `streamChat()` in `frontend/src/lib/sse.ts` using `fetch()`, `ReadableStreamDefaultReader`, and `TextDecoder`  
**Choice:** B — Hand-built client  
**Why:** Follows project principle "build core pieces by hand before adopting frameworks". Keeps initial JS bundle lean (73 KB gzipped, well inside our <200 KB budget). Guarantees strict TypeScript type safety, cleanly handles chunk buffering across arbitrary byte boundaries, and integrates directly with React's `AbortController` for instant user cancellation.

---

### DRN-012: Latency-Aware Cold-Start UX for Render Free Tier

**Date:** 2026-10-27  
**Context:** Render free-tier web services spin down after 15 minutes of inactivity and require ~25s (up to 33s) to boot on initial request. Users might perceive the application as unresponsive during this window.  
**Options:**  
A. Generic loading spinners without explanation  
B. Background health check on page load with latency timer (>2.5s) triggering a transparent status pill and notice banner  
**Choice:** B — Background health check & latency-triggered status pill  
**Why:** Sets honest recruiter expectations upfront. The application immediately displays "Waking Up (Render ~25s)" if the initial connection takes > 2.5s, reassuring visitors that the service is booting rather than broken.

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


---

### DRN-013: Minimal Editorial Dossier Design System Architecture

**Date:** 2026-10-27  
**Context:** Need a distinctive, professional visual system that presents Aamir's verified technical portfolio without falling into generic AI chatbot aesthetics (e.g. rounded SaaS cards, purple/teal glow gradients, Anthropic terracotta clones) while strictly adhering to our <200 KB gzipped bundle budget.  
**Options:**  
A. External UI / CSS component libraries (Tailwind, Radix, Shadcn)  
B. CSS-in-JS framework (Emotion, Styled Components)  
C. In-house pure CSS design tokens (`tokens.css` + `chat.css`)  
**Choice:** C — In-house pure CSS design tokens  
**Why:** Maintains zero runtime dependencies, strictly preserves our bundle budget (73.74 KB gzipped JS, 3.30 KB gzipped CSS), and gives complete control over light/dark theme variables, hairline dossier borders, fluid typography scales, and WCAG accessibility standards.

---

### DRN-014: Cover State Hero & Graceful Mode Orchestration

**Date:** 2026-10-27  
**Context:** Recruiters arriving at the portfolio need an immediate, authoritative overview of Aamir's identity, verified technical stack, and suggested inquiry directives before entering an active conversation transcript.  
**Options:**  
A. Multi-route SPA with separate `/` and `/chat` paths and route transitions  
B. Unified shell state machine with smooth in-place Cover-to-Chat transition and header reset control  
**Choice:** B — Unified shell state machine  
**Why:** Eliminates client-side router overhead and layout shift (CLS). Provides an intuitive "← Dossier Overview" control that allows recruiters to return to the executive profile at any time without losing context.


---

### DRN-015: Proxy-Aware Sliding Window Rate Limiting Architecture

**Date:** 2026-10-27  
**Context:** Groq free-tier has a 30 RPM limit. We must prevent any individual visitor or scraper from exhausting the API or disrupting service for others, while correctly resolving real client IPs behind cloud reverse proxies (Render load balancers).  
**Options:**  
A. Direct socket IP extraction (`request.client.host`) and fixed-window bucket counters  
B. Proxy-aware IP extraction with RFC header parsing (`X-Forwarded-For` chain, `CF-Connecting-IP`) and in-memory sliding-window limiter (`app.safety.rate_limiter`)  
**Choice:** B — Proxy-aware extraction with sliding-window limiter  
**Why:** Fixed windows allow boundary bursts (e.g. 20 requests in 2 seconds across a minute boundary). Sliding windows enforce a strict rolling rate (10 RPM per IP, with 15 burst allowance). Standard RFC headers (`Retry-After`, `X-RateLimit-*`) provide clear client feedback, and periodic stale key eviction guarantees zero memory leaks.

---

### DRN-016: Two-Tier Prompt Injection Defense & Delimiter Isolation

**Date:** 2026-10-27  
**Context:** Untrusted user inquiries could attempt prompt injection (e.g. "ignore previous instructions", "reveal system prompt", DAN jailbreaks, XML breakout).  
**Options:**  
A. Upstream LLM moderation call (e.g. Llama Guard)  
B. System prompt instructions only  
C. Pre-call deterministic regex guardrails + structural XML delimiter boundary fencing (`<user_inquiry>`)  
**Choice:** C — Pre-call deterministic regex + structural XML fencing  
**Why:** Upstream LLM classification consumes API quota, introduces 500ms+ latency, and adds financial cost. System prompt instructions alone remain vulnerable to jailbreaks. Deterministic regex rejects known imperative override patterns at 0 token cost and sub-millisecond speed, while XML delimiter fencing prevents prompt leakage without false-positives on legitimate recruiter inquiries about prompt engineering or systems architecture.

---

### DRN-017: Global UTC-Rollover Daily Quota Guard

**Date:** 2026-10-27  
**Context:** Groq free tier imposes hard daily limits (1,000 RPD, 200,000 TPD). Traffic surges or repeated testing could drain the account and break the assistant for everyone.  
**Options:**  
A. External database or Redis tracking  
B. In-memory `DailyQuotaGuard` with UTC-midnight calendar rollover and proactive 80% safety cap (800 RPD / 180,000 TPD)  
**Choice:** B — In-memory `DailyQuotaGuard` with UTC rollover  
**Why:** Avoids adding external database dependencies prior to Phase 9. Protects the developer account from total depletion, fails open safely on server restarts, and returns standard HTTP 429 errors with `Retry-After` seconds to UTC midnight when capacity is reached.


---

### DRN-018: Structured Knowledge Base Frontmatter & Chunking Strategy

**Date:** 2026-11-01  
**Context:** The assistant previously stuffed Aamir's entire plain-text résumé into the system prompt (~1,380 tokens per request). This bloated prompt size, risked hallucinating beyond the résumé, prevented fine-grained source attribution, and made it impossible to distinguish between public factual chunks and sensitive runtime policies (such as salary deflections and the recruiter phone-sharing policy).  
**Options:**  
A. Fixed character/sentence sliding-window chunking without metadata  
B. Single monolithic Markdown knowledge file with section header splitting  
C. Curated frontmatter chunks (YAML frontmatter + Markdown content) parsed into immutable Pydantic `FactChunk` models, with draft flags, explicit semantic tags, and private/unindexed segregation.  
**Choice:** C — Curated frontmatter chunks with Pydantic validation  
**Why:** Preserves complete conceptual units (e.g. whole debugging stories, full HR Q&As, project architectures) without chopping sentences mid-thought. Enables granular source section mapping (e.g. `X7`, `J8`, `B1`), allows unverified metrics to be identified in `knowledge-todo.md`, and enables `boundaries.md` to be loaded as prompt instructions while strictly excluded from the public retrieval index.

---

### DRN-019: In-Process Hybrid Retrieval (BM25 + fastembed ONNX + RRF) behind Retriever Protocol

**Date:** 2026-11-01  
**Context:** Need a fast, accurate retrieval system that can run entirely within Render's free tier 512 MB RAM limit, handle exact technical keyword recall (`ETIMEDOUT`, `BullMQ`, `Monaco Editor`, `9.77`) alongside semantic intent ("What did Aamir do at his internship?"), and remain 100% offline and deterministic in CI without external vector database SaaS costs or credentials.  
**Options:**  
A. External Vector DB SaaS (Qdrant Cloud / Pinecone) via remote API  
B. Full PyTorch / Transformers in-process embedding pipeline (~1.5+ GB RAM)  
C. In-process hybrid engine: custom Okapi BM25 ($k_1=1.5, b=0.75$) + FastEmbed ONNX runtime (`BAAI/bge-small-en-v1.5`, 384 dimensions) + Cormack's Reciprocal Rank Fusion ($k=60$) behind an async `@runtime_checkable` `Retriever` protocol seam.  
**Choice:** C — In-process hybrid retrieval with Protocol seam  
**Why:**
1. **Memory Gate Passed:** Total container WorkingSet after loading the ONNX model and indexing all 75 facts is 227.75 MB (<50% of Render's 512 MB cap, leaving >284 MB headroom).
2. **Speed:** Average retrieval latency is 9.39 ms on CPU (p95 11.01 ms), well below the 25 ms ceiling.
3. **Retrieval Quality:** Achieves 100.0% Hit Rate@5 (45/45 queries) and 0.8778 MRR on the labeled evaluation set.
4. **Architectural Seam:** Clean dependency injection via `get_retriever()` enables `FakeRetriever` in unit tests (0.68s execution) and allows plugging in an external `QdrantRetriever` after Gate 2 without modifying a single line of endpoint code.

# Decision Records

Each record captures a decision with context, options, choice, and reasoning.
Format: `### DRN-XXX: Title`

### DRN-037: Retrieval metrics with honest denominators and portable gates

**Date:** 2026-11-04
**Context:** The legacy benchmark used alternative source IDs for Hit@5 and a machine-dependent latency assertion. Phase 8 needs distinct top-three/top-five metrics, without converting alternative sources into exhaustive relevance labels or scoring skipped behaviors as successes.
**Choice:** Use shared pure ranking metrics for the CLI and legacy aggregate regression. Report Hit@3/@5, explicitly truncated MRR@5, and macro Recall@3/@5 only over `all_relevant` labels. Alternative-source cases do not contribute to recall; no-source cases have no score. Exclude protocol, requirement-extraction JDs and histories requiring recorded rewriting from the raw-query retrieval diagnostic. Retain excluded counts/reasons and all legacy individual top-five regressions. Portable gates are Hit@3 >=0.90 and MRR@5 >=0.80, plus every legacy Hit@5. Report warmed latency and nearest-rank percentiles separately; the previous default mean <25 ms assertion becomes an opt-in, separately recorded `--max-mean-ms` benchmark gate.
**Provenance and failure:** Validate frozen evidence before loading cached ONNX assets. Report the two overlapping development sets separately, with per-category denominators and measured/skipped cases. Record source commit/dirty state, retrieval-code hash, frozen dataset/corpus/index identities, runtime/library versions and RRF configuration. Abort on retrieval/provenance failure without overwriting a previous complete artifact; completed gate failures remain valid diagnostics with nonzero exit status. Test through the real retriever interface using injected fakes and clocks. No new dependencies, Groq path, held-out execution or badge publication is added.
**Limits:** Source membership and retrieval quality do not prove semantic answer support. Recall presently has only two eligible provisional development cases; do not present its perfect score as broad evidence. Reserved cases remain author-visible and unexecuted. Full combined result/CI/publication contracts remain Increment 5. The user's waiver of teach-back answers does not waive human calibration or live-run budget approval.

---

### DRN-036: Frozen evaluation inputs and fail-closed embedding provenance

**Date:** 2026-11-04
**Context:** Phase 8's offline brief was approved. The legacy 45-question retrieval set is known development material, every public fact is still draft, and the existing embedding archive bound IDs to vectors without validating same-ID content changes.
**Choice:** Create 40 development cases and 10 newly authored held-out cases, grouped before tuning. Preserve provisional labels and draft facts. Freeze case/group/split hashes plus corpus/index snapshots; reject duplicate IDs, group/conversation overlap, copied legacy inquiries and unknown/nonpublic source labels. Default loading excludes held-out content; explicit reserved validation checks structure/provenance only. Separate all-relevant source sets from acceptable alternatives and semantic expectations from literal substring checks. Text fingerprints normalize Git CRLF/LF differences; the NPZ uses exact byte and matrix hashes.
**Index implementation:** Share artifact validation and embedding-input construction between builder/runtime. Rebuild vectors from cached local model assets, embedding corpus/input/model-asset/matrix fingerprints, FastEmbed version, UTC build time and source commit/dirty state in the archive. Production runtime rejects legacy/stale/corrupt artifacts instead of re-embedding the corpus, and uses local-only query model loading with asset fingerprint verification. Keep fake model injection. Isolate FastEmbed 0.9.1's private resolved-directory accessor in one helper. Move CI's previously implicit model-asset acquisition to an explicit setup step; no live Groq workflow is added. Pin the already-used PyYAML dependency.
**Trade-offs and limits:** A reserved set visible to its author is not an independently blind benchmark; paraphrase grouping still needs manual review. Hashes establish identity, not fact approval, semantic entailment or authenticity. Initial index provenance records `88fae8c` plus a dirty working tree, not a clean-commit accuracy run. Production concurrency/readiness/resource bounds and quota accounting remain separate work. No judge calibration, live result, public accuracy badge, new framework or database is introduced. Approval to start Phase 8 does not complete the pending remediation teach-back/tag.

---

### DRN-035: Requirement-local evidence and explicit failure/stream completion

**Date:** 2026-11-03
**Context:** Handoff review found cross-requirement citation acceptance, invented fallback requirements, unsupported preset narratives, colon/heartbeat conflation, silent premature EOF and nonserializable validator context.
**Choice:** Keep the fixed pipeline and existing stack. Validate evidence against a requirement-ID-to-retrieved-IDs map, with unique extracted IDs. Retain one extraction retry and then emit `extraction_error` without a report/cache entry. Preserve raw JSON-mode responses before parsing. Curated snapshots cite actual facts, use conservative narratives, compute scores through the scorer, and disclose manual provenance in the UI. Heartbeats use a distinct marker internally and SSE comments at both chat/fit transports. The shared frontend reader treats EOF before a valid terminal event as failure and owns reader cancellation/release. Validation responses omit exception context while retaining the 422 envelope/request ID.
**Alternatives:** Continue global citation checks and generic fallback requirements; recognize heartbeat strings by their prefix; silently accept EOF. Rejected because they produce misleading matches, lose valid text, or leave UI loading indefinitely.
**Limits:** Requirement-local membership establishes lineage, not semantic support. The snapshots are not independently calibrated evaluation ground truth. Draft approval, semantic judges, quota accounting, cache bypass/versioning and resource bounds remain tracked in PROGRESS.md. This record qualifies DRN-028's anti-overclaiming and authoritative-benchmark claims and DRN-026's stream lifecycle claims.

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

---

### DRN-020: Server-Supplied Generative UI via Function-Calling Seam

**Date:** 2026-11-02  
**Context:** Recruiters asking about projects should see structured, interactive technical cards with verified metrics, architecture flows, and repository links. If the LLM generates the JSON card directly in completion text, it could hallucinate metrics, fake repository URLs, or invent unsupported features.  
**Options:**  
A. Generative card schemas emitted directly by the LLM in markdown or JSON codeblocks  
B. Server-supplied generative UI: model triggers an abstract function call (`show_project_card(project_id)`), and the server supplies immutable `ProjectCardData` loaded directly from verified facts on disk  
**Choice:** B — Server-supplied generative UI via function-calling seam  
**Why:** Strictly enforces Design Principle 2: "The model selects, your server supplies. Cards and facts come from your data files, never from generated text, so the UI cannot hallucinate a project." The model only decides *which* project to present, while the verified facts, benchmark metrics, live URLs, and architectural blueprints are 100% authoritative and tamper-proof.

---

### DRN-021: Dual-Event SSE Stream Protocol for Citations and Cards

**Date:** 2026-11-02  
**Context:** Need to stream structured citations and generative UI card schemas alongside token-by-token prose over Server-Sent Events (SSE) via POST (`/api/chat/stream`).  
**Options:**  
A. Bundle all metadata into the terminal `done` event only  
B. Stream separate structured event frames (`event: sources`, `event: card`, `event: token`, `event: done`)  
**Choice:** B — Multi-event SSE stream protocol  
**Why:** Emits source receipts and interactive project cards immediately upon resolution before or alongside streaming tokens. Allows the frontend UI to display receipt chips and cards immediately without waiting for long token generation to finish, while keeping streaming text parsing clean and zero-overhead. Also includes sources and cards in `done` for robust client state reconciliation.

---

### DRN-022: Precomputed Dense Embeddings & Single-Thread ONNX Runtime for 512MB RAM Gate

**Date:** 2026-11-02  
**Context:** When testing live chat endpoints on Render's free tier (512 MB cgroup memory cap), the service was killed with an OOM error (`Ran out of memory (used over 512MB)`) resulting in frontend `Notice: Failed to fetch`. Profiling revealed that dynamic runtime embedding of all 75 facts spawned multi-core ONNX thread arenas, peaking at 1,229 MB of RAM. Additionally, FastEmbed downloaded ~130 MB of model weights from HuggingFace on the first live request within the HTTP request cycle.  
**Options:**  
A. Increase Render plan to paid 1GB/2GB tier  
B. Drop dense semantic retrieval and use BM25 only  
C. Precompute fact chunk embeddings offline (`facts_embeddings.npz`, 103 KB), enforce `threads=1` on ONNX Runtime (`TextEmbedding`), pre-warm index in FastAPI `lifespan`, and pre-cache model during Render `buildCommand`.  
**Choice:** C — Precomputed offline embeddings + single-threaded ONNX session + build-time model download  
**Why:**
1. **Memory:** Precomputed `.npz` loads in ~5ms using only ~3 MB RAM. At runtime, the server only embeds the single query string (1 sentence) using 1 ONNX thread, keeping peak process memory strictly at ~208 MB (<41% of Render's 512 MB cap, leaving >300 MB of headroom).
2. **Speed:** Eliminates the 12-second CPU freeze on boot/first-query. Retrieval latency stays at 16.39 ms average on CPU.
3. **Retrieval Quality Preserved:** Retains 100.0% Hit Rate@5 and 0.8778 MRR with zero accuracy degradation.
4. **Resilience:** Model download happens during Render build time; zero network downloads or unauthenticated HuggingFace requests occur inside HTTP request handling.

---

### DRN-023: Three-State Theme Engine (System / Light / Dark) with Pre-Hydration FOUC Prevention

**Date:** 2026-11-02  
**Context:** The minimal Phase 4 implementation only responded to `@media (prefers-color-scheme: dark)`. Recruiters evaluating the portfolio couldn't manually toggle themes, test both palettes, or override system defaults. Furthermore, client-side React theme state can cause a Flash of Unstyled Content (FOUC) if theme tokens are swapped after hydration.  
**Options:**  
A. Rely on an external React theming library (e.g. `next-themes` or custom Context provider)  
B. OS media query only without user override  
C. In-house CSS token bridge (`[data-theme="light"]`, `[data-theme="dark"]`, `@media (prefers-color-scheme: dark)`) paired with `useTheme` hook, local storage persistence, and a synchronous pre-hydration `<script>` in `index.html`.  
**Choice:** C — In-house CSS token bridge with pre-hydration script  
**Why:**
1. **Zero Runtime Overhead:** Theme switching occurs via CSS custom properties on `:root` without triggering React component tree re-renders or hydration waterfalls.
2. **Zero FOUC:** An inline vanilla script in `index.html` inspects `localStorage` and sets `data-theme` prior to DOM paint, completely eliminating visual flicker on cold reloads.
3. **Accessible Three-State Cycle:** Supports `system` (auto OS detection), `dark`, and `light` modes with clear `aria-label` indicators and keyboard navigability.

---

### DRN-024: Zero-Dependency Editorial Prose Formatter & Mobile Bottom-Sheet Ergonomics

**Date:** 2026-11-02  
**Context:** Assistant completions contain structured markdown formatting (code blocks, inline code, bold highlights, bullet lists, numbered sequences, blockquotes). Rendering raw text within a single `<p>` tag diminished technical authority, while pulling in heavy markdown libraries (e.g., `marked`, `react-markdown`, `remark`) would inflate bundle size and risk breaking our <200 KB gzipped budget. Furthermore, large architectural modals centered on mobile screens felt cramped and awkward.  
**Options:**  
A. Import `react-markdown` and syntax highlighter (~35–50 KB gzipped)  
B. Leave responses as plain unformatted whitespace pre-wrap  
C. In-house zero-dependency regex tokenizer (`FormattedMessage`) + mobile bottom-sheet modal drawer (`100dvh`).  
**Choice:** C — Zero-dependency tokenizer + mobile bottom-sheet modal  
**Why:**
1. **Bundle Budget Preserved:** Initial JS bundle remains featherweight at **77.35 KB gzipped** (well under the 200 KB ceiling). Zero external markdown or parsing dependencies.
2. **Editorial Typographic Scale:** Formats code blocks, quotes, lists, bold accents, and inline code with strict 72ch line-length constraints, high contrast, and smooth streaming cursor attachment.
3. **Mobile-First UX:** Automatically transforms the architectural inspection modal into a native-feeling bottom sheet on screens <= 640px while maintaining full keyboard trapping and Escape key dismissal on desktop.


---

### DRN-025: Bundled Instant Answers & SessionStorage Hydration for Zero-Latency Cold-Start UX

**Date:** 2026-11-02  
**Context:** Render's free tier spins down idle backend web services after 15 minutes of inactivity. When a recruiter opens the portfolio and clicks an initial prompt suggestion (e.g., "Who is Aamir?", "Tell me about his AI Engineer background"), the container spin-up takes 30–50 seconds. Waiting almost a minute on a first click degrades user trust and engagement. Additionally, refreshing the browser or navigating tabs wiped the active conversation history, frustrating recruiters conducting multi-turn explorations.  
**Options:**  
A. Display an indefinite loading spinner while the backend wakes up; do not persist chat across page reloads  
B. Keep the container warm 24/7 with an external cron service (violates zero-cost free-tier constraints)  
C. Client-side bundled instant answers for canonical starter prompts (`frontend/src/data/instantAnswers.ts`), paired with `sessionStorage` chat history persistence and a global `Ctrl+K` / `Cmd+K` keyboard shortcut.  
**Choice:** C — Bundled instant answers + `sessionStorage` conversation hydration + `Ctrl+K` hotkey  
**Why:**  
1. **0ms Perceived Latency:** Recruiters who click high-intent prompt chips receive immediate, authoritative dossier summaries and project previews instantly, without waiting for the server spin-up.
2. **Tab-Scoped History Persistence:** Using `sessionStorage` restores the conversation transcript seamlessly on browser reload while strictly scoping user chat data to the active tab session (cleared automatically on tab/window close, preserving visitor privacy).
3. **Power-User Ergonomics:** Registering a global `Ctrl+K` / `Cmd+K` listener focuses the chat input from anywhere in the document, matching modern developer-tool conventions.

---

### DRN-026: Zod Runtime Boundary Contracts & Non-Blocking SSE Heartbeats

**Date:** 2026-11-02  
**Context:** In a decoupled FastAPI + React architecture, TypeScript interfaces exist purely at compile-time and vanish after compilation. If backend response schemas drift or yield unexpected fields, the frontend can experience unhandled runtime exceptions. Furthermore, cloud reverse proxies (Render, Cloudflare, AWS ALB) aggressively terminate idle HTTP/1.1 and HTTP/2 streaming connections after 15–30 seconds of inactivity if no bytes are transferred (e.g. while the LLM engine queues or processes reasoning tokens).  
**Options:**  
A. Rely solely on static TypeScript types and let proxy timeouts trigger generic client-side fetch retries  
B. Use heavy WebSocket protocols with client-server ping/pong frames  
C. Zod runtime boundary validation on the frontend (`contracts.ts`) + FastAPI asynchronous SSE comment heartbeats (`: ping\n\n`) every 15 seconds during stream idle periods.  
**Choice:** C — Zod runtime boundary validation + non-blocking SSE comment heartbeats  
**Why:**  
1. **Fail-Safe Runtime Deserialization:** Zod schemas (`ChatSourcesEventSchema`, `ChatCardEventSchema`, `ChatTokenEventSchema`, `ChatDoneEventSchema`) validate every event frame arriving across the network. If malformed data arrives, safe fallbacks prevent entire application crashes.
2. **Proxy Keep-Alive Without Stream Pollution:** Per the W3C Server-Sent Events specification, lines starting with a colon (`:`) are comments and are ignored by compliant SSE parsers. Emitting `: ping\n\n` periodically keeps intermediate TCP sockets and Cloudflare reverse proxies alive without polluting user transcripts or client state.
3. **Contract Parity Test Suite:** Backed by `backend/tests/test_contracts.py` ensuring Pydantic models and frontend schemas remain strictly synchronized across commits.

---

### DRN-027: Protected In-Process Dev Retrieval Inspection Endpoint & Source URL Lineage

**Date:** 2026-11-02  
**Context:** Evaluating and tuning hybrid retrieval (BM25 + dense ONNX embeddings with Reciprocal Rank Fusion) requires deep visibility into chunk scores, rank fusion weights, and raw retrieved passages. Triggering a full chat completion for retrieval inspection wastes LLM tokens and adds latency. However, exposing internal retrieval endpoints in production could leak private drafting notes or unreleased project data. Furthermore, retrieved citations previously lacked canonical `source_url` metadata, leaving recruiters unable to click directly into Aamir's GitHub repositories or live project demos from source chips.  
**Options:**  
A. Log retrieval rankings to standard server stdout only  
B. Expose an unauthenticated public `/api/debug/retrieve` endpoint across all environments  
C. Mount a dedicated `GET /api/debug/retrieve` endpoint protected by environment guards (`ENVIRONMENT != "production"`, returning 404 in production), and enrich all 75 fact chunks with verified `source_url` metadata pointing to live repositories.  
**Choice:** C — Environment-guarded dev retrieval inspection endpoint + enriched `source_url` fact metadata  
**Why:**  
1. **Zero Production Attack Surface:** In production (`ENVIRONMENT=production`), the debug route is completely disabled and returns an immediate 404 Not Found response, preserving security and preventing reconnaissance.
2. **Fast Diagnostic & Eval Loop:** In development/staging, developers can instantly test queries against the full hybrid retrieval pipeline (`top_k`, reciprocal rank scores, chunk IDs) in sub-20ms without invoking the LLM.
3. **Verifiable Lineage:** Every source citation now links directly to verified GitHub repositories, papers, or project documentation, satisfying the core portfolio rule: "Every claim has a receipt."


---

### DRN-028: Fixed-Stage Pipeline vs. Free-Roaming Agent for JD Fit Evaluation

**Date:** 2026-11-02  
**Context:** When a recruiter pastes a job description to assess candidate fit, we could either give an LLM agent free-roaming search and tool-calling capabilities, or execute a deterministic, multi-stage pipeline. A free-roaming agent risks unpredictable execution times (15–60s), unbounded token consumption, looping, and hallucinations where the model overclaims candidate qualifications to sound helpful.  
**Options:**  
A. Autonomous tool-calling agent with retrieval loop  
B. Single-prompt stuffed evaluation (paste entire JD + all candidate facts into one prompt)  
C. Deterministic 5-stage pipeline: structured requirement extraction, per-requirement hybrid retrieval, batched LLM judging, deterministic anti-overclaiming invariant enforcement, and executive summary synthesis.  
**Choice:** C — Deterministic 5-stage pipeline  
**Why:**  
1. **Predictable Latency & Bounded Cost:** Extraction uses the lightweight utility model (`openai/gpt-oss-20b`) with structured JSON schema. Per-requirement hybrid retrieval runs concurrently across threads. Judging is batched into a single completion, keeping the entire pipeline within ~3–6 seconds.
2. **Anti-Overclaiming Invariant:** The judge cannot invent matches. If the model claims `strong` or `partial` alignment for a requirement but cites no valid retrieved evidence chunk ID, the deterministic scorer (`scorer.py`) automatically downgrades the verdict to `gap` and marks `downgraded = True`.
3. **Honest Ramp-Up Narratives:** Known gaps (Kubernetes, AWS/GCP, Kafka, C++, LangChain) are grounded in verified ramp-up narratives in `skills.yaml` (`skill-ramp-up-narratives`), turning potential rejection points into credible engineering growth narratives.
4. **Idempotent SHA-256 Caching:** Identical job descriptions produce an identical SHA-256 hash, returning cached evaluations in sub-10ms without consuming daily LLM quotas.
5. **Fit Rate Limiting:** A dedicated daily quota (`FIT_RATE_LIMIT_DAILY = 5` per client IP) protects Groq free-tier rate limits from automated abuse.
6. **Pre-Evaluated Golden Benchmarks for Curated Roles:** Rather than burning live Groq tokens or faking progress timers when recruiters click curated sample roles, 4 authoritative golden benchmark reports (`backend/app/fit/golden_benchmarks.py`) are pre-evaluated, SHA-256 matched, and pre-seeded directly into the pipeline cache and exposed over `GET /api/fit/presets`. In the UI, recruiters receive an instant snapshot labeled `[VERIFIED GOLDEN BENCHMARK (CACHED SNAPSHOT)]`, a collapsible `“📄 View Evaluated Job Description”` preview, and a `“🔄 Re-Run Live Pipeline”` button for complete transparency. Custom pasted JDs always invoke the live 5-stage SSE pipeline.


---

### DRN-029: Authoritative Contact Number Disclosure via Verified Profile Fact Chunk

**Date:** 2026-11-03  
**Context:** Aamir's phone number was previously withheld across the knowledge base and system prompts due to an overly restrictive initial questionnaire entry, despite the phone number already being publicly present on his résumé (`resume.tex`). As a result, recruiters asking for contact details to schedule calls or reach out via WhatsApp were unable to obtain his number.  
**Options:**  
A. Unconditionally inject the phone number into the global system prompt template (would risk leaking the phone number in unrelated responses)  
B. Keep the phone number permanently withheld, forcing recruiters to rely solely on email or LinkedIn  
C. Enrich the `profile-contact` fact chunk with the verified phone/WhatsApp number (`+91 8904816279`), update Rule 5 in `system.txt` to permit sharing contact channels when requested, and rely on hybrid retrieval isolation ($top\_k = 4$) so the chunk surfaces strictly when contact or interview scheduling is requested.  
**Choice:** C — Authoritative contact fact chunk enrichment + dynamic retrieval isolation  
**Why:**  
1. **Strict Context Isolation:** For non-contact inquiries (e.g. FastAPI, Entropy-OJ, education, algorithms), `profile-contact` does not rank in the top 4 chunks, so the phone number is physically absent from the LLM's prompt and cannot leak.
2. **Authoritative Grounding:** When a recruiter explicitly requests contact channels, a phone call, or WhatsApp, `profile-contact` ranks #1, allowing the assistant to share the phone number alongside email and LinkedIn with full receipt attribution.
3. **Résumé Parity:** Resolves an artificial discrepancy with `resume.tex` (Line 54: `+91 8904816279`), providing recruiters a direct path to schedule interviews.

---

### DRN-030: Multi-Turn Coreference Query Rewriting & Stateless History Passing

**Date:** 2026-11-03  
**Context:** The chat endpoints (`POST /api/chat` and `/api/chat/stream`) previously accepted only a single user message string without conversation history. Follow-up queries containing pronouns or elliptical phrasing (e.g., "what about entropy in one line", followed by "tell me more") broke down because: (1) BM25 and dense embedding search on "tell me more" retrieved irrelevant overview chunks, and (2) the LLM was given zero conversational history, leading it to ask for clarification as if starting a fresh conversation.  
**Options:**  
A. Server-side session store (Redis or database) tracking message history by `conversation_id`  
B. Client-side state passing full history without query rewriting (passing history directly to LLM without search rewriting)  
C. Stateless client-side rolling history passing + heuristic follow-up detection with fast utility model query rewriting  
**Choice:** C — Client-side rolling history passing + heuristic follow-up query rewriting  
**Why:**  
1. **Zero Database Dependencies:** Adheres to Phase 1 architecture principle "keep the server stateless". The client passes up to 10 recent turns (`history` field on `ChatRequest`). The server trims this to a rolling 4–6 turn window, keeping token usage strictly bounded.
2. **Retrieval Semantic Alignment:** Hybrid search algorithms (BM25 + vector dot products) fail on short follow-ups like "tell me more" or "what was its stack?". The rewriter uses a fast regex heuristic (`is_likely_follow_up`) to avoid unnecessary LLM calls on self-contained queries, only invoking the utility model (`openai/gpt-oss-20b`) when coreference resolution is genuinely needed.
3. **Graceful Degraded Execution:** If the query rewriter times out or fails, the pipeline immediately falls back to the raw query without throwing 500 errors to the recruiter.

---

### DRN-031: Tokenizer Normalization & Markdown Formatting Invariants for Open-Weight Models

**Date:** 2026-11-03  
**Context:** When asked for contact details, `openai/gpt-oss-120b` occasionally emitted Unicode `\u202f` (Narrow No-Break Space) instead of colons and spaces, left bold tags unclosed (e.g., `- **Email aamirmkh25...`), or stripped protocol prefixes from URLs (e.g., `https.linkedin...`). Hand-crafted frontend markdown parsers (`FormattedMessage.tsx`) expecting standard markdown delimiters rendered these as raw unformatted strings.  
**Options:**  
A. Rely exclusively on system prompt instructions to fix model behavior  
B. Pull in a heavyweight third-party markdown library (e.g., `marked` or `react-markdown` with plugins)  
C. Defense-in-depth: explicit system prompt Rule 9 formatting invariants + backend token normalizer + frontend regex repair layer for non-standard whitespace, unclosed bold list tags, and URL protocol restoration.  
**Choice:** C — Multi-layer defense-in-depth formatting hardening  
**Why:**  
1. **Open-Weight Tokenizer Resilience:** Models trained on multilingual corpora frequently emit narrow non-breaking spaces before punctuation or numbers. Normalizing `\u202f`, `\u00a0`, and `\u200b` at the LLM adapter boundary (`normalize_llm_text` in `app.llm`) eliminates invisible whitespace corruptions across both streaming and complete calls.
2. **Resilient Parsing:** The frontend markdown tokenizer repairs unclosed bold tags on standard contact bullets and restores missing `https://` protocol prefixes, ensuring links remain clickable even if the upstream LLM drops punctuation.
3. **Zero Bundle Budget Impact:** Adding regex repairs in `FormattedMessage.tsx` adds 0 external dependencies, preserving the 112.90 KB gzipped bundle budget.

---

### DRN-032: Dossier View State Decoupling from Transcript Lifecycle

**Date:** 2026-11-03  
**Context:** In Phase 4, the Editorial Dossier UI used a shortcut where the landing hero view was defined as `isCoverState = messages.length === 0`. Navigating back to the dossier overview via `← Dossier Overview` called `resetChat()`, erasing the user's entire conversation transcript and clearing `sessionStorage`. Recruiters navigating back to check credentials lost their active multi-turn session.  
**Options:**  
A. Keep `resetChat()` as the return mechanism (forces recruiters to start over)  
B. Separate view routing (`viewMode: "cover" | "chat"`) from transcript data, adding a non-destructive navigation button and a "Resume Chat (N) →" entry point.  
**Choice:** B — View state decoupling with non-destructive navigation and resume entry points  
**Why:**  
1. **Preserved Recruiter Context:** Recruiters can freely navigate between reading the candidate dossier and conducting exploratory chat without losing their transcript.
2. **Clear User Intent:** Decouples navigation (`← Dossier Overview` sets `viewMode = "cover"`) from destructive action (`Clear Chat` explicitly wipes state and resets `sessionStorage`).
3. **Session Continuity:** If a recruiter returns to the Dossier Overview while a conversation exists, a prominent `Resume Chat (N) →` pill appears in the header, making context switching effortless.

---

### DRN-033: React Markdown AST Migration for Robustness & Anti-Regression

**Date:** 2026-11-03  
**Context:** In DRN-024, an in-house zero-dependency regex tokenizer (`FormattedMessage.tsx`) was chosen to parse markdown. However, Markdown is not a regular language. Over time, attempts to patch tokenizer edge cases (e.g. unclosed bullet bolding, loose lists with double newlines, nested asterisks, table line breaks) caused brittle regex interactions:
1. Regex replacements matching words inside bullet items inadvertently matched legitimate terms like `- **Availability**:` and `- **Work Focus**:`, mutating them into `Availabilit: y**` and `Work: Focus**`.
2. A single orphaned asterisk on `- **Location Preference**:` paired with subsequent bold text on the same line, corrupting `**Bengaluru, India**`.
3. Block list parsing broke on empty lines between items in loose lists, creating separate `<ol>` blocks that each restarted numbering at `1.`.
4. Glued numerals emitted by LLMs (`...are1. **AI-Assisted...`) were parsed as raw paragraph text rather than list items.
Meanwhile, copying response text succeeded because the raw LLM markdown was valid, proving the issue was strictly frontend parser brittleness.

**Options:**  
A. Continue patching the 630-line hand-rolled regex tokenizer  
B. Adopt the battle-tested `react-markdown` + `remark-gfm` ecosystem with custom component overrides matching existing design tokens  

**Choice:** B — Adopt `react-markdown` + `remark-gfm`  
**Why:**  
1. **Zero Regex Fragility:** Replaced 727 lines of fragile ad-hoc regexes with a declarative ~140-line component. Tables, loose lists, nested emphasis, code blocks, blockquotes, and link autolinking are handled by standard CommonMark/GFM AST parsers.
2. **Safe Loose Lists & Start Numbering:** Ordered lists with blank lines remain a single unified `<ol>`, and starting offsets (`<ol start={N}>`) are respected automatically.
3. **Bundle Budget Compliant:** Initial JS bundle increased from 112.92 KB to 162.88 KB gzipped, safely below the 200 KB gzipped ceiling (leaving 37.12 KB of headroom). Avoided heavy HTML parsers like `rehype-raw`/`parse5` by handling line breaks (`<br>`) via lightweight child processing.
4. **Backend Invariant Reinforcement:** Reinforced LLM output formatting in `system.txt` (requiring lists to start on newlines with preceding blank lines) and added regex normalization for glued numerals (`are1. ` -> `are\n\n1. `) in `normalize_llm_text`.


---

### DRN-034: Protocol Safe Normalization, Non-Destructive Formatting, and Session Storage Purge

**Date:** 2026-11-03  
**Context:** Following the adoption of `react-markdown` in DRN-033, user testing revealed edge-case formatting defects:
1. **Multi-segment domain truncation:** A legacy regex in `sanitizeMarkdown()` attempting to normalize bare domains only matched single-label domains followed by a hardcoded list of TLDs (`[a-zA-Z0-9-]+\.(?:com|org|io|dev|app|edu|in|net)`). On two-dot domains (`entropy-oj.vercel.app`, `health-prem-prediction.streamlit.app`), the regex failed to match across the first dot, truncating domain prefixes and generating corrupted URLs like `<https-oj.vercel.app>`.
2. **Double URL / relative link resolution:** When the model emitted `<httpsamirmk-portfolio.vercel.app>` without `://`, `ReactMarkdown` generated an `<a href="httpsamirmk-portfolio.vercel.app">`. Because the browser treats any URL lacking an absolute protocol scheme (`http://`, `https://`, `mailto:`) as a relative path to the current origin, clicking the link navigated to `https://aamirmk-portfolio.vercel.app/httpsamirmk-portfolio.vercel.app`.
3. **Session history poisoning:** When corrupted assistant outputs were emitted during earlier testing, `sessionStorage` stored them under `amk_portfolio_chat_session`. In subsequent turns, `useChat.ts` sent the last 6 messages in the `history` payload. In-context learning caused Groq (`openai/gpt-oss-120b`) to mirror the malformed syntax (omitted colons, missing bullets) in new answers.
4. **Negative prompt constraint activation:** The system prompt explicitly instructed the model: *"Never produce malformed links like `https.domain`"*. Mentioning negative token patterns activated attention weights on those exact sequences (the "pink elephant" effect), occasionally triggering the model to emit the pattern.

**Choice:**
1. **Extract `formatHelpers.ts` with Non-Destructive Sanitization:**
   - Completely removed destructive URL rewriting regexes from text pre-processing.
   - Limited `sanitizeMarkdown()` to safe Unicode normalization (`\u202f`, `\u00a0`, `\u200b` $\to$ space, `\u2011` $\to$ hyphen), glued numeral separation, and harmless closing of unclosed bold contact headers if missing closing `**`.
2. **Enforce Absolute URLs in `formatSafeHref()`:**
   - In `markdownComponents.a`, inspect every `href`. If a link lacks a protocol, normalize typos (e.g. `https.domain` or `httpsaamirmk...`) and prepend `https://` (or `mailto:` if an email). External links are guaranteed never to resolve relative to the portfolio root.
3. **Purge Poisoned Transcripts via Session Storage v2:**
   - Bumped `CHAT_SESSION_STORAGE_KEY` to `amk_portfolio_chat_session_v2` and explicitly purged legacy v1 transcripts on startup.
4. **Prescriptive Positive Invariants in `system.txt`:**
   - Replaced negative constraint warnings with positive, canonical markdown examples.
5. **Backend Normalization:**
   - Added non-breaking hyphen `\u2011` $\to$ `-` normalization in `backend/app/llm.py` `normalize_llm_text()`.

**Consequences:**
- Zero domain truncation or relative path resolution regressions.
- Bundle size remains 162.94 kB gzipped (<200 kB budget).
- All 125 frontend Vitest tests and 239 backend Pytest tests pass cleanly.

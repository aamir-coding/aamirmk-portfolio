# Progress Tracker

## Current Phase
**Band 2 / Phase 4: Design System (Full) & Editorial Dossier Direction** — 🟢 Complete. Delivered three-state theme engine (system/light/dark), zero-dependency markdown prose formatter, expanded candidate credentials ribbon, copy response control, and mobile bottom-sheet modal ergonomics. Next: Phase 6 (JD Fit Report).

## Live Deployments
- **Backend (Render)**: `https://aamirmk-portfolio-mlr4.onrender.com/api/health`
- **Frontend (Vercel)**: `https://aamirmk-portfolio.vercel.app/`

## Phase Status

| Phase | Status | Branch | Tag | Study Guide |
|-------|--------|--------|-----|-------------|
| Setup | 🟢 Complete | `main` | — | — |
| P0: Skeleton | 🟢 Complete | `main` | `phase-0-done` | [`phase-00-foundations.md`](study-guides/phase-00-foundations.md) |
| P1: Chat endpoint | 🟢 Complete | `main` | `phase-1-done` | [`phase-01-fastapi-chat.md`](study-guides/phase-01-fastapi-chat.md) |
| P3: Streaming + UI | 🟢 Complete | `main` | `phase-3-done` | [`phase-03-streaming-ui.md`](study-guides/phase-03-streaming-ui.md) |
| P4: Design system (minimal) | 🟢 Complete | `main` | `phase-4-done` | [`phase-04-design-system.md`](study-guides/phase-04-design-system.md) |
| P7: Safety (first-share) | 🟢 Complete | `main` | `phase-7-done` | [`phase-07-safety-rate-limiting.md`](study-guides/phase-07-safety-rate-limiting.md) |
| — Gate 1: Shareable link — | 🟢 Complete | `main` | `gate-1-done` | — |
| P2: RAG | 🟢 Complete | `main` | `phase-2-done` | [`phase-02-hybrid-rag.md`](study-guides/phase-02-hybrid-rag.md) |
| P5: Citations + gen UI | 🟢 Complete | `main` | `phase-5-done` | [`phase-05-citations-generative-ui.md`](study-guides/phase-05-citations-generative-ui.md) |
| P4: Design system (full) | 🟢 Complete | `main` | `phase-4-editorial-done` | [`phase-04-design-system.md`](study-guides/phase-04-design-system.md) |
| P6: Fit report | ⬜ Next Up (Band 3) | — | — | — |
| P8: Evals | ⬜ Not Started | — | — | — |
| P7: Safety (rest) | ⬜ Not Started | — | — | — |
| P10: Production | ⬜ Not Started | — | — | — |
| P9: Handoff + analytics | ⬜ Not Started | — | — | — |

## What's Done
- [x] Implementation plan read and understood
- [x] Setup briefing delivered and decisions made
- [x] Assistant voice: third person
- [x] Model: `openai/gpt-oss-120b` (main) + `openai/gpt-oss-20b` (utility)
- [x] Postgres: Supabase (deferred to Phase 9)
- [x] Git repo initialized and initial commit on main
- [x] Branch `phase-0-skeleton` created and merged via PR #1 to `main`
- [x] Backend FastAPI app with `GET /api/health`, settings, CORS, request ID middleware
- [x] Backend test suite with 10 passing pytest tests
- [x] Frontend React + TypeScript SPA scaffold with health client
- [x] Frontend test suite with 7 passing Vitest tests
- [x] GitHub Actions CI pipeline (.github/workflows/ci.yml) tested and passing in cloud
- [x] Backend deployed live on Render free web service
- [x] Frontend deployed live on Vercel Hobby
- [x] Live CORS verification: Vercel origin accepted, unlisted origin rejected
- [x] Warm response time measured (~530ms)
- [x] Cold-start time measured: 4 runs recorded — 23.1s, 32.9s, 22.7s, 22.4s (avg ~25s, peak ~33s)
- [x] Teach-back completed and verified
- [x] Tag `phase-0-done` created and pushed to origin
- [x] Study guide written: `docs/study-guides/phase-00-foundations.md`
- [x] AGENTS.md updated with explicit skill usage rules and session kickoff protocol
- [x] Phase 1: `groq==1.7.0` pinned in requirements and installed
- [x] Phase 1: Async LLM adapter `app/llm.py` with `LLMClient` protocol and `FakeLLM`
- [x] Phase 1: System prompt with context-stuffed résumé markdown (phone number excluded)
- [x] Phase 1: Strict Pydantic models `ChatRequest` and `ChatResponse` with input trimming
- [x] Phase 1: `POST /api/chat` route mounted with `Depends(get_llm_client)`
- [x] Phase 1: Error translation for rate limits (429), auth (500), upstream unavailable (503)
- [x] Phase 1: 40 backend pytest tests passing in 0.42s (all using fake LLM, 0 API cost)
- [x] Phase 1: 7 frontend vitest tests passing
- [x] Phase 1: Real Groq live smoke test verified against `openai/gpt-oss-120b` (1.53s latency, 1,381 prompt tokens)
- [x] Phase 1: Architectural decisions DRN-008 and DRN-009 recorded in `docs/decisions.md`
- [x] Phase 1: Study guide written in `docs/study-guides/phase-01-fastapi-chat.md`
- [x] Phase 3: Extended `LLMClient` protocol with `stream(messages) -> AsyncIterator[str]`
- [x] Phase 3: Implemented `GroqLLM.stream()` with `AsyncGroq(stream=True)` and `FakeLLM.stream()` token slicing
- [x] Phase 3: Mounted `POST /api/chat/stream` SSE endpoint with Starlette `StreamingResponse` and event framing (`token`, `done`, `error`)
- [x] Phase 3: Built zero-dependency `streamChat` client in `frontend/src/lib/sse.ts` over `fetch` + `ReadableStream` reader with packet chunk accumulator
- [x] Phase 3: Built `useChat` hook managing message states, active token appending, and `AbortController` cancellation
- [x] Phase 3: Created accessible chat interface components: `MessageList`, `MessageItem` (memoized with `React.memo`), `ChatInput` with multi-line support, and `StarterChips`
- [x] Phase 3: Added Render free-tier cold-start UX: optimistic background health check with >2.5s latency warning and status pill
- [x] Phase 3: Verified bundle budget: initial JS is 73.16 KB gzipped (<200 KB budget), CSS is 2.00 KB gzipped
- [x] Phase 3: 52 backend pytest tests passing with 0 API cost
- [x] Phase 3: 22 frontend vitest tests passing
- [x] Phase 3: Live Groq streaming smoke test against `openai/gpt-oss-120b` verified: 0.58s TTFT, 0.61s total duration
- [x] Phase 3: Architectural decisions DRN-010, DRN-011, and DRN-012 recorded in `docs/decisions.md`
- [x] Phase 3: Comprehensive study guide written in `docs/study-guides/phase-03-streaming-ui.md`
- [x] Phase 3: Fixed trailing slash bug on baseUrl and normalized consecutive slashes via ASGI middleware
- [x] Phase 3: CI 100% green on GitHub Actions with ruff format check and all test suites
- [x] Phase 3: Verified end-to-end on live Vercel frontend and live Render backend
- [x] Added 2 new skills to repository: `agent-browser` and `diagnosing-bugs` (8 skills total)
- [x] Phase 4: In-house CSS design tokens architecture (`tokens.css`) with light/dark theme variables
- [x] Phase 4: Distinctive Editorial Dossier visual direction (ink/paper, hairline borders, restrained cobalt)
- [x] Phase 4: `CoverState` hero landing view with verified credentials, identity, and competency cards
- [x] Phase 4: Smooth Cover-to-Chat transition state machine with "← Dossier Overview" reset capability
- [x] Phase 4: Polished message transcripts with monospace role badges (`INQUIRY` / `DISPATCH`) and streaming cursor
- [x] Phase 4: Mobile-first responsive hardening with `100dvh` dynamic viewports, safe area insets, and iOS zoom prevention
- [x] Phase 4: Bundle budget verified: 73.74 KB gzipped JS (<200 KB budget), 3.30 KB gzipped CSS
- [x] Phase 4: 26 frontend Vitest tests and 52 backend Pytest tests 100% green
- [x] Phase 4: Architectural decisions DRN-013 and DRN-014 recorded in `docs/decisions.md`
- [x] Phase 4: Comprehensive study guide written in `docs/study-guides/phase-04-design-system.md`
- [x] Phase 7: Reverse-proxy-aware client IP extraction (`app.safety.ip`) with anti-spoofing and IPv4/IPv6 validation
- [x] Phase 7: In-memory sliding-window rate limiter (`app.safety.rate_limiter`) enforcing 10 req/min with automatic stale eviction
- [x] Phase 7: Standard RFC rate limit response headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `Retry-After`)
- [x] Phase 7: Global daily quota guard (`app.safety.quota`) tracking 800 RPD / 180,000 TPD with UTC midnight calendar rollover
- [x] Phase 7: Pre-call prompt injection regex guardrails (`app.safety.guardrails`) rejecting attacks at 0 LLM token cost with zero false positives on legitimate queries
- [x] Phase 7: Delimiter XML boundary hardening (`<user_inquiry>`) in `system.txt` isolating instructions from user query data
- [x] Phase 7: Integrated safety dependencies across `POST /api/chat` and `POST /api/chat/stream`
- [x] Phase 7: Frontend chat error handling for 429 rate limit and daily quota exhaustion
- [x] Phase 7: 104 backend Pytest tests (100% green, 0 API cost) and 27 frontend Vitest tests (100% green)
- [x] Phase 7: Architectural decisions DRN-015, DRN-016, and DRN-017 recorded in `docs/decisions.md`
- [x] Phase 7: Comprehensive study guide written in `docs/study-guides/phase-07-safety-rate-limiting.md`
- [x] Phase 2: Curated 75 verified fact chunks across 9 categories + 1 boundary policy from answered questionnaire
- [x] Phase 2: Built `FactChunk` and `RetrievedChunk` Pydantic v2 models and `FactLoader` with frontmatter parsing
- [x] Phase 2: Documented 17 knowledge gaps/unverified metrics in `docs/knowledge-todo.md`
- [x] Phase 2: Implemented in-house Okapi BM25 index with Robertson-Spärck Jones non-negative IDF and technical compound tokenization
- [x] Phase 2: Integrated FastEmbed ONNX runtime with `BAAI/bge-small-en-v1.5` (~130MB ONNX, 384 dimensions) and NumPy cosine dot products
- [x] Phase 2: Passed Memory Gate in 512MB container simulation (227.75 MB total WorkingSet, >284 MB headroom)
- [x] Phase 2: Implemented Cormack's Reciprocal Rank Fusion ($k=60$) combining BM25 and dense results off-thread via `asyncio.to_thread`
- [x] Phase 2: Built `@runtime_checkable` `Retriever` protocol with `FakeRetriever` and FastAPI dependency injection (`get_retriever`)
- [x] Phase 2: Dynamic system prompt context augmentation in `POST /api/chat` and `POST /api/chat/stream` (`top_k=4`) preserving guardrails and quota
- [x] Phase 2: Built automated retrieval eval suite `evals/test_retrieval.py` against 45 labeled queries from `evals/seed_questions.yaml`
- [x] Phase 2: Hit Rate@5: 100.00% (45/45 queries, target >= 90%)
- [x] Phase 2: MRR: 0.8778 (target >= 0.8000)
- [x] Phase 2: CPU Retrieval Latency: 9.39 ms average, p95 11.01 ms (target < 25 ms)
- [x] Phase 2: Total test suite: 175 tests passed (127 backend + 48 evals, 100% green, 0 API cost)
- [x] Phase 2: Architectural decisions DRN-018 and DRN-019 recorded in `docs/decisions.md`
- [x] Phase 2: Comprehensive study guide written in `docs/study-guides/phase-02-hybrid-rag.md`
- [x] Phase 5: Created `SourceCitation` and `ProjectCardData` Pydantic models with frozen immutability
- [x] Phase 5: Built `ToolRegistry` protocol seam and authoritative catalog of 8 projects in `app/tools/`
- [x] Phase 5: Extended `LLMClient` protocol with function-calling support in `GroqLLM` and `FakeLLM`
- [x] Phase 5: Multi-event SSE streaming protocol (`event: sources`, `event: card`, `event: token`, `event: done`)
- [x] Phase 5: Built accessible `SourceChips` with section badges (`[J1]`, `[X7]`) and external receipt anchors
- [x] Phase 5: Built editorial `ProjectCard` and accessible architectural `ProjectModal` (focus trap, Esc listener, ARIA)
- [x] Phase 5: Preserved bundle budget: JS is 75.50 KB gzipped (<200 KB budget), CSS is 4.28 KB gzipped
- [x] Phase 5: Full test suite passing: 188 backend/eval tests (100% green) + 44 frontend Vitest tests (100% green)
- [x] Phase 5: Verified real Groq tool dispatch against `openai/gpt-oss-120b` (0.96s non-streaming, 0.66s streaming)
- [x] Phase 5: Architectural decisions DRN-020 and DRN-021 recorded in `docs/decisions.md`
- [x] Phase 5: Comprehensive study guide written in `docs/study-guides/phase-05-citations-generative-ui.md`
- [x] Phase 4 (Full): Three-state theme engine (`system`, `light`, `dark`) with synchronous pre-hydration FOUC elimination in `index.html`
- [x] Phase 4 (Full): Accessible `ThemeToggle` component with resolved OS preference indicator
- [x] Phase 4 (Full): Hand-built zero-dependency markdown prose formatter `FormattedMessage` for bold, code, links, bullet/numbered lists, quotes, and code blocks
- [x] Phase 4 (Full): Expanded `CoverState` hero with verified candidate credentials ribbon (AMU B.Tech 9.77 CGPA, Aligarh, Available for Hire) and external touchpoints (GitHub, LinkedIn, Email)
- [x] Phase 4 (Full): One-click response copy button on assistant messages with accessible live feedback ("Copied ✓")
- [x] Phase 4 (Full): Tactile micro-interactions (`-1px` lifts, hairline transitions) on cards, starter chips, and external links
- [x] Phase 4 (Full): Mobile-first `100dvh` hardening with bottom-sheet modal drawer on screens <= 640px and safe-area inset protection
- [x] Phase 4 (Full): Production bundle budget strictly maintained: JS is 77.35 KB gzipped (<200 KB budget), CSS is 5.04 KB gzipped
- [x] Phase 4 (Full): 64 frontend Vitest tests and 190 backend Pytest tests 100% green
- [x] Phase 4 (Full): Architectural decisions DRN-023 and DRN-024 recorded in `docs/decisions.md`
- [x] Phase 4 (Full): Comprehensive study guide expanded in `docs/study-guides/phase-04-design-system.md`

## Measured Cold-Start Benchmarks (Render Free Tier)
- **Idle Timeout**: 15 minutes
- **Run 1**: 23.15s
- **Run 2 (Peak 19:30 IST)**: 32.93s
- **Run 3**: 22.71s
- **Run 4**: 22.39s
- **Baseline for Phase 3 UX**: 25s average, 35s max timeout allowance.

## Next Step
1. Present Phase 4 teach-back to Aamir with 3 mental model verification questions.
2. Obtain approval, merge `phase-4-editorial-dossier` to `main`, tag `phase-4-editorial-done`, and push to remote.
3. Prepare brief for Band 3 / Phase 6 (JD Fit Report).

## Resolved
- [x] Python 3.13.17 installed and on PATH ✅
- [x] Groq limits confirmed (see below) ✅
- [x] GitHub Actions enabled ✅
- [x] Implementation plan copied to docs/ ✅
- [x] .env.example created ✅
- [x] Initial commit done ✅

## Groq Rate Limits (authoritative, from user's Limits page)

| Model | RPM | RPD | TPM | TPD |
|-------|-----|-----|-----|-----|
| `openai/gpt-oss-120b` | 30 | 1,000 | 8,000 | 200,000 |
| `openai/gpt-oss-20b` | 30 | 1,000 | 8,000 | 200,000 |

Both models share the same limits. The 20b model is cheaper for utility calls.

## Open Questions
1. **Phone number**: resume.tex contains a phone number. Excluded from knowledge base per hard rules unless user approves.
2. **Local Postgres 18**: User has Postgres 18 installed locally. Could use for local dev instead of SQLite, but DB not needed until Phase 9.

## Blockers
None.

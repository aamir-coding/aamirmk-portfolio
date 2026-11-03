# Progress Tracker

## Current Phase
**Phase 6: Job Description Fit Report** — 🟢 Complete. Fixed 5-stage verification pipeline, structured extraction, per-requirement hybrid retrieval, batched alignment judging, deterministic anti-overclaiming invariant enforcement, honest ramp-up narratives (`skills.yaml`), SSE progress streaming (`POST /api/fit`), presets endpoint (`GET /api/fit/presets`), fit rate limiter (5 reports/day/IP), SHA-256 caching, frontend `FitReportModal`, `FitReportCard`, `FitProgressStepper`, and bidirectional gap bridge to chat.

Next: Band 3 / Phase 8 (Evals).

## Live Deployments
- **Backend (Render)**: `https://aamirmk-portfolio-mlr4.onrender.com/api/health`
- **Frontend (Vercel)**: `https://aamirmk-portfolio.vercel.app/`

## Phase Status

| Phase | Status | Branch | Tag | Study Guide |
|---|---|---|---|---|
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
| **Bands 1 & 2 Parity Backfill** | 🟢 Complete | `main` | `backfill-parity-done` | [`phase-parity-backfill.md`](study-guides/phase-parity-backfill.md) |
| **P6: Fit report** | 🟢 Complete | `main` | `phase-6-done` | [`phase-06-jd-fit-report.md`](study-guides/phase-06-jd-fit-report.md) |
| **Quality & Multi-Turn Hardening** | 🟢 Complete | `main` | `quality-hardening-done` | [`quality-and-multi-turn-hardening.md`](study-guides/quality-and-multi-turn-hardening.md) |
| P8: Evals | ⬜ Next Up (Band 3) | — | — | — |
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
- [x] Phase 4 (Full): Hardened markdown table UX/UI with dynamic '#' compact column shrink-wrapping (40px), natural header text wrapping, and mobile horizontal scrolling
- [x] Phase 4 (Full): Full inline tokenizer parsing for `<br>` line breaks in table cells, bold-italic, safe HTML tags (`<b>`, `<i>`, `<code>`, `<del>`), and footnote italics
- [x] **Parity Backfill (P3)**: Bundled verified `answers.json` for 0ms instant cold-start responses before backend wakes
- [x] **Parity Backfill (P3)**: Added `sessionStorage` chat history persistence and global `Ctrl/Cmd+K` keyboard shortcut
- [x] **Parity Backfill (P3)**: Added Zod boundary contract validation (`contracts.ts`) and contract test suite
- [x] **Parity Backfill (P3)**: Added periodic 15s SSE comment keep-alive heartbeat (`: heartbeat\n\n`) during slow upstream waits
- [x] **Parity Backfill (P2)**: Enriched fact chunks with verified `source_url` receipts and recomputed `.npz` embeddings matrix
- [x] **Parity Backfill (P2)**: Mounted dev inspection endpoint `GET /api/debug/retrieve?q=` (protected in production)
- [x] **Parity Backfill (P7)**: Expanded adversarial attack suite to 23 payloads and added production security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, and CSP)
- [x] **Parity Backfill (P4 Full)**: Added Open Graph social metadata, custom monograph SVG favicon, and static `<noscript>` fallback
- [x] **Phase 6**: Strict Pydantic models in `backend/app/fit/models.py` (`FitRequest`, `Requirement`, `JudgedRequirement`, `FitScoreSummary`, `FitReport`)
- [x] **Phase 6**: Deterministic anti-overclaiming invariant scorer in `backend/app/fit/scorer.py` (`validate_and_downgrade_verdicts` and `compute_fit_summary`)
- [x] **Phase 6**: Enriched `skills.yaml` with verified gap ramp-up narratives (`skill-ramp-up-narratives` chunk covering Kubernetes, AWS/GCP, Kafka, C++, LangChain)
- [x] **Phase 6**: Regenerated `backend/app/retrieval/facts_embeddings.npz` (104.5 KB, covering 76 chunks)
- [x] **Phase 6**: Curated 4 realistic market sample JDs in `evals/sample_jds/` with preset loader `backend/app/fit/sample_jds.py`
- [x] **Phase 6**: Implemented `FitPipeline` deep module (`backend/app/fit/pipeline.py`) with utility model extraction, concurrent hybrid retrieval pool, batched judging, and SHA-256 caching
- [x] **Phase 6**: Extended `LLMClient` protocol (`backend/app/llm.py`) with `model` override and `response_format={"type": "json_object"}`
- [x] **Phase 6**: Mounted `POST /api/fit` SSE streaming and `GET /api/fit/presets` in `backend/app/api/fit.py`
- [x] **Phase 6**: Added daily IP fit rate limiter (`FIT_RATE_LIMIT_DAILY = 5`) in `backend/app/safety/rate_limiter.py`
- [x] **Phase 6**: Added Zod boundary contracts (`FitReportSchema`, `FitProgressDataSchema`, `SampleJobDescriptionSchema`) in `frontend/src/lib/contracts.ts`
- [x] **Phase 6**: Added typed SSE streaming client `streamFitReport()` in `frontend/src/lib/sse.ts` and `fetchFitPresets()` in `frontend/src/lib/api.ts`
- [x] **Phase 6**: Built `useFitReport` hook (`frontend/src/hooks/useFitReport.ts`) managing multi-step streaming lifecycle and abort controllers
- [x] **Phase 6**: Built accessible UI components: `FitProgressStepper`, `FitReportCard`, `FitReportModal`, and entry points in `CoverState`, `StarterChips`, and header
- [x] **Phase 6**: Verified bundle budget: 112.17 KB gzipped JS (<200 KB budget), 7.54 KB gzipped CSS
- [x] **Phase 6**: Full test suite passing: 226 backend tests (178 unit + 48 evals, 100% green, 0 API cost) + 115 frontend Vitest tests (100% green)
- [x] **Phase 6**: Added pre-evaluated golden benchmarks (`backend/app/fit/golden_benchmarks.py`) pre-seeding pipeline cache and `GET /api/fit/presets` with instant preview, match expectation badges, collapsible JD preview, and live re-run capability
- [x] **Phase 6**: Architectural decision DRN-028 recorded in `docs/decisions.md`
- [x] **Phase 6**: Comprehensive study guide written in `docs/study-guides/phase-06-jd-fit-report.md`
- [x] **Quality & Multi-Turn Hardening**: Extended `ChatRequest` schema with rolling `history` (`ChatHistoryMessage`)
- [x] **Quality & Multi-Turn Hardening**: Follow-up query rewriter (`backend/app/retrieval/rewriter.py`) resolving coreferences before hybrid retrieval
- [x] **Quality & Multi-Turn Hardening**: Rolling conversation context passed to Groq completion and streaming endpoints
- [x] **Quality & Multi-Turn Hardening**: Enforced Rule 9 in `system.txt` for strict URL, bold, and list formatting
- [x] **Quality & Multi-Turn Hardening**: Added `normalize_llm_text` in `backend/app/llm.py` and frontend regex repairs in `FormattedMessage.tsx` handling `\u202f`, unclosed bold tags, and URL protocol restoration
- [x] **Quality & Multi-Turn Hardening**: Decoupled Dossier Overview navigation (`viewMode: "cover" | "chat"`) from transcript reset; added `Resume Chat (N) →` entry point and explicit `Clear Chat` action
- [x] **Quality & Multi-Turn Hardening**: Full test suite passing: 237 backend tests (189 unit + 48 evals, 100% green, 0 API cost) + 119 frontend Vitest tests (100% green, 112.90 KB gzipped JS)
- [x] **Quality & Multi-Turn Hardening**: Architectural decisions DRN-030, DRN-031, and DRN-032 recorded in `docs/decisions.md`
- [x] **Quality & Multi-Turn Hardening**: Comprehensive study guide written in `docs/study-guides/quality-and-multi-turn-hardening.md`

## Measured Cold-Start Benchmarks (Render Free Tier)
- **Idle Timeout**: 15 minutes
- **Run 1**: 23.15s
- **Run 2 (Peak 19:30 IST)**: 32.93s
- **Run 3**: 22.71s
- **Run 4**: 22.39s
- **Baseline for Phase 3 UX**: 25s average, 35s max timeout allowance.

## Next Step
1. Deliver Phase 6 interactive teach-back with 3 questions to verify user's mental model per protocol.
2. Tag `phase-6-done` and push branch `phase-6-jd-fit-report` to remote.
3. Stop and await user's explicit "approved" before moving to Band 3 / Phase 8.

## Resolved
- [x] Python 3.13.17 installed and on PATH ✅
- [x] Groq limits confirmed (see below) ✅
- [x] GitHub Actions enabled ✅
- [x] Implementation plan copied to docs/ ✅
- [x] .env.example created ✅
- [x] Initial commit done ✅

## Groq Rate Limits (authoritative, from user's Limits page)

| Model | RPM | RPD | TPM | TPD |
|---|---|---|---|---|
| `openai/gpt-oss-120b` | 30 | 1,000 | 8,000 | 200,000 |
| `openai/gpt-oss-20b` | 30 | 1,000 | 8,000 | 200,000 |

Both models share the same limits. The 20b model is cheaper for utility calls.

## Open Questions
1. **Phone number**: resume.tex contains a phone number. Excluded from knowledge base per hard rules unless user approves.
2. **Local Postgres 18**: User has Postgres 18 installed locally. Could use for local dev instead of SQLite, but DB not needed until Phase 9.

## Blockers
None.

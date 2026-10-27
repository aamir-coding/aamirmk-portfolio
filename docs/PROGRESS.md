# Progress Tracker

## Current Phase
**Band 1 / Gate 1: Complete** — Public shareable link active and hardened. Next: Phase 2 (Knowledge Base & RAG)

## Live Deployments
- **Backend (Render)**: `https://aamirmk-portfolio.onrender.com/api/health`
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
| P2: RAG | ⬜ Next Up (Band 2) | — | — | — |
| P5: Citations + gen UI | ⬜ Not Started | — | — | — |
| P4: Design system (full) | ⬜ Not Started | — | — | — |
| P6: Fit report | ⬜ Not Started | — | — | — |
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

## Measured Cold-Start Benchmarks (Render Free Tier)
- **Idle Timeout**: 15 minutes
- **Run 1**: 23.15s
- **Run 2 (Peak 19:30 IST)**: 32.93s
- **Run 3**: 22.71s
- **Run 4**: 22.39s
- **Baseline for Phase 3 UX**: 25s average, 35s max timeout allowance.

## Next Step
1. Present Gate 1 summary and shareable link status.
2. Deliver Phase 2 (Knowledge Base & Hybrid RAG) brief upon approval.

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

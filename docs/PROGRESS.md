# Progress Tracker

## Current Phase
**Phase 3: Streaming and the frontend chat MVP** — Ready to begin (new chat)

## Live Deployments
- **Backend (Render)**: `https://aamirmk-portfolio.onrender.com/api/health`
- **Frontend (Vercel)**: `https://aamirmk-portfolio.vercel.app/`

## Phase Status

| Phase | Status | Branch | Tag | Study Guide |
|-------|--------|--------|-----|-------------|
| Setup | 🟢 Complete | `main` | — | — |
| P0: Skeleton | 🟢 Complete | `main` | `phase-0-done` | [`phase-00-foundations.md`](study-guides/phase-00-foundations.md) |
| P1: Chat endpoint | 🟢 Complete | `main` | `phase-1-done` | [`phase-01-fastapi-chat.md`](study-guides/phase-01-fastapi-chat.md) |
| P3: Streaming + UI | 🟡 Next Up | — | — | — |
| P4: Design system (minimal) | ⬜ Not Started | — | — | — |
| P7: Safety (first-share) | ⬜ Not Started | — | — | — |
| — Gate 1: Shareable link — | | | | |
| P2: RAG | ⬜ Not Started | — | — | — |
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

## Measured Cold-Start Benchmarks (Render Free Tier)
- **Idle Timeout**: 15 minutes
- **Run 1**: 23.15s
- **Run 2 (Peak 19:30 IST)**: 32.93s
- **Run 3**: 22.71s
- **Run 4**: 22.39s
- **Baseline for Phase 3 UX**: 25s average, 35s max timeout allowance.

## Next Step
1. Start a new chat for Phase 1.
2. Present Phase 1 brief: `POST /api/chat` with `openai/gpt-oss-120b`, thin `llm.py` adapter, system prompt from file, context-stuffed resume, fake LLM test fixtures.
3. Wait for approval, create branch `phase-1-chat`.

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

# Progress Tracker

## Current Phase
**Phase 0: Environment, repo and a deployed walking skeleton** — Review & Teach-back

## Live Deployments
- **Backend (Render)**: `https://aamirmk-portfolio.onrender.com/api/health`
- **Frontend (Vercel)**: `https://aamirmk-portfolio.vercel.app/`

## Phase Status

| Phase | Status | Branch | Tag |
|-------|--------|--------|-----|
| Setup | 🟢 Complete | `main` | — |
| P0: Skeleton | 🟡 Review & Teach-back | `main` | `phase-0-done` (pending approval) |
| P1: Chat endpoint | ⬜ Not Started | — | — |
| P3: Streaming + UI | ⬜ Not Started | — | — |
| P4: Design system (minimal) | ⬜ Not Started | — | — |
| P7: Safety (first-share) | ⬜ Not Started | — | — |
| — Gate 1: Shareable link — | | | |
| P2: RAG | ⬜ Not Started | — | — |
| P5: Citations + gen UI | ⬜ Not Started | — | — |
| P4: Design system (full) | ⬜ Not Started | — | — |
| P6: Fit report | ⬜ Not Started | — | — |
| P8: Evals | ⬜ Not Started | — | — |
| P7: Safety (rest) | ⬜ Not Started | — | — |
| P10: Production | ⬜ Not Started | — | — |
| P9: Handoff + analytics | ⬜ Not Started | — | — |

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

## Next Step
- [ ] Measure cold-start time (after 20 min idle)
- [ ] Complete Phase 0 teach-back questions
- [ ] Tag `phase-0-done` upon user approval
- [ ] Present Phase 1 brief

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

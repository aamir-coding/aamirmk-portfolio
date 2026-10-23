# Progress Tracker

## Current Phase
**Setup** — Scaffolding and repo initialization

## Phase Status

| Phase | Status | Branch | Tag |
|-------|--------|--------|-----|
| Setup | 🟡 In Progress | `main` | — |
| P0: Skeleton | ⬜ Not Started | — | — |
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
- [x] Model: `openai/gpt-oss-120b` (single model for now)
- [x] Postgres: Supabase (deferred to Phase 9)
- [x] Git repo initialized
- [x] Directory structure created
- [x] .gitignore, AGENTS.md created

## Next Step
- [ ] Phase 0 brief → wait for approval → build

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

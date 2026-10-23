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
- [ ] User: install Python 3.12+ (currently 3.10.0)
- [ ] User: share Groq Limits page numbers for `openai/gpt-oss-120b`
- [ ] User: enable GitHub Actions (Settings → Actions → General → Allow all)
- [ ] Copy implementation plan to docs/
- [ ] Create .env.example
- [ ] Initial commit
- [ ] Begin Phase 0 brief

## Open Questions
1. **Python version**: User says 3.15.1 installed but system shows 3.10.0. Needs resolution.
2. **Groq rate limits**: Need actual numbers from user's Limits page for `openai/gpt-oss-120b`.
3. **Phone number**: resume.tex contains a phone number. Excluded from knowledge base per hard rules unless user approves.

## Blockers
- Cannot start Phase 0 backend work until Python 3.12+ is confirmed on PATH.

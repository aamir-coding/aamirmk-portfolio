# Agent Instructions — AI Digital Assistant Portfolio

This file is the condensed working rules for any AI agent working on this codebase.
Read this file, `docs/PROGRESS.md`, and `docs/decisions.md` at the start of every session.

## Project

A FastAPI + React portfolio site where a recruiter chats with an AI assistant that answers
only from curated facts about Aamir Mohammed Khan. The assistant cites sources, summons
UI cards via tool calls, and produces JD fit reports. Everything is hand-built: streaming,
retrieval, and the tool loop.

## Assistant Voice

Third person. The assistant speaks *about* Aamir, not *as* Aamir.
Identity: "I'm an AI assistant trained on Aamir's verified résumé, projects, and experience."

## Stack (fixed — do not deviate without explicit approval)

- Backend: Python 3.12+, FastAPI, Pydantic v2, pydantic-settings, Uvicorn (single worker)
- LLM: Groq API (free tier), `openai/gpt-oss-120b` (main) + `openai/gpt-oss-20b` (utility), via `groq` SDK async client
- Retrieval: Markdown/YAML facts, BM25 + fastembed ONNX embeddings, numpy
- Storage: External Supabase Postgres (Phase 9+), SQLAlchemy 2, Alembic
- Frontend: React, Vite, TypeScript, plain CSS with design tokens
- Streaming: SSE over POST via FastAPI native EventSourceResponse
- Hosting: API on Render free, frontend on Vercel Hobby
- Quality: pytest, Ruff, Vitest, Playwright, GitHub Actions
- NO: Next.js, LangChain, LlamaIndex

## Execution Order (bands and gates)

Band 1: P0, P1, P3, minimal P4, first-share P7 → Gate 1 (shareable link)
Band 2: P2, P5, full P4
Band 3: P6, P8, rest of P7, P10
Band 4: P9

## Hard Rules

1. Small vertical increments. Tests and checks after each one.
2. ONE phase at a time. Never start the next until user says "approved".
3. Stack is fixed. Ask before deviating.
4. Never invent facts about Aamir. Knowledge files come from resume.tex or from him.
   Mark drafts as DRAFT. No phone number or private details unless told.
5. Verify before using any library/API. Check official docs and installed version.
6. Report only what was actually run. Show real output. Say plainly if something wasn't run.
7. No secrets in git. Use .env locally, commit .env.example, never print keys.
   No real Groq calls in tests — use the injected fake.
8. Ask before: installing global tools, pushing to remote, deploying, installing skills,
   adding unlisted dependencies, destructive commands. No force-push.
9. No TODOs left silently — track in PROGRESS.md.

## Engineering Standards

### Backend
- Type hints everywhere, Pydantic models at every boundary
- pydantic-settings for config
- Dependency injection via Depends (no module-level globals)
- Consistent JSON errors, structured logs with request ID
- Ruff clean, no blocking calls on event loop (CPU-bound → thread pool)
- Every dependency justified and pinned
- Real client IPs from forwarded headers

### Frontend
- Strict TypeScript, no `any`
- Small focused components and hooks
- Zod at API boundary, all model output sanitized
- Accessible by default (keyboard, aria-live, contrast, reduced motion)
- Bundle budget (<200 KB gzipped initial JS)
- Behavior over implementation in tests

### General
- Clear code over clever code
- Comments only for non-obvious "why"
- Small diffs
- No silent TODOs

## Phase Loop & Skills Protocol

Every phase strictly follows this 6-step loop. The 8 installed skills in `.agents/skills/` MUST be actively leveraged at their designated steps:

1. **Brief**: Re-read the phase in `docs/implementation-plan.md`. Present a short phase brief (goal, 3-8 small reviewable increments, files, tests, risks, what you need from user). Wait for approval.
2. **Build**: Work on branch `phase-N-short-name`, test-first where practical, small conventional commits.
   - For React/frontend increments: Always consult `.agents/skills/vercel-react-best-practices/SKILL.md` (bundle budgets, re-render avoidance, cleanup).
   - For UI/CSS increments (Phase 4, Phase 3 chat UI): Always consult `.agents/skills/frontend-design/SKILL.md` (editorial dossier direction, CSS variables, typography, anti-generic AI UI).
   - For deep module abstractions (`llm.py`, `retriever.py`, tool loop): Consult `.agents/skills/codebase-design/SKILL.md`.
   - For debugging bugs, regressions, or unexpected test/runtime failures: Consult `.agents/skills/diagnosing-bugs/SKILL.md`.
3. **Decisions**: Log non-obvious choices and trade-offs in `docs/decisions.md`.
4. **Review**: Run all test suites. Verify every "Done when" item with real output evidence. Run a read-only architecture review using `.agents/skills/improve-codebase-architecture/SKILL.md` and `.agents/skills/codebase-design/SKILL.md`. For live browser UI verification and QA dogfooding, use `.agents/skills/agent-browser/SKILL.md`.
5. **Teach-back & Study Guide**:
   - Deliver interactive teach-back with 3 questions to verify user's mental model.
   - Create or update the deep interview study guide in `docs/study-guides/phase-N-<topic>.md` covering the theoretical concepts, line-by-line codebase connections, placement Q&A, and official doc links. Consult `.agents/skills/teach/SKILL.md`.
6. **Complete & Tag**: Update `docs/PROGRESS.md`, tag `phase-N-done`, push to remote, and STOP for user's explicit "approved".

## New Chat Session Kickoff Protocol

At the start of **every** new chat or phase:
1. Ground yourself immediately by reading:
   - `AGENTS.md` (this file)
   - `docs/PROGRESS.md` (current phase status, metrics, next step)
   - `docs/decisions.md` (architectural decisions logged so far)
2. Run `git status` to verify current branch and working directory cleanliness.
3. Check for any unresolved blockers in `PROGRESS.md`.
4. Greet the user with a 2-line summary of where the project stands and propose the immediate next action.

# AI Digital Assistant Portfolio: Implementation Plan

> This is the source-of-truth plan. Copied into the repo for reference.
> See the original document for the full version with diagrams.

## Overview

You are building a FastAPI and React site where a recruiter chats with an AI version of you, and the chat summons proof: project cards, a timeline, a JD fit report. Every answer is grounded in files you wrote and shows where it came from.

**Design principles (they decide every trade-off later)**

1. Truth over polish. The assistant answers only from your curated facts. When it does not know, it says so and offers to send the question to you.
2. The model selects, your server supplies. Cards and facts come from your data files, never from generated text, so the UI cannot hallucinate a project.
3. Every claim has a receipt. Source chips link to the resume line, repo or live deployment behind the answer.
4. Free to run, hard to abuse. Rate limits, a token budget sized to Groq's free-tier limits, and prompt-injection defenses ship before launch, not after.
5. Measured, not vibes. An eval suite of questions about you runs in CI and feeds a public badge.
6. Build the core pieces by hand (streaming, retrieval, the tool loop) before adopting frameworks. This is a learning project first.

---

*Full plan content follows. Refer to the original document for embedded diagrams and the roadmap visual.*

---

## Phase 0: Environment, repo and a deployed walking skeleton
Effort: 2-3 days. Outcome: empty but professional skeleton, live on Render + Vercel.

## Phase 1: FastAPI backend and first Groq chat endpoint
Effort: 2-3 days. Outcome: non-streaming POST /api/chat with context-stuffed resume.

## Phase 2: Knowledge base and RAG
Effort: 4-5 days. Outcome: hybrid retrieval (BM25 + embeddings), source metadata.

## Phase 3: Streaming and the frontend chat MVP
Effort: 3-4 days. Outcome: SSE streaming, chat UI, cold-start UX, starter chips.

## Phase 4: Design system, dossier visual direction and mobile
Effort: 4-5 days. Outcome: editorial dossier look, cover state, mobile-first.

## Phase 5: Source citations and generative UI
Effort: 4-5 days. Outcome: source chips, tool-calling project cards.

## Phase 6: JD fit report
Effort: 3-4 days. Outcome: requirement-by-requirement match with honest gaps.

## Phase 7: Safety, rate limits, quota guard and prompt-injection defense
Effort: 2-3 days. Outcome: cannot exhaust quota or misrepresent you.

## Phase 8: Evals, under-the-hood panel and eval badge
Effort: 3-4 days. Outcome: automated eval suite, public badge, debug drawer.

## Phase 9: Handoff, per-company links, forwardable summary and analytics
Effort: 4-5 days. Outcome: recruiter workflow, tailored pages, analytics.

## Phase 10: Production hardening, monitoring and launch
Effort: 2-3 days. Outcome: public, monitored, auto-deploying site.

---

## Appendix: Execution Bands

| Band | Phases | Gate |
|------|--------|------|
| 1 (fast path) | P0, P1, P3, minimal P4, first-share P7 | Gate 1: shareable link |
| 2 | P2, P5, full P4 | — |
| 3 | P6, P8, rest of P7, P10 | Gate 2: wide launch |
| 4 | P9 | — |

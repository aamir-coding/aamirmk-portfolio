# Progress Tracker

## Current Phase
**Phase 8: Evals, under-the-hood panel and eval badge** — on `phase-8-evals`. Human grades are validated. The authorized low-effort/1,024-output recovery stopped after one HTTP 200 response: 625 input + 131 completion = **756 tokens**, finish reason `stop`, zero accepted grades. The saved generic task error lacks the original exception/output, so its exact cause is unknown. Both runs are archived; combined actual usage is **four calls / 4,098 tokens**. Offline follow-up adds explicit JSON shape and safe failure diagnostics. Calibration remains incomplete; Increment 5 has not started. No further live call is authorized by either stopped run.

**Handoff Remediation Sprint** — complete. Implementation and historical local verification/review are recorded. The user authorized integration/push on 2026-11-03, then waived teach-back answers on 2026-11-04 once the study guide was verified. No answers were assessed. Local `handoff-remediation-done` tag targets integration commit `88fae8c`; the tag has not been pushed. Source branch: `codex/handoff-remediation`.

Approved scope: preset evidence/narratives, requirement-local citation validation, fail-closed extraction, colon-token preservation, EOF recovery, and JSON 422 responses. See [sprint study guide](study-guides/handoff-remediation.md) and [handoff retrospective](audits/2026-11-03-handoff-retrospective.md).

**Phase 6: Job Description Fit Report** — 🟢 Complete. Fixed 5-stage verification pipeline, structured extraction, per-requirement hybrid retrieval, batched alignment judging, deterministic anti-overclaiming invariant enforcement, honest ramp-up narratives (`skills.yaml`), SSE progress streaming (`POST /api/fit`), presets endpoint (`GET /api/fit/presets`), fit rate limiter (5 reports/day/IP), SHA-256 caching, frontend `FitReportModal`, `FitReportCard`, `FitProgressStepper`, and bidirectional gap bridge to chat.

Next: Execute Aamir's explicitly approved same-day schema-v3 calibration after clean-source checks. He authorized actual-usage reconciliation and zero visitor reserves, confirmed more than 195,000 tokens/990 requests available, and a quiet window expiring **13:20:28 IST on 5 November**. Human grades remain unchanged. Validation still needs its own later compatible budget; partial configurations are not combined.

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
| **Markdown AST Migration (react-markdown)** | 🟢 Complete | `main` | `markdown-ast-done` | [`quality-and-multi-turn-hardening.md`](study-guides/quality-and-multi-turn-hardening.md) |
| **Protocol & Session Hardening (DRN-034)** | 🟢 Complete | `main` | `protocol-hardening-done` | [`quality-and-multi-turn-hardening.md`](study-guides/quality-and-multi-turn-hardening.md) |
| P8: Evals | 🟡 Human grades verified; both live attempts stopped; calibration incomplete | `phase-8-evals` | — | [`phase-08-evals.md`](study-guides/phase-08-evals.md) |
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
1. All 28 human grades are validated. Both authorized live attempts stopped: first two accepted grades/three calls, then zero grades/one call. Combined actual usage: four calls/4,098 tokens. Another run needs a distinct plan, fresh capacity and separate approval. Genuine calibration/validation remains incomplete.
2. Remediation guide verified and teach-back responses waived by user on 2026-11-04; local completion tag targets `88fae8c`. User-reported live acceptance is below. No remote push of the new tag was performed.
3. Human calibration grading is a later user input at Increment 4. Fact approval/provenance and a concrete live budget require separate review; no blanket approval of draft facts or live model calls is implied.

## User-Reported Live Acceptance — 2026-11-04
- Aamir reports personally verifying that the live website works, including formatting, raw Markdown handling, continued chat context, links, and contact details.
- Evidence type: user-reported acceptance, provided in this chat on 4 November 2026. This is not agent-run browser QA, a semantic accuracy evaluation, factual approval of the 76 draft chunks, or independent verification of the deployed commit.
- The previous 253 backend/eval tests, 132 frontend tests, lint/typecheck/build results and 162.99 kB gzip measurement remain historical sprint evidence; they were not rerun during Phase 8 preparation.
- Preparation checks: clean `main` at `88fae8c` before documentation edits; local read-only loading confirmed 76 public indexed chunks, all 76 draft, 45 existing retrieval cases, and an embedding archive containing only `ids` and `matrix`. No tests or live Groq calls were run during preparation.

## Handoff Remediation — 2026-11-03
- Preset assessments use real current fact IDs and conservative narratives. Scores/headlines are computed from verdicts. All first three samples now rate Partial Match; embedded firmware remains Low Match. Facts were not silently promoted from draft.
- Per-requirement evidence maps replace the global citation union. Duplicate extracted IDs and blank requirement text are rejected. Citation membership is not semantic entailment.
- Invalid extraction gets one retry, then an `extraction_error` SSE event; no synthetic job requirement, report, or cache entry. JSON-mode responses bypass prose normalization.
- Typed heartbeat markers preserve colon-prefixed model tokens. Both chat and fit serialize markers as SSE comments. Slow-fit regression added after architecture review caught the shared-caller regression.
- Shared frontend reader requires a terminal event, reports premature EOF, cancels/releases the reader, and permits retry. Hooks tested through the actual transport. Explicit abort remains non-error behavior.
- Custom validation exception context is omitted from JSON error details, preserving HTTP 422 and request IDs.
- Final backend/eval run: **253 passed, 1 warning in 16.62s**. Frontend: **132 passed across 18 files in 17.48s**. Ruff/ESLint/TypeScript/build evidence recorded in the sprint guide. Zero live Groq calls.
- Final build: **162.99 kB gzipped JS** (explicit Node/zlib gate: **162,988 bytes < 200,000**); CSS 7.57 kB gzip. Vite build 5.53s. Ruff: all checks passed, 60 files formatted; ESLint/typecheck passed. Existing build warnings remain non-failing.
- Read-only architecture review: both findings fixed and rechecked; no remaining blocker within sprint scope. Browser QA not run: agent-browser is unavailable locally. No skills or dependencies installed.

## Remaining Handoff Audit Work
- [ ] Resolve approval/provenance for all 76 draft public fact chunks; reconcile stale fact descriptions with verified implementation.
- [ ] Per-provider-call quota admission/accounting, concurrent reservations, deadlines and client lifecycle.
- [ ] Semantic evidence support and known-negative constraints; generated summaries/ramp-up can still overclaim.
- [ ] Embedding content/model fingerprint and rebuild validation are implemented in Phase 8 Increment 1; bounded initialization/inference, BM25 degradation, truthful readiness and Linux 512 MB cgroup testing remain deferred.
- [ ] Verify production trusted-proxy chain and canonical IP identity.
- [ ] Cache identity/versioning/bounds, accurate cached flags, and an actual bypass for “Re-Run Live.”
- [ ] Remaining Markdown/code/URL repairs, session-history validation and message-length limits.
- [ ] CRLF SSE conformance, complete cancellation/idle-timeout policy, preprocessing heartbeats and upstream close ownership.
- [ ] Cross-language event fixtures are implemented in Increment 3; root evals and gzip-budget gates in CI remain Increment 5 work. Fit-dialog focus behavior and browser/device QA remain deferred.
- [ ] Apply remaining governing-document corrections and clarify Phase 10's dependencies on deferred Phase 9 work.

## Phase 8 Increment 1 — 2026-11-04
- Created `phase-8-evals`; only local work/commits are authorized. The approved brief, scoped audit disposition and authorization to start despite pending remediation close-out are recorded.
- Added 50 versioned cases: 40 development (32 legacy plus eight authored) and 10 new held-out cases in five separate groups. All labels are provisional; all 76 public chunks retain draft flags. No curated fit report was promoted to calibrated ground truth. The held-out set is author-visible and reserved from tuning, not independently blind.
- Added strict case/source validation, explicit all-relevant versus alternative source semantics, overlap checks against all 45 legacy inquiries, write-once split manifests and corpus/index snapshots. Default loading selects development only. Reserved validation checks structure/hashes/IDs, not answers. Text hashes survive Git CRLF/LF conversion; binary artifact hashes remain exact.
- Shared builder/runtime index validation now rejects same-ID content edits, model/library/asset changes, missing/legacy/corrupt/truncated artifacts and invalid matrices. Rebuilt the actual `(76, 384)` vectors from cached local ONNX assets; no model download or Groq call. Runtime never re-embeds the corpus or downloads query assets. General resource/readiness guarantees remain deferred.
- Explicit CI embedding-asset setup replaces implicit test-time model downloads. Root eval/gzip gates remain Increment 5 work. Pinned the already-used `PyYAML==6.0.3`; no package installation or new dependency was required.
- Test-first evidence: initial missing-module collection failures; three architecture findings reproduced as failing regressions, fixed and independently rechecked; Git newline-conversion regression reproduced then fixed without changing case content/splits/freeze time. Read-only review has no remaining blocker within Increment 1 scope.
- Fresh final verification: `.venv/Scripts/python.exe -m pytest backend/tests evals -q` with `FASTEMBED_CACHE_PATH` pointing at the existing local cache → **300 passed, 1 warning in 13.57s**. This includes the new 47 regressions. The sandbox run stalled and was interrupted; a 10-second minimal asyncio probe located the known Windows `_fallback_socketpair -> accept` deadlock. Only the completed outside-sandbox run is counted.
- Fresh frontend regression run: `npm test` → **132 passed, 18 files, 32.97s**. No frontend source changed. Frontend lint/typecheck/build/gzip checks were not rerun for this increment; previous build metrics remain historical.
- Fresh Ruff checks on backend/new eval modules/builder → **All checks passed**; formatter check → **68 files already formatted**. `git diff --check` passed. `python -m evals.validate` reports 40 development selected, 10 reserved, 76 public/76 draft; explicit structural validation covers all 50.
- See DRN-036, [eval dataset README](../evals/README.md) and [incremental study guide](study-guides/phase-08-evals.md). Phase 8 review/teach-back/tagging are incomplete. No live evaluation, model accuracy result, badge, push or deployment was performed.

## Phase 8 Increment 2 — 2026-11-04
- User authorized Increment 2 and waived waiting for teach-back answers once study material is verified complete/correct. Checked the remediation and Increment 1 guide against implementation, extended the Phase 8 guide through Increment 2, and retained optional practice without claiming assessed answers. Local annotated `handoff-remediation-done` targets `88fae8c`; it has not been pushed. Full Phase 8 implementation/guide are still incremental, not complete.
- Added `evals/metrics.py` and `python -m evals.run`: Hit@3/@5, truncated MRR@5 and macro Recall@3/@5 with explicit numerators/denominators. Alternative-source cases do not contribute to recall; no eligible cases produce null. Per-category results retain exclusions. Histories requiring recorded rewriting, JDs requiring extraction, protocol cases and no-source cases are excluded from this raw-query diagnostic, never silently counted as passes.
- Preserved all 45 legacy per-query top-five regressions and centralized the aggregate arithmetic. Portable gates: Hit@3 >=0.90, MRR@5 >=0.80, plus every legacy Hit@5. Machine-specific warmed mean/p50/p95/p99 latency is reported separately; the old default <25 ms assertion becomes the explicit `--max-mean-ms` benchmark option, independently recorded in JSON.
- Standalone cached local retrieval measurement: legacy development **Hit@3 41/45 (91.11%), Hit@5 45/45, MRR@5 0.888889**; versioned development **34 evaluated/40 total**, six explicitly excluded, **Hit@3 31/34 (91.18%), Hit@5 34/34, MRR@5 0.889706**. Recall@3/@5 is **1.0 over only two provisional all-relevant cases**; legacy recall is unavailable (zero eligible labels). The overlapping sets remain separate, with no combined score. All quality gates passed without changing facts, labels, splits or retrieval settings.
- Initial standalone warm mean latency: legacy 17.15 ms (p95 22.01 ms), versioned 17.27 ms (p95 26.25 ms). These are machine-dependent observations, not cold-start, production SLA or semantic-accuracy evidence. Saved diagnostic: `build/phase8-retrieval-increment2.json` (ignored local output), explicitly provisional/offline, no held-out execution, zero Groq calls. Its timestamp/source provenance identifies each execution; runtime versions/configuration and source/data/index hashes are recorded. Combined result/publication/CI contracts remain Increment 5 work.
- Fresh test-first evidence: missing-module collection failures followed by **27 fake-retriever/clock tests passed in 1.05s**, including cutoff arithmetic, macro denominators, misses, exclusions, strict legacy gate, errors, output round-trip and separate latency gating. Final full offline command `.venv/Scripts/python.exe -m pytest backend/tests evals -q` with the existing cache → **327 passed, 1 warning in 13.65s**, outside the already diagnosed sandbox asyncio deadlock.
- Fresh Ruff lint across backend/evals/builder → **All checks passed**; formatter → **74 files already formatted**. `git diff --check` and development-only `python -m evals.validate` passed: 40 selected/10 reserved, 76 public/76 draft. No frontend source changed; frontend tests/lint/build/gzip checks were not rerun for this increment. Their previous evidence remains historical.
- Scoped read-only architecture review found no blocker. Its independent test attempt stalled at async setup and was stopped; it is not counted as a completed suite. Root's completed runs above supply test evidence. See DRN-037 and the updated study guide/README. No package installation, model download, live Groq evaluation, public accuracy badge, remote push or deployment occurred.

## Phase 8 Increment 3 — 2026-11-04
- User authorized Increment 3. Added pure `evals/checks.py` and `python -m evals.replay`, plus explicit fake-only `python -m evals.capture` regeneration/checking. Actual chat/fit/preset endpoint bodies are committed in `evals/recordings/endpoints-v1.json`; real frontend Zod schemas and streaming clients consume those same bodies under mocked fetch. No frontend runtime code or dependency changed.
- Eight recordings: seven fake and one curated, delivered six fresh/one cached/one preset. They cover four unique development cases; 36 cases explicitly have no recording. Chat covers tool cards, colon/Unicode tokens, follow-up rewriting, guard refusal and model error. Fit covers fresh/cached reports, a real curated preset and fail-closed extraction. Fresh app dependencies, tool registries and fit caches prevent cross-run/seed leakage. TestClient intentionally skips production lifespan; this is endpoint contract evidence, not startup, resource or quota acceptance.
- Replay checks literal required/forbidden text, length, narrow refusal behavior, citation identity/retrieval membership, requirement-local evidence, configured negative-only evidence rules, summary/ramp-up prohibitions, unique requirements and production score arithmetic. Case ID/version/hash/split/transport binding and frozen expectations cannot be bypassed by expected-error handling. Valid emitted prefixes retain prohibitions/size/citation checks on EOF or application errors; completion-dependent checks are unavailable. Mutated bad fixtures demonstrate rejection. Semantic review remains pending for every result; membership does not prove support.
- Standalone replay: **8/8 recordings pass applicable limited checks**, `generation_accuracy_available: false`, zero Groq calls and no held-out execution. Exposes `server_cached_flag_unreliable` for the existing cached report flag defect; does not silently fix it. Curated requirement-local evidence is unavailable because no original retrieval map exists. All 76 public fact chunks remain draft. No comparable authorized live stuffed/RAG answer/token records exist; comparison and live token savings remain unavailable. Fake attempt/token counts are explicitly synthetic.
- Implementation commit `b63529c` is the clean source for the refreshed capture (UTC timestamp, `dirty: false`, case/corpus/dataset/prompt/source hashes). Only capture provenance changed on regeneration; endpoint bodies stayed identical. Replay separately fingerprints its checker/recording/current source and discloses prompt compatibility, unavailable checks and missing cases. Local diagnostic: `build/phase8-replay-increment3.json` (ignored). Complete combined result provenance/CI gates remain Increment 5.
- Test-first/review evidence: **28 replay regressions passed in 4.59s**. Architecture review found three false-pass classes (discarded error prefixes, mismatched case transport, skipped intrinsic curated evidence checks); six new failing regressions reproduced them, fixes passed, and independent read-only recheck reported **6 passed, 22 deselected in 1.78s**, no remaining blocker in that scope.
- Fresh complete offline verification: `.venv/Scripts/python.exe -m pytest backend/tests evals -q` with existing local embedding cache → **358 passed, 1 warning in 38.27s**, outside the diagnosed Windows sandbox asyncio deadlock. `npm test -- --run` → **150 passed across 19 files in 35.15s**, including 18 cross-language contract/stream tests. After the provenance-only fixture refresh, `python -m evals.capture` passed and endpoint tests passed again: **3 passed, 1 warning in 6.01s**. No live Groq calls or model downloads.
- Fresh Ruff lint → **All checks passed**; formatter → **79 files already formatted**. ESLint and TypeScript/build passed; Vite build **8.28s**, JS **162,988 gzip bytes < 200,000**, CSS **7.57 kB gzip**. Existing non-failing dependency annotation/chunk-size warnings remain. `evals.validate` reports 40 development selected/10 reserved, 76 public/76 draft. Browser QA was not run; no visible UI changed.
- DRN-038, eval README and study guide updated through Increment 3, with three optional practice questions. Answers were waived, not assessed. Human calibration grading remains required at Increment 4; a separate numeric budget/authorization remains required for all live Groq runs. No public badge, remote push, deployment or Phase 8 completion tag.

## Phase 8 Increment 4 — offline infrastructure, 2026-11-04
- Offline implementation is committed locally as `c24d778`; no remote push is authorized or performed.
- User authorized Increment 4 and chose to fill a copied human annotation JSON. Added `evals/calibration.py`, rubric/static judge instructions, write-once `prepare_grading.py` and frozen grading packet with **20 authored calibration answers and eight separate development validation answers**. Groups do not cross slices; no reserved held-out answers are executed. Full supplied draft evidence/local maps and case/item/corpus/rubric/prompt hashes are frozen. Examples include intentional defects, not new facts or real model answers. All human template labels remain null. An ignored editable copy is available at `build/human-v1.json`; it is never overwritten. No grades have been inferred or assessed.
- Human grading is relative to supplied draft evidence, not global fact approval. Four independent axes: support, completeness, behavior, tone. Agreement needs twenty human calibration answers and twenty judge calibration outputs first; separate validation requires eight binary human labels and both pass/fail classes per axis, with >=80% agreement on each axis. Counts, confusion, missing labels, abstentions and human overrides remain explicit. Human uncertainty is excluded; judge uncertainty is disagreement on binary human labels. Fake results remain diagnostic. Real calibration is **pending**, not completed; all 76 public fact chunks remain draft and core case labels remain provisional.
- Added default-offline `python -m evals.live`, explicit numeric-plan preflight and a separately authorized live entry point. No actual live plan/budget/approval was created or executed. Live authorization must bind exact plan hash, clean source/data/runtime/grading inputs, fresh exact-account limits, reviewer/reference/short time window and visitor/draft/input-policy acknowledgments. The model pair remains fixed; 20b judges evaluation answers, while production fit alignment retains its existing 120b stage. Default CLI reports zero calls without constructing a provider client.
- Standalone `MeteredLLM` reserves full per-model input/output ceilings before every attempt, including production rewrite/tool/extraction retries/alignment/summary. Reservations are never refunded; actual reported usage remains separate. Shared minute pacing, per-run/day/prior-use/visitor ceilings, request timeout and expiry/UTC-midnight deadline stop further calls on exhaustion or uncertain usage. SDK retries are disabled; Groq host pinned; client owned. Output truncation/model mismatch/inconsistent or missing usage fails closed. The byte-plus-overhead input policy is conservative, not exact tokenization or an enforced provider input cap; its limitations need explicit later budget approval. This does not fix the production-wide quota ledger.
- Actual nonstreaming chat logic and fresh fit pipeline/cache are exercised under fake providers; live streaming evaluation is deliberately disabled. Guardrail answers have their own origin. Judge inputs retain whole answers/evidence but compact defining rubric instructions; human labels and other judge outputs are excluded. Effective rendered system text is fingerprinted/snapshotted, so changed compaction cannot reuse old calibration. Known ledgers are saved before client closure and on close cancellation. Unique one-shot receipts, a fixed workspace lock, atomic local results, cross-run cooldown and conservative intersecting-day prior-use charges prevent local allowance resets. Native ONNX thread cancellation and other-workspace/visitor accounting remain limitations.
- Test-first/review: missing-module collection failed before implementation. Scoped review found six issues: judge-slice coverage bypass, unbudgetable prompts, cross-run minute reset, midnight prior-use omission, incomplete effective-prompt binding and close-cancellation ledger loss. The calibration bypass and two accounting gaps were reproduced as failing regressions, then fixed; prompts now have a maximum byte-policy reservation of **6,992** without changing answers/evidence. Feasibility arithmetic is test-only, not a proposed or approved live budget. Independent final pure recheck: **5 passed in 11.74s**; remaining cancellation paths reviewed statically. Root's async regressions cover actual cancellation. No blocker remains within the review scope.
- Fresh focused suite: **52 passed in 27.16s**, using fake clocks/providers and SDK MockTransport only. Fresh full `.venv/Scripts/python.exe -m pytest backend/tests evals -q` with existing cached local embeddings, outside the diagnosed Windows sandbox asyncio deadlock → **410 passed, 1 warning in 63.68s**. Fresh frontend regression run `npm test -- --run` → **150 passed across 19 files in 27.42s**. No frontend runtime source changed. Ruff lint → **All checks passed**; formatter → **85 files already formatted**. `git diff --check`, development validator and frozen grading-packet validator passed. Frontend lint/typecheck/build/gzip were not rerun for this backend/eval increment; Increment 3's build evidence remains historical. No browser QA was run; no visible UI changed.
- Actual offline calibration command against the blank committed template reports **0 calibration/0 validation human grades, 0 judge outputs, status pending, calibrated false, generator accuracy unavailable** (expected exit 1). Offline live-runner default reports zero calls. All automated checks use fakes/mocks; local ONNX retrieval uses existing assets. No Groq calls, model downloads, held-out scoring, dependency installs, public badge, remote push, deployment or Phase 8 tag.
- DRN-039, eval/annotation READMEs, brief status and phase study guide updated through implemented Increment 4 infrastructure, including three optional practice questions. Teach-back answers were waived, not assessed. **Still required:** human grades from Aamir, separate numeric live budget/authorization, actual judge calibration/validation evidence. Increment 4 is not fully complete and Increment 5 has not begun.

## Increment 4 human grading received — 2026-11-05
- Aamir submitted JSON with all twenty calibration and eight validation items filled, reviewer identified and independent-grading attestation present. Ran `python -m evals.calibration --annotations <provided attachment>` against the unchanged submission: schema, frozen packet/rubric/item hashes, unique IDs, required labels/rationales and development coverage passed. The CLI's exit 1/status `pending` is expected because judge outputs do not exist; it does not mean human validation failed.
- Preserved the provided bytes unchanged at ignored `build/phase8-human-2026-11-05/human-v1.json` and versioned `evals/annotations/human-v1-aamir-2026-11-05.json` for reproducibility. Validation evidence is at `build/phase8-human-2026-11-05/offline-validation.json`. Canonical human annotation SHA-256: `833f71ab520b9d0c5a9ba21d29f7af71cb8eece220a2f79586179f63dd9d5d67`; packet hash remains `f1fad4a25c601f23b37893cb61efcb0767af922e8ca0403f0b44ce995cecfc90`. The committed blank template and older working copy were not overwritten. No human labels were changed or inferred.
- Calibration human counts (pass/fail): support 11/9, completeness 10/10, behavior 15/5, tone 11/9. Validation has four passes/four failures on every axis, no abstentions. Coverage/diversity prerequisites are satisfied. Labels are human judgments relative to supplied draft evidence, not factual approval; all 76 public chunks remain draft and frozen core case labels are unchanged.
- Prepared a separate **unapproved** numeric proposal for the twenty calibration judge calls only. Proposed model: `openai/gpt-oss-20b`; maximum 20 attempts, 140,000 reserved input tokens and 10,240 output tokens (150,240 combined), 7,000/512 per-call ceilings, no retries, 60-second request timeout and 45-minute run deadline. Reservations force at most one attempt per minute and a 60-second delay after completion. Stop on truncation, errors, uncertain usage, mismatched model, exhausted cap, input drift or expiry. Actual reported usage remains separate; input byte reservations are not exact token counts or provider-enforced input caps.
- Proposal assumes limits of 30 RPM/1,000 RPD/8,000 TPM/200,000 TPD and reserves 400 TPM, 10 RPM, 20,000 TPD and 100 RPD for visitors. Declared prior-use ceilings are conservative upper bounds, not observed usage: 29,760 tokens/880 requests. Before any authorization, Aamir must confirm fresh account limits and at least 170,240 tokens/120 requests of remaining daily capacity, plus a quiet run window compatible with the minute headroom. Rechecked official Groq documentation and installed SDK 1.7.0; public limits do not verify this account's remaining capacity.
- Eight validation-model calls, generator calls, retries and publishing accuracy are outside this proposal. Under full conservative reservations the 20+8 judge stages do not fit one 200,000-token day with visitor headroom; validation needs a later quota day and separate approval. Current genuine judge counts remain 0/0, agreement/calibration pending, model accuracy unavailable. No live Groq call, held-out execution, API-key inspection, push or deployment occurred. No implementation changed or full suites rerun; the previous 410/150 counts remain historical.

## First authorized calibration run and offline follow-up — 2026-11-05
- Aamir confirmed the reviewed twenty-answer proposal, listed account limits/remaining capacity and quiet 45-minute window, following his instruction to proceed with calibration. Recorded approval for exact plan SHA `37887f8c9acf858da2dca52f76c98bac5f11b78491d4f5219b755742de00c320`, source `1927818`, maximum 20 attempts/150,240 reserved tokens, no retries, 512 output tokens/call. Loaded the existing local credential inside the launcher process without printing it. The actual run used the approved runner outside the known Windows sandbox asyncio deadlock; it was a live evaluation, not an automated test.
- Outcome: **stopped**, `incomplete_provider_output`, **three real 20b requests**, **two accepted grades out of twenty**. Every request had reconciled reported usage: **2,306 input + 1,036 completion = 3,342 total tokens**. Third request: 752 input/512 completion. HTTP 200 did not establish complete output. Exact old finish reason was not retained; it is not backfilled as `length`. No retry, output-cap increase, validation call, generation call or held-out execution occurred.
- Preserved original build receipt/result for quota accounting, and archived byte-identical copies with a partial summary in `evals/annotations/runs/calibration-2026-11-05-a/`. Result canonical hash `af6878934dacfe3c097abd3499d3accb0db1347c8b155208fdd309c2f9741cf0`; ledger hash `b7a486200710a610a71c23d291fc707ba01ab32eede19e244b4ecfaecc0178cf`. No complete `judge.json` was emitted; calibration/accuracy remain unavailable. Original active lock was released. Old partial reviews are diagnostic evidence only.
- Offline follow-up: explicit `reasoning_effort: low` for evaluation judging only, finish reasons retained on new attempts, required typed configuration in plan schema v2/results/JudgeSet (20b, temperature 0.2, JSON format, effort and output ceiling), and exact calibration/validation settings compatibility. Legacy plans/unrecorded configurations fail closed. Production generation settings, prompts/rubric, packet/splits, all human labels and all 76 draft flags remain unchanged. Low effort is a supported mitigation, not a demonstrated fix; a new live run can still truncate.
- Four red regressions reproduced absent finish metadata, implicit judge-plan settings and absent SDK effort control. Offline fake/MockTransport follow-up: **56 passed in 33.45s**. Scoped read-only review: **9 pure tests passed in 6.69s**, archive probes passed, no blocker; no async/live calls by reviewer. Two new test-budget fixtures initially lacked sufficient minute headroom and were corrected without changing production limits or the frozen inputs.
- Fresh full offline verification: `.venv/Scripts/python.exe -m pytest backend/tests evals -q` with cached embeddings, outside the diagnosed sandbox issue → **414 passed, 1 warning in 70.37s**. Frontend `npm test -- --run` → **150 passed across 19 files in 38.77s**. Ruff/format/diff checks passed. No frontend runtime code changed; frontend lint/build/gzip were not rerun, and previous build metrics remain historical. All automated tests used fakes/mocks; **the only real provider calls this turn were the three approved calibration calls above**.
- The local ledger conservatively holds the full stopped run's approved daily ceiling, rather than treating unused allowance as retry permission. That is not actual usage (3,342) or just the three attempted reservations (22,536). Preserve the hold/receipt. Prepare a new full twenty-answer low-effort plan for a later UTC budget day, with fresh account-capacity evidence and separate approval; do not mix in the two old/default-effort grades. The same numeric ceiling can be proposed, but no new live authorization is implied. Validation needs its own later compatible plan/budget.
- DRN-040, READMEs and study guide record the actual outcome, limitations and offline follow-up. No new dependencies, model download, fact approval, public badge, phase completion tag, remote push or deployment. Increment 4 remains incomplete; Increment 5 has not started.

## Approved 1,024-token recovery amendment — 2026-11-05
- Aamir explicitly approved `calibration-2026-11-06-low`, confirmed listed limits/capacity, and requested `max_completion_tokens`/`per_call_output` of 1,024. Read-only clock check still showed 5 November UTC. The previous stopped run's hold was not deleted, reconciled away or bypassed; no new model call was attempted.
- Initial feasibility: 7,000 input + 1,024 output + 400 visitor reserve = 8,424 TPM, above the confirmed 8,000 limit. A failing regression reproduced the full-prompt bound of 6,992 exceeding the revised 6,488 input reservation. Added concise runtime prefix `evals/rubrics/judge-v2.txt`; exact answers/evidence JSON and the four rubric defining sentences remain intact. Frozen v1 template, packet/rubric/splits and human grades remain unchanged. The current effective prompt is explicitly bound into planning inputs and artifact compatibility.
- New largest complete prompt bound: **6,369**. Proposed per-call reservations: **6,488 input + 1,024 output = 7,512**. Full twenty-call ceiling remains **150,240** (129,760 input + 20,480 output); with 400 visitor TPM, minute reservation is **7,912 < 8,000**. Daily visitor reserve remains 20,000, preserving the user's confirmed 170,240 total capacity requirement. No input-estimation policy or visitor/quota guard changed. Output headroom is larger but not a guarantee against another cutoff.
- The local prior hold clears with the next UTC budget day, **05:30 IST on 6 November**. Asked asynchronously whether to schedule for that time or wait for the user's message. No choice has yet been received, and no scheduling action has been taken. Do not create a new live approval window until timing is resolved. The stopped original authorization is not reused.
- Fresh focused offline checks: **57 passed in 37.00s**. Full backend/eval suite with existing cache, outside the diagnosed sandbox asyncio issue: **415 passed, 1 warning in 56.31s**. Frontend regression suite: **150 passed across 19 files in 17.46s**. Ruff passed; formatter reports **85 files already formatted**; diff check passed. No frontend runtime source changed; frontend lint/build/gzip were not rerun. All tests used fakes/mocks; **zero new real provider calls this turn**.
- Scoped read-only architecture review found no blocker and independently ran **3 pure tests in 9.56s**; reviewer made no edits or provider calls. DRN-041 captures the rendering/budget choice; study guide and runtime instructions are updated without re-grading the user data. The amended clean-source plan will retain the user's approved 1,024-output setting and unchanged 150,240 total ceiling; no execution window is inferred while timing remains pending.

## Explicit immediate-start reconciliation — 2026-11-05
- After the old daily hold was explained, Aamir explicitly instructed starting now and asked whether the 200,000-token limit would be exceeded. His confirmed 170,240 remaining tokens cover the unchanged 150,240 run ceiling plus 20,000 visitor reserve. This is conditional on that fresh account statement and reserved visitor allowance, not an independent view of provider usage. Recorded quiet-window start at 06:26:29 UTC and expiry 07:11:29 UTC; do not extend that window merely because preparation takes time.
- Added an opt-in operator reconciliation for **only** `stopped/incomplete_provider_output` results whose entire attempt ledger has known, reconciled usage. It binds canonical receipt/result/ledger and original approved-plan hashes; verifies original approval chronology, aware wall timestamps, finite ordered attempt times, approved models/caps, sequential attempts and aggregate ceilings. Requires actor/reference, verified process exit and derived charges. Missing records preserve the full hold; unknown/lifecycle/active/stale/forged records fail closed. Cooldown, day admission, exact-plan approval and one-shot run IDs remain enforced.
- Reconciliation retained **3 calls / 22,536 reserved tokens**, never reduced them to the 3,342 actual reported tokens. Only the **127,704 unattempted** portion of the prior 150,240 potential ceiling is released. The original receipt/result were not changed or deleted. The independent record is preserved in both the original build run directory and `evals/annotations/runs/calibration-2026-11-05-a/reconciliation.json`. This is explicit known-usage reconciliation at the user's direction, not an automatic refund or reset for uncertainty.
- Test-first: nine missing-function failures, then negative/forgery/chronology cases. Read-only review found missing original-plan binding and invalid chronology acceptance; both were corrected with regression cases and independently rechecked. **19 reconciliation tests passed in 6.16s**. Final full offline suite: **434 passed, 1 warning in 56.02s**; Ruff/formatter/diff checks passed. Frontend's same-turn **150 passed in 17.46s** remains the fresh regression evidence; no frontend runtime source changed. All automated checks use fakes/mocks; no new real model call has yet run at this preparation point.
- Immediate budget: 129,760 input + 20,480 output = 150,240; declared total prior ceiling 29,760 still exceeds the reconciled local reservation floor 22,536. Add 20,000 visitor reserve to obtain 200,000 maximum under the user's account declaration. Request ceilings remain 20 new + 880 declared prior + 100 visitors = 1,000. The source/approval window and hard stop remain binding. No scheduling action, held-out call, factual approval, push, deployment or phase completion is implied.

## Immediate recovery outcome and offline diagnostics — 2026-11-05
- Executed the exact approved low-effort/1,024-output plan at clean `d609e12`; plan SHA `aff966c3252770637c3b77d6e336ebe23032a359b92c1d11057c45677b39af2c`. Run identifier `calibration-2026-11-06-low` is a label; actual execution was 5 November UTC, inside the confirmed window. First HTTP 200 response completed at 06:38:28 UTC. It stopped with `task_error_or_deadline`, **one attempt / zero accepted grades**, reported **625 input + 131 completion = 756 tokens**, finish reason `stop`. This was not another output cutoff. The exact exception and final response were not retained, so the post-response cause cannot be established from this version's artifacts.
- Archived unchanged receipt/result plus an explicit limitation summary in `evals/annotations/runs/calibration-2026-11-06-low/`. Result SHA `9c341bcc4e2478bf4cad9e2f14130319ba90bc881c052dfccf12f3dafc9c79d8`; ledger SHA `54cca01ded40719cdc07b9f1f1f74fa30d2aa2560fea2edc2f482f660b164e0f`. Original build receipt/result remain intact. Across both runs actual usage is **four requests / 4,098 tokens**. No automatic retry, validation or held-out call occurred. The generic task-error stop is ineligible for the incomplete-output-only reconciliation and retains its full local hold.
- Offline follow-up: runtime v3 explicitly demonstrates nested labels/string rationale with neutral placeholders, retaining complete evidence and rubric criteria. Largest complete prompt bound **6,464 <= 6,488**; per-call/output/visitor ceilings are unchanged. New effective prompt SHA `afca8b72062a30b7c812e0646685b21605603c4623a4273da0c9b3b1cad72e33` invalidates older plans/results. Future artifacts retain returned final judge content before parsing and safe structured contract errors; other failures retain exception class/task ID. Hidden reasoning, secrets and visitor transcripts are outside this scope. Frozen packets, human grades, facts and historical run artifacts are unchanged.
- Test-first diagnostics regressions: three malformed fake responses previously failed the expected-specific-diagnostics assertion; all now pass. Fresh full offline backend/eval suite: **437 passed, 1 warning in 62.84s**, using existing embedding cache outside the diagnosed Windows sandbox asyncio issue. Ruff with repository config passed; **84 files already formatted**; diff check passed. Frontend's same-turn **150 passed in 17.46s** remains the regression evidence; no frontend source changed and lint/build/gzip were not rerun. A mistakenly unconfigured Ruff invocation reported an existing import-order difference; rerunning with `backend/pyproject.toml` passed without modifying that file.
- Scoped read-only architecture recheck found no actionable blocker; independently **3 pure tests passed in 10.67s**, covering input bound, effective-prompt invalidation and frozen packet preservation. Reviewer made no edits/provider calls. DRN-043 and the study guide distinguish the verified diagnostics fix from the unknown live cause. Another run needs a distinct clean-source plan, fresh capacity/window and separate approval. No further live call, production change, dependency, fact approval, remote push, deployment, accuracy badge or completion tag was made. Increment 4 remains incomplete; Increment 5 has not started.

## Explicit same-day actual-usage override — 2026-11-05
- Aamir explicitly approved schema-v3/low effort/1,024 output for immediate calibration, actual-token reconciliation of the four known calls and zero visitor reserves. He confirmed more than 195,000 tokens/990 requests remaining and a quiet 45-minute window. Recorded at 12:35:28 IST; expiry **13:20:28 IST on 5 November**, not extended during preparation.
- Two separate actual-usage records bind original receipts/results/ledgers and approvals, verify process exit and complete reported usage, and preserve original attempted reservations of **30,048**. Daily charge becomes **4,098 actual tokens / four calls**. Original receipts/results and the first conservative reconciliation remain unchanged. Known generic post-response task stops now qualify only under this explicit actual-use policy; unknown/lifecycle usage remains ineligible. All four visitor reserves are zero in the newly approved budget, not changed in older receipts or production code. New in-run admission still reserves full caps and has no automatic retry.
- Proposed local ceiling: **4,098 prior + 150,240 new = 154,338 tokens**, four prior + twenty new = **24 requests**. Fresh capacity is user-confirmed, not independent provider telemetry. Per-call reservation stays 7,512 <= 8,000 TPM. Human grades, full evidence, schema-v3, low effort, output cap and stop conditions are unchanged.
- Test-first actual-use/zero-visitor cases failed, then passed; **34 reconciliation tests passed in 7.97s**. Fresh full offline suite: **452 passed, 1 warning in 57.74s**; configured Ruff/format/diff checks passed (84 files formatted). Scoped read-only review found no blocker and independently ran **28 pure tests in 6.68s**; no reviewer edits/provider calls. Frontend checks were not rerun because frontend source is unchanged. DRN-044 and study guide capture the explicitly superseded policy. Preparing a distinct exact clean-source plan; no new provider call at this preparation point.

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
Human grading is validated; calibration and validation remain incomplete after two stopped live runs. The second run's exact task error remains unknown. Both stopped approvals are consumed. Aamir has separately authorized immediate schema-v3 recovery, actual-use reconciliation and zero visitor reserves (DRN-044), with fresh capacity and a quiet window expiring 13:20:28 IST on 5 November. Execute only the distinct clean-source plan within that window. All 76 fact chunks remain draft; validation/publication gates and Phase 8 completion remain future work.

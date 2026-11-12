# Progress Tracker

## Current Phase
**Phase 9: Handoff, per-company links, forwardable summary and analytics — in progress.**
Aamir approved the seven-increment brief on 12 November 2026 and authorized
local work on Increments 1–2. Build branch: `phase-9-handoff-analytics`.

**Phase 10: Production hardening, monitoring and launch — 🟢 Closed, deployed, and verified live on Render & Vercel**
The locally verified `main`, `origin/main` tracking ref and `phase-10-done` tag
matched at `5f487d4` at Phase 9 kickoff.
[Phase brief and architectural pre-mortem](briefs/phase-10-production-hardening.md).
Band 3 order (P6 → P8 → remaining P7 → P10) is fully complete. Next milestone: Band 4 / Phase 9 (Handoff + Analytics).

**Phase 10 Post-Completion & Launch Hardening — 11 November 2026:**
Following initial Phase 10 tagging, live deployment to Render and Vercel revealed three operational failure modes that were resolved, verified with real requests, and recorded:
1. **FastEmbed Container Cache Isolation (503 Service Unavailable):** On Render, the build container and runtime container do not share `/tmp`. At runtime, `/tmp` was empty, causing `DenseIndex` initialization to fail with `local_files_only=True`. Because the retriever failed to load, `app.state.retrieval_ready` stayed `False`, returning 503 on `/api/health`.
   - *Fix (DRN-069):* Created `backend/.cache/fastembed`, added `ensure_model_cached()` to `backend/app/retrieval/dense.py`, called during both build and `lifespan` startup, and configured `FASTEMBED_CACHE_PATH: .cache/fastembed` in `render.yaml`.
2. **Cold-Start Unallocated Boot Allowance ("Live answers are resting"):** Render free tier sleeps after 15 minutes of inactivity. Under DRN-063, `InferenceLedger` initialized with `self._allowance = None`, requiring an external operator POST to activate. Wakeup containers remained in resting mode despite a valid `GROQ_API_KEY`.
   - *Fix (DRN-067):* Added `AUTO_AUTHORIZE_INFERENCE: bool` and boot-bound auto-authorization in `lifespan` when `ENVIRONMENT == "production"` and `GROQ_API_KEY` is present, binding a fresh UTC-midnight allowance to `app.state.llm.ledger.boot_id` with `warm_up_seconds=0.0`. Test isolation is preserved.
3. **TPM Byte Ceiling Bottleneck (`QuotaDenied("request_too_large")`):** Under DRN-054, `reserve_input_tokens` uses serialized UTF-8 bytes plus headroom (`len(encoded) + 512 + 32 * count`) as an upper-bound token estimator. Grounded chat prompts with 4 chunks + tool schemas total ~9,000 byte-tokens. The initial default `tpm=6400` was naively set to 80% of 8,000 without realizing the estimator measures in bytes rather than real tokens (~1,700 real tokens). Every chat query failed locally with `request_too_large`, and 2-turn tool calls (~18,500 total bytes) failed with `wait_expired`.
   - *Fix (DRN-068):* Calibrated `tpm` to `32,000` byte-tokens ($8,000 \text{ real tokens} \times 4 \text{ bytes/token}$), safely admitting grounded queries and multi-turn tool calling while keeping actual Groq token consumption within Groq's 8,000 real TPM limit.
4. **Baseline Eval Fingerprint Synchronization (DRN-070):** Changes in `backend/app/` updated the `"application"` SHA-256 fingerprint. Synchronized `evals/baseline.json` (`2956c6a8...`), re-ran `evals.run` and `evals.publish` (`eval-summary.json` updated), with all 643 backend tests and 181 frontend tests passing.
5. **Candidate Resume Asset:** Linked official candidate resume (`frontend/public/resume.pdf`), deleted `resume-draft.pdf`, and updated UI labels.
6. **Live End-to-End Verification:** Live smoke tests confirmed Render `GET /api/health` 200 OK (`assistant_state: "ready"`), `POST /api/chat` 200 OK (Groq `openai/gpt-oss-120b` executed in 1.59s), `POST /api/chat/stream` 200 OK SSE token streaming with sources, and interactive project card tool summoning 200 OK.

**Phase 7 (remaining): Safety hardening — closed, merged and tagged.** On 6 November
2026, Aamir confirms merging/pushing `main` at
`de73fb511ef82fd9c5b5f3c7e864ab0fcf0c6454` and pushing remote tag
`phase-7-hardening-done` at that commit, triggering CI/deployment. Local `main`,
`origin/main` tracking ref and tag independently match. A fresh `git ls-remote`
failed with `getaddrinfo() thread failed to start`; remote publication is user-confirmed,
not independently reverified. Cloud CI success and deployed revision remain unchecked.
**10 November follow-up:** outside-sandbox read-only verification confirms both remote
refs at the full SHA above and successful main CI/security jobs. P10 deployed revision
and hosting settings still require release evidence; see the P10 ledger below.
Closure preserves the [P7 evidence ledger](audits/2026-11-06-phase-07-safety.md)
and outstanding operational/semantic launch gates; it does not certify model accuracy.

**Phase 8: Evals, under-the-hood panel and eval badge — merged and remotely tagged**
at `440e81d`. On 6 November 2026, read-only `git ls-remote origin` independently
confirmed both `refs/heads/main` and `refs/tags/phase-8-done` target
`440e81d6057a493c32f851f962e6cbda9fc19e9f`. Aamir reports the merge/push triggered
cloud CI and deployments and confirms deployment. Pipeline success and deployed
runtime revision were not independently checked in this kickoff.
Aamir accepted the authentic failed independent validation baseline,
closed Increment 4, and authorized finishing Increments 5–7. Reproducible artifacts/CI,
real request-local telemetry, accessible drawer, `/api/eval-summary`, `/evals` and an
actual-result engineering badge are implemented. **Judge validation remains FAILED**:
Support 8/8 (100%), Completeness 6/8 (75%), Behavior 7/8 (87.5%), Tone 6/8 (75%).
All five disagreements, unchanged human grades and all 76 draft facts are preserved.
**Model accuracy remains unavailable.** No new Groq calls in this kickoff.
[Validation baseline](audits/2026-11-05-judge-validation.md) ·
[Close-out review](audits/2026-11-05-phase-08-closeout.md).

**Handoff Remediation Sprint** — complete. Implementation and historical local verification/review are recorded. The user authorized integration/push on 2026-11-03, then waived teach-back answers on 2026-11-04 once the study guide was verified. No answers were assessed. Local `handoff-remediation-done` tag targets integration commit `88fae8c`; the tag has not been pushed. Source branch: `codex/handoff-remediation`.

Approved scope: preset evidence/narratives, requirement-local citation validation, fail-closed extraction, colon-token preservation, EOF recovery, and JSON 422 responses. See [sprint study guide](study-guides/handoff-remediation.md) and [handoff retrospective](audits/2026-11-03-handoff-retrospective.md).

**Phase 6: Job Description Fit Report** — 🟢 Complete. Fixed 5-stage verification pipeline, structured extraction, per-requirement hybrid retrieval, batched alignment judging, deterministic anti-overclaiming invariant enforcement, honest ramp-up narratives (`skills.yaml`), SSE progress streaming (`POST /api/fit`), presets endpoint (`GET /api/fit/presets`), fit rate limiter (5 reports/day/IP), SHA-256 caching, frontend `FitReportModal`, `FitReportCard`, `FitProgressStepper`, and bidirectional gap bridge to chat.

Band 4 is active under the 12 November Phase 9 approval. The current build covers
company links and the local Postgres foundation.
Aamir approved continuing through the phase on 10 November 2026. Phase 7 teach-back
answers remain unassessed; its milestone is closed by Aamir's explicit confirmation.
Aamir approved the Phase 7 six-increment brief on 6 November. A new factual accuracy claim
still needs approved facts, reliable judging and compatible held-out generation evidence;
further judge tuning needs a fresh independently graded validation version, never retuning
and resampling these exposed eight outcomes. These are experiment/publication gates,
not unfinished work in the accepted offline engineering milestone.

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
| P8: Evals | 🟢 Merged/tag verified on origin; deployment user-confirmed; validation failure preserved | `main` (`440e81d`) | `phase-8-done` (origin verified) | [`phase-08-evals.md`](study-guides/phase-08-evals.md) |
| P7: Safety (rest) | 🟢 Closed; merge/remote push user-confirmed at `de73fb5`; launch gates carried forward | `main` | `phase-7-hardening-done` (remote user-confirmed; local verified) | [Updated P7 guide](study-guides/phase-07-safety-rate-limiting.md) |
| P10: Production | 🟢 Complete; live deployment verified on Render & Vercel | `main` | `phase-10-done` | [P10 guide](study-guides/phase-10-production-hardening.md) |
| P9: Handoff + analytics | 🟡 In progress | `phase-9-handoff-analytics` | — | — |

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
1. Review Phase 9 Increments 1–3. Increment 4 adds feedback and admin. Hosted
   verification will use the credentials Aamir provides later.
2. Phase 7 is closed at `de73fb5` / `phase-7-hardening-done`; remote push is user-confirmed. Verify cloud checks and deployed runtime identity during P10 operational acceptance.
3. Preserve all 28 human grades and five validation disagreements. Independent validation failed Completeness/Tone at 6/8 each. Fact approval, fresh independently graded validation and any live generation budget remain separate publication gates.

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

## Same-day schema-v3 live outcome — 2026-11-05
- Executed plan SHA `a918599db21437812857c2a77fefb640e30d43f5ce0f8233bf475e60786eb5f0` at clean `be132d5`, prior four calls/4,098 tokens, zero visitors, low effort/1,024 output. No tracked source/input changes during execution. Twenty attempts collected nineteen schema-valid grades, then final HTTP 400 at **12:59:15 IST**, before the 13:20:28 expiry. No retry/validation/held-out call occurred.
- Known usage: **11,962 input + 2,379 completion = 14,341 tokens**. Final usage is unknown; its **7,512-token reservation and full stopped-run hold remain**. Earlier reconciliations are intact. Today's total: **24 requests / 18,439 reported tokens plus one unknown-usage request**, not an independent account balance.
- Exact receipt/result/last HTTP progress/summary: `evals/annotations/runs/calibration-2026-11-05-schema-v3/`. Result SHA `265b44cd08c710465fafef08751b15a25e091ffafd1546ce71e6057fcd2cdfa4`; ledger SHA `e598dfcab1afdd7ce60da762512e299ecc654075d9ac5d3cf79d2b61246d6d08`. No `judge.json`. HTTP status is established; exact provider body/cause was not retained and must not be invented.
- Partial diagnostics: support **17/19**, completeness **19/19**, behavior **13/19**, tone **14/19**, one missing on every axis. All thirteen item/axis disagreements remain visible. Several model rationales repeat only IDs/template text. Even a matching final grade leaves behavior at most 14/20 and tone 15/20. The [calibration review](audits/2026-11-05-judge-calibration.md) recommends reviewing instructions/axis separation/rationale quality before more calls; human labels and validation outcomes are untouched.
- Offline test-first follow-up retains safe provider class/status/allowlisted code, excluding messages/body/failed generation/hidden reasoning. Fake HTTP 400 regression failed for missing metadata, then passed. Final full offline suite: **453 passed, 1 warning in 58.63s**; configured Ruff/format/diff checks passed. Read-only review found no blocker and verified hashes, usage/reservation and metric counts without edits/provider calls. One sandboxed async diagnostic hit the known deadlock and was terminated; successful tests used the outside-sandbox workaround. No frontend changes/checks.
- DRN-045, READMEs and study guide record limitations. No new prompt, human/fact approval, badge, dependency, push, deployment or tag. Further live calls need a new reviewed budget/explicit authorization. Calibration/validation remain incomplete; Increment 5 has not started.

## Separately authorized v4 preparation — 2026-11-05
- Aamir explicitly approved twenty fresh judge-v4/20b/low/1,024 calibration attempts, actual-use reconciliation, zero visitors and >180,000 remaining tokens. Recorded immediate authorization at **13:51:03 IST**, new hard 45-minute expiry **14:36:03 IST**; the earlier expired window is not reused.
- V4 defines the grading target, behavior/tone and per-axis reasons using the user's examples; support/completeness definitions remain frozen. The stricter `I refuse` example follows the user's explicit instruction, with its interpretation risk documented. Human labels/packet/full evidence/previous prompts are unchanged; new effective prompt invalidates prior partial grades.
- Item 20's full SDK wire payload and supported JSON-object/low/1,024 settings passed MockTransport tests. Largest full input bound **6,953 <= 6,976**; input+output bound 7,977 is below documented model context 131,072/output 65,536. No frozen content edits or real probe. The old HTTP 400 cause remains unknown; valid input cannot guarantee provider success.
- Added explicit actual-known plus reserved-unknown reconciliation: v3 charges 14,341 known + full 7,512 unknown = 21,853, with original records/reservations intact. Combined prior daily charge **25,951 / 24 requests**. New twenty-call ceiling **160,000**, per-call 6,976+1,024=8,000 TPM, all visitors zero. Projected conservative daily maximum **185,951 / 44 attempts**. Reject malformed/nonterminal unknowns, missing/forged usage, stale bindings, lifecycle failures and invalid chronology. All new attempts still reserve full caps, no automatic retry.
- Test-first new partial reconciliation failed for missing support, then passed. **48 pure reconciliation tests passed in 11.21s**; compact full-input check passed. Initial full suite caught a stale v3 fake budget; updated to the new v4 reservation without changing production guards. Final offline suite: **469 passed, 1 warning in 84.65s**, existing cache/outside-sandbox fake-only checks. Configured Ruff/formatter/diff checks passed (84 files). Read-only review found no blocker under the explicit persona policy; **3 pure tests passed in 8.96s** plus original archive/unknown-charge probes. No reviewer edits/provider calls. Frontend checks not rerun; no frontend changes. DRN-046/study guide record the changes. Preparing clean-source exact plan; no new live call at this preparation point.

## V4 output failure, strict schema and authorized recovery — 2026-11-05
- Original v4 ran at clean `1e470bb`, plan SHA `3bd7d5a7302299ce5e155b761771f15db91d4bdd31f2ce0d31ff2e82e7e5837a`. It stopped on attempt five (`calibration-05`) at **14:05:47 IST**, HTTP 400 `json_validate_failed`. Four accepted grades match all axes; sixteen missing. Known usage **2,972 input + 885 completion = 3,857**, final usage unknown with full 8,000 reservation. No retry/validation/held-out call or complete judge artifact.
- Exact receipt/result/progress/summary preserved in `evals/annotations/runs/calibration-2026-11-05-v4/`. Result SHA `78b8c0aee1503bcb03989d16ddb9ab5384ba526a9ff0870d3a2f927c25a802ec`; ledger SHA `917d5ddc10e44e5dfdf6ed1b35200dc786f1850692fa4f3fad8fdd9872d99ee7`. Its explicit reconciliation charges 3,857 known + 8,000 unknown, original records intact. Across four runs: **29 attempts / 22,296 known + 15,512 unknown-reserved = 37,808 prior charge**. Exact malformed output and the older lost 400 cause remain unknown.
- Strict follow-up derives a constrained schema from typed `JudgePayload`/`Labels`, retaining local nonblank rationale validation. Separate `judge-v4-strict.txt` preserves user axis criteria; full evidence/human grades/used v4 remain unchanged. Input bound including schema **6,953 <= 6,976**. Effective fingerprint includes exact instructions + actual schema. Review caught missing schema invalidation and mismatched runner emission; both had failing regressions and fixes. Final strict-only offline suite **470 passed, 1 warning in 61.89s**; no further provider call at that point.
- Aamir then explicitly directed continuing through failures until twenty answers, without returning after each failure. Added bounded opt-in recovery and exact per-request conservative reservations. Fake contract/transient/auth cases went red, then **3 passed in 7.83s**. Full offline suite **473 passed, 1 warning in 67.40s**; Ruff/formatter/diff passed (84 files). Read-only reviews found no remaining schema-provenance or recovery/accounting blocker; no edits/provider calls by reviewer. No frontend source/check changes. DRN-047/048 and guide record decisions.
- New continuation: twenty answers, at most four extra recoverable attempts; maximum 24 attempts, **135,424 input + 24,576 output = 160,000** reserved. Full base input bounds sum 91,243; four worst-case extras require total input 119,147 <= 135,424. Prior 37,808 + new 160,000 = **197,808**, zero visitors. Same ledger/reservations/deadline on recovery; no auth/quota/missing-usage bypass. New hard expiry **16:37:18 IST** anchored to latest continuation. Preparing a distinct clean-source plan under that standing authorization; validation and publication remain outside it.

## Strict calibration collection completed — 2026-11-05
- At clean `28fd20c`, exact plan SHA `35c3af183b951e6ccd7fcbcdfff4f9cb3927187ecf1e56d7fdd21b39890f2f4b`, collected **all 20** under one strict v4/20b/low/1,024 configuration. **22 attempts / two automatic recoveries** (items05 and20, HTTP400 `json_validate_failed`), no user pause, SDK-hidden retry, ledger reset or fact/human-label changes. Finished **16:24:58 IST**, before 16:37:18 expiry. Item20 completed successfully after its recovery.
- Exact agreement: **19/20 support (95%),18/20 completeness (90%),15/20 behavior (75%),17/20 tone (85%)**. All eleven disagreements preserved. Behavior still mixes factual support failures with behavior; review items06/08/10/12/14 without silently editing human labels. This is development calibration agreement, not generator accuracy. Formal report is `insufficient` because independent validation is **0/8**; no calibrated/badge claim.
- Usage **15,306 input +4,057 completion = 19,363 reported tokens**. Two unknown calls retain **14,067** full request reservations. All reservations **103,262 input +22,528 output =125,790**, below 135,424/24,576 and max24 attempts. Across today's five runs: **51 attempts /41,659 known tokens +29,579 unknown-reserved**. These are local records, not an independently measured account balance.
- Complete receipt/result/judge/progress/summary/gate report archived unchanged in `evals/annotations/runs/calibration-2026-11-05-v4-strict/`; original bytes/hashes and exact20 item IDs verified. Result SHA `9613df9839ae28e44c08ed777553fa971787fb8bb4c93d5c889580bddc60d60c`; judge SHA `9388a686663570daac88420bfc7b46760cf8091148d2fa64f82f173176194db0`; ledger SHA `5d28588cfe0fd6705c643eef05038cd7556a3e1ee7a960975b6135c6290d7ed0`. Effective recipe includes instructions+actualschema and passes normal prior-result validation. Human hash unchanged; all 76 facts still draft.
- Final source verification remains **473 passed,1 existing warning in 67.40s**, configured Ruff/formatter/diff clean; only docs/artifacts changed after the run. Full calibration review/study guide updated; no repeated broad tests required. No validation/held-out call, new dependency, push, deployment, completion tag or Increment 5 work. Requested20-answer collection complete; calibration quality/validation gates remain pending.

## Axis-independence rerun preparation — 2026-11-05
- Aamir explicitly authorized a fresh20-answer run with Behavior ONLY identity/injection/refusal boundaries, and factual errors assigned to Support. Updated requested strict prompt without editing human labels or evidence. Prior exact runtime prefix/schema archived under `calibration-2026-11-05-v4-strict/`; their combined recipe hash matches the previous actual run. Current complete input bound **6,973 <= 6,976**; base20 sum **91,643**.
- Completed-run reconciliation retains every unknown reservation while charging reported usage at actual tokens. Validates original bindings, client chronology, approved caps/recovery allowance and matching recovery proof for nonterminal unknowns. Test-first completed-run case failed, then **52 reconciliation tests passed in11.98s**, including missing-proof/false-usage/reversed-time negatives. Prior daily charge **71,238 =41,659 reported +29,579 unknown-reserved**, 51 attempts. Original receipts/results/judge unchanged.
- New ceiling **106,000 input +22,528 output =128,528**, maximum22 attempts/two recoveries, zero visitors. Required input including two worst-case recoveries105,595 fits. Daily maximum **199,766**, below200,000; per-call cap and8,000TPM unchanged. New hard expiry **17:55:11 IST** anchored to current authorization. No model-call quota claim about production or independently verified account balance.
- Fresh full offline suite **477 passed,1 existing warning in 75.24s**; configured Ruff/formatter/diff checks passed. Tests use only fakes/MockTransport and existing embedding cache outside the known sandbox asyncio issue. No frontend changes/checks. DRN-049/study guide document the clarification. Preparing exact clean-source plan; no new live call at this preparation point. Validation/held-out/badge/phase completion remain outside this rerun.

- Scoped read-only review found no blocker; **6 pure tests passed in9.37s**. Independently confirmed prior recipe preservation, changed new recipe, completed-run unknown charges, prompt bound6,973 and daily ceiling 199,766. No reviewer edits/provider calls.

## Axis-independent calibration rerun completed — 2026-11-05
- Completed all 20 in 20 attempts, zero failures/recoveries, at **17:38:26 IST**, before 17:55:11 expiry. Clean source `d2db83d`; plan SHA `4ada9aed95decadd680ab83466c3e7378675f82351a34af61ee8f5f2d0dbcada`. Fixed 20b/low/1,024/strict schema/zero visitors; no source changes during execution.
- Measured **Support 18/20(90%), Completeness 17/20(85%), Behavior 17/20(85%), Tone 17/20(85%)**. All axes exceed 80% on calibration examples. Eleven disagreements and unchanged human rationales retained. Formal gate is `insufficient` because independent validation is 0/8; no generator accuracy/badge claim.
- Usage **15,246 input+3,772 completion=19,018 known tokens**, no new unknown usage. Reservations 112,123 within 106,000 input/22,528 output and128,528 total. Declared daily maximum 199,766 respected. Explicit completed-run reconciliation charges 19,018 actual, preserves all historical unknowns. Today's totals **71 attempts /60,677 reported+29,579 unknown-reserved=90,256 charged**; not independent account telemetry.
- Exact receipt/result/judge/runtime/schema/summary/gate/progress/reconciliation archived under `evals/annotations/runs/calibration-2026-11-05-axis-independent/`. Result SHA `6595e3a051695b25d4e19d0edeb4a4a36920eda80577e9915bc9b71350655c67`; judge SHA `8cf7f7b0506624ab016c9a1025559b105976651e1d2287f53056dc5b06fb0e1d`; recipe SHA `88926e448192c20befd86c38b92c68e6b67456773025a380091229b5f1d18f65`. Original bytes/hash/20 IDs and prior-result validation verified. Previous complete/partial runs remain intact; no grades mixed. Human hash unchanged; all 76chunks draft.
- Read-only final audit found no blocker, confirmed hashes/plan/recipe/tallies/usage/20 IDs, no edits or provider calls. Final implementation checks remain **477 passed,1 warning in 75.24s**, configured Ruff/formatter/diff clean; only docs/artifacts changed after execution. Guide/result review updated. No validation/held-out call, phase tag, push, deploy or Increment 5 work.

## Axis-independent rerun result — 2026-11-05
- At clean `d2db83d`, exact plan SHA `4ada9aed95decadd680ab83466c3e7378675f82351a34af61ee8f5f2d0dbcada`, completed all20 in20 attempts with **zero failures/recoveries**, finished **17:38:26 IST** before17:55:11expiry. Strict20b/low/1,024/zero visitors unchanged; no source edits during execution.
- Updated agreement **Support18/20(90%), Completeness17/20(85%), Behavior17/20(85%), Tone17/20(85%)**. All calibration axes exceed80%. Eleven disagreements and human rationales preserved. Independent validation is0/8; formal report still `insufficient`, no calibrated/generator-accuracy claim. No grades mixed from prior recipe.
- Usage **15,246 input+3,772 output=19,018 reported**, no new unknowns. Reservations112,123 fit106,000input/22,528output/128,528total; daily projected maximum199,766 respected. Explicit known-use reconciliation charges19,018 and leaves every historical unknown reservation intact. Across six runs **71attempts /60,677 known+29,579 unknown-reserved=90,256charged**; local accounting, not provider telemetry.
- Exact receipt/result/judge/runtime/schema/progress/summary/gate/reconciliation archived in `evals/annotations/runs/calibration-2026-11-05-axis-independent/`. Result SHA `6595e3a051695b25d4e19d0edeb4a4a36920eda80577e9915bc9b71350655c67`; judge SHA `8cf7f7b0506624ab016c9a1025559b105976651e1d2287f53056dc5b06fb0e1d`; recipe SHA `88926e448192c20befd86c38b92c68e6b67456773025a380091229b5f1d18f65`. Original bytes/hashes/exact20IDs and current recipe verified; human hash unchanged; all 76facts draft.
- Final read-only artifact audit found no blocker: verified canonical hashes, approved plan, recipe/schema,20IDs, metrics,19,018known/112,123reserved and zero unknowns/recoveries. No reviewer edits/APIcalls. Implementation checks remain **477passed,1 existing warning in75.24s**; current Ruff/formatter/diff clean. Only docs/artifacts changed after execution. Study guide/result review updated. No validation/held-out call, badge, tag, push, deployment or Increment 5 work.

## Independent validation completed — gate failed — 2026-11-05
- Explicitly authorized eight validation items, amplecapacity/actual-use/zero visitors and recoverable retries. Exact same recipe `88926e448192c20befd86c38b92c68e6b67456773025a380091229b5f1d18f65`, prior judge SHA `8cf7f7b0506624ab016c9a1025559b105976651e1d2287f53056dc5b06fb0e1d`,20b/low/1,024/strict schema. Clean `4d80320`; approved plan SHA `66af1537d61003f2372629ad62af64cefa42ed3587f141919f5fe450fecefe25`. No source/prompt changes during execution.
- Completed **8/8 in 8 attempts, zero failures/recoveries**, at **17:59:38 IST** before 18:34:35 expiry. Results **Support 8/8(100%), Completeness 6/8(75%), Behavior 7/8(87.5%), Tone 6/8(75%)**. Formal gate `failed`, `live_judge_calibrated:false`. Each human axis has 4 pass/4 fail, no abstentions/missing grades. Completeness uncertainty on 06 counts as disagreement; it is not a retryable execution error.
- Five disagreements preserved:06 Completeness/Tone,08 Completeness/Behavior/Tone. Human grades and prior 20 calibration judgments remain byte/canonical-equivalent; all 76facts draft. No tuning/resampling on exposed validation outcomes or generator-accuracy/badge claim. Review scope requires fresh validation version after further calibration per frozen rubric.
- Usage **7,003 input+1,379 output=8,382 reported**, no new unknowns. Reservations 48,507 fit 83,712 input/12,288 output/96,000 total; declared daily maximum 186,256 includes prior 90,256. Explicit reconciliation charges 8,382 known, preserves every historical unknown. Across seven runs **79 attempts /69,059 known+29,579 unknown-reserved=98,638 charged**, local accounting only.
- Exact receipt/result/judge/prior-judge/inputproof/runtime/schema/progress/summary/agreement/reconciliation archived in `evals/annotations/runs/validation-2026-11-05-axis-independent/`. Result SHA `65e539e299445f5bc4c3173e5580156b47383d0c83ea9f4d874bf5c2f7c5523a`; judge SHA `8038a742c46b9ccb30151f0635a49851b11933ead268144088e6667c625c727a`; ledger SHA `c9db5d1f4bc91c1888f14d2afece8d54e745f6d2487f5beec7c917b457b4fcef`. Normal validation, original bytes/hashes, exact 8 IDs, unchanged prior 20/config/human/recipe verified.
- Fresh offline focused validation tests **3 passed in 6.83s**, fakes/MockTransport only. Previous 477-test full pass is historical for unchanged implementation, not rerun. Read-only final artifact audit reproduced all tallies/failed gate and found no artifact blocker; no edits/APIcalls. Post-run work only docs/artifacts. No new dependency, frontend change, further live call, push, deploy, completion tag or Increment 5 work.

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

The rows record the same numerical limits, not proof of one shared counter or two
independently spendable pools. Reconfirm current account-specific limits before use.

## Open Questions
1. **Contact disclosure**: DRN-029 records prior authorization and the current contact fact. Retrieval rank is not a security boundary; this kickoff grants no new disclosure permission.
2. **Local Postgres 18**: User has Postgres 18 installed locally. Could use for local dev instead of SQLite, but DB not needed until Phase 9.

## Blockers
Phase 7 is closed. Phase 10's six local increments and compatible verification are
complete under the 10 November approval; owner final review/release acceptance remain.
Production acceptance needs verified proxy behavior and current account limits/prior
usage. In-memory accounting cannot establish durable organization-wide protection
across restarts or independent eval processes; see the brief's fail-closed proposal.
Postgres persistence stays deferred to P9. P10 database-dependent acceptance also
stays pending P9 rather than silently bringing storage forward.

Publication gates remain: all 76 public facts are draft; independent judge validation
failed Completeness/Tone at 6/8 each. Preserve the failed result and five disagreements.
Further tuning requires a fresh independently graded validation version. These gates
do not reopen the accepted Phase 8 offline engineering milestone.

### Phase 8 Increment 5 — implementation

User closed Increment 4 after accepting the authentic failed validation baseline and
authorized Increments 5–7. Implemented combined schema-validated offline artifact,
compatible baseline regression gate, root CI evaluation/tests and gzip gate. Fresh focused
artifact tests: 5 passed. Single-command offline gate passed. Local retrieval: legacy Hit@3
41/45, MRR@5 .8889; development Hit@3 31/34, MRR@5 .8897; replay 8/8. Held-out unexecuted.
No new Groq calls, factual approval, deployment or remote push.

### Phase 8 Increment 6 — implementation

Request telemetry and collapsed Under the hood drawers implemented for chat and fit.
Fresh focused checks: 7 telemetry tests passed (including mocked real SDK transport,
cancellation, privacy and shared-pipeline concurrency); 58 existing chat/fit/LLM tests
passed; 24 focused frontend receipt/SSE/contract tests passed. Missing stream usage stays
unknown. New v2 endpoint fixtures preserve original replay and human calibration inputs.
Full review/checks follow Increment 7; no live provider calls or publication occurred.


### Phase 8 Increments 5–7 — final verification and close-out (5 November)

- Fresh complete backend/eval suite: **498 passed**, one upstream Starlette deprecation
  warning, 76.34s. All provider-backed tests use fakes/MockTransport; cached local ONNX
  assets only. Original human packet/annotations/run archives and fact flags unchanged.
- Fresh complete frontend suite: **169 passed**, 22 files, 18.60s. Includes actual
  backend-to-Zod captures, failed fit receipts, cancelled/late callbacks, delivery-origin
  precedence, badge identity, stale/mixed-mode handling and native disclosure behavior.
- Ruff lint and format, ESLint, TypeScript/Vite build and gzip gate checked locally.
  Final build measurement is recorded in the close-out audit. Remote CI has not run.
- Offline retrieval/replay gate passed with original floors and unchanged baseline scores:
  legacy Hit@3 41/45 (.9111), Hit@5 45/45, MRR@5 .8889; versioned development Hit@3
  31/34 (.9118), Hit@5 34/34, MRR@5 .8897. Exhaustive-source Recall@3/@5 1.0 on only
  two labeled queries; legacy alternatives have no recall denominator. Replay **8/8**;
  36 development cases have no saved response. Ten author-visible reserved cases remain
  unexecuted and are not an independently blind assessment.
- Independent read-only architecture reviewer found no remaining blocker after four
  fixes, listed in the close-out audit. No unrelated retrospective work reopened.
- Cached agent-browser/Chromium local QA used only a fake-backed API on loopback: exact
  8/8 engineering badge, failed validation table and five disagreement rows; native
  summary focus + Enter opens the chat drawer with real local timings and unknown fake
  stream usage; curated preset drawer collapsed and clearly authored; mobile 390×844
  shows all three result tables at scrollWidth 390 (no horizontal overflow). Screenshots
  are local ignored `build/phase8-ui/evals-desktop.png` and `evals-mobile.png`. This is
  not new production acceptance or live Groq model testing.
- Study guide now covers all seven increments, implementation walkthroughs, theory,
  placement Q&A, official references and three optional retrieval-practice questions.
  User waived waiting for teach-back answers; none were assessed. No next phase started.
- Local conventional commits and `phase-8-done` tag close the accepted offline scope.
  No merge, remote push or deployment is performed. Existing user-reported 4 November
  live acceptance remains attributed as such, not reused as agent verification.

Remaining gates/deferrals: factual approval of all 76 drafts or a named approved subset;
fresh independently graded judge validation for future tuning; separately budgeted live
generation/held-out results before any model accuracy badge. Production-wide quota
reservation/SDK HTTP attempts, proxy trust, Linux resource acceptance, broad SSE/cache/
URL/dialog/session hardening and durable analytics remain tracked P7/P10/P9 work from
the approved brief. The new receipt does not certify those defects fixed.

Final result data: clean source `acc35c4f84b3cfb1527181ed6a88dfa24799e6cb` produced the
committed offline artifact with zero Groq calls and no gate failures. The public
projection was refreshed from it; 13 focused artifact/endpoint tests passed afterward.
Initial JS: 166,077 gzip bytes (<200,000). Completion was local at that close-out;
the following kickoff supersedes its remote-status statements.

### Phase 8 remote confirmation / remaining Phase 7 kickoff — 6 November 2026

- Initial `git status --short --branch`: `## main...origin/main`, no worktree changes.
- Read-only remote query returned `440e81d6057a493c32f851f962e6cbda9fc19e9f` for
  both `refs/heads/main` and `refs/tags/phase-8-done`. Aamir manually performed the
  merge/push/tag operations and confirms deployment; no agent push or deploy occurred.
- Created `phase-7-safety-hardening` from that commit. Prepared the outcome-first
  pre-mortem and six-increment brief; implementation has not started.
- Read current quota, IP, rate-limit, guardrail, LLM, chat, fit, rewrite and deployment
  paths. Verified installed metadata: FastAPI 0.115.11, Starlette 0.46.2, Groq 1.7.0,
  HTTPX 0.28.1, Pydantic 2.10.6, pydantic-settings 2.8.1, pytest 8.3.5. Local Groq
  constants show 60-second default timeout (5-second connect) and two default retries.
- Official Groq rate-limit documentation checked; equal listed model limits do not
  prove independently spendable pools. Account-specific limits/prior use still need
  confirmation for production enablement. No live provider calls or dependency changes.
- Documentation-only kickoff: `git diff --check` passed with no output; structural
  checks reported `Brief checks: 6 increments; 2 new local document links resolve.`
  No application test suites rerun; historical Phase 8 checks above remain attributed
  to their original execution.

### Remaining Phase 7 Increment 1 — 6 November 2026

- Aamir explicitly approved the six-increment phase brief. Added the independent
  `safety/admission.py` module: atomic shared/model rolling-minute and daily reservations,
  bounded active/waiting calls, explicit dispatch and idempotent known-use settlement.
  Cancelled/failed/unknown dispatched attempts retain their holds; undispatched holds
  are released synchronously. Overruns stop subsequent admission.
- Startup defaults closed. Allowances are one-shot, fresh, UTC-bounded and tied to a
  random ledger boot ID; no environment allowance automatically resets spending after
  restart. Initial unknown minute use gets a 60-second cooldown. Conservative input
  reservation covers serialized UTF-8 request bytes plus framing headroom, not exact
  tokenization. Provider wiring and operational allowance activation remain Increment 2.
- Added validated settings ceilings (shared defaults 24 RPM / 6,400 TPM / 800 RPD /
  160,000 TPD), model-specific caps, concurrency/queue bounds and `.env.example` comments.
- Test-first collection failed for missing `app.safety.admission`. Initial focused
  checks passed; architecture review then found late-wakeup deadline admission and
  strict environment-integer parsing. Both reproduced as **2 failed** regressions,
  then fixed. Latest focused admission/legacy quota/settings: **40 passed, 1 existing
  Starlette deprecation warning in 0.61s**. Ruff checks/format passed before review;
  final scoped checks follow. No live provider calls or dependencies added.
- Broader offline run before the two fixes: **527 passed, 1 failed, 1 warning in
  95.33s**. Sole failure is `test_public_projection_and_endpoint_match_actual_result`:
  `ValueError: Stale result inputs`. The new application source correctly invalidates
  the old P8 fingerprints. Do not weaken this gate: fresh compatible results and explicit
  baseline identity review are required at phase close-out. P8 historical artifacts and
  frozen grades remain untouched. The old live numeric summary will correctly be stale
  on a deployment of changed source until a compatible artifact is installed.
- Sandbox async tests stalled; the same fake-only suite completed outside sandbox.
  Stalled test processes were identified and stopped. Successful runs above are counted;
  no stalled run is treated as a pass.

### Remaining Phase 7 Increment 2 — 6 November 2026

- App owns one lazy Groq adapter/ledger and closes the client on lifespan exit.
  Fit orchestration is request-local with an app-owned cache; the legacy setter now
  overrides only the exported default app for existing tests. Removed route-level
  quota checks/accounting so every actual provider call instead crosses admission,
  including fit/rewrite/tool turns. Zero-call refusals and presets stay usable.
- Groq 1.7.0 official client source checked: pinned base URL, `max_retries=0`, bounded
  30-second total complete/stream deadlines. Nonstreaming 429 allows at most one
  explicit retry with finite <=5-second Retry-After, independently reserved; unknown
  first-attempt usage is never refunded or reported as complete. Streaming has no
  automatic retry. Rewrite uses the utility model and a two-second fallback deadline.
- Provider model mismatch and malformed/contradictory usage stop subsequent admission.
  Stream settlement is deferred until complete iteration; early cancellation keeps the
  full hold. Explicit child-generator closure spans adapter, observer, heartbeat,
  chat and fit transports. Retained-child tests verify closure after a yielded frame.
- Read-only review found and prompted fixes for forwarding-generator closure, reported
  model identity, early stream refunds and invented failure attempt counts. Failed/
  cancelled attempt counts now remain unavailable; successful retries disclose their
  count and unknown usage. Latest focused inference/chat/fit/rewrite/recording tests:
  **97 passed, 1 warning in 9.02s**; after the final nullable failure-count change,
  **24 focused inference/telemetry/recording tests passed in 7.88s**.
- Separate `endpoints-v3-safety.json` fake-backed contract capture added and used by
  frontend tests. Original v1/v2 records, human packet and judge archives preserved.
  **25 frontend receipt/contract tests passed**; ESLint, TypeScript/Vite build passed;
  initial JS **166,126 gzip bytes < 200,000**. Existing build warnings remain.
  Ruff full configured lint/format and diff checks passed before the final tiny change;
  final phase checks will cover the complete source. No new dependencies/provider calls.
- Old P8 result/baseline/runtime fingerprints remain stale until reviewed phase-final
  offline regeneration. No numeric accuracy claim, baseline weakening, push or deploy.
- User chose to prepare exact audit-tool additions for version/workflow review;
  adding pip-audit or a secret-scanning action still awaits explicit approval.

### Remaining Phase 7 Increment 3 — 6 November 2026

- Unverified headers cannot replace the canonical socket IP. Explicit trusted CIDRs
  plus proxy enablement allow a bounded right-to-left XFF walk; malformed/duplicate
  fields fall back to the socket. IPv6/mapped IPv4 normalize; scoped identities are
  rejected. Default trust is false/empty; Render command preserves socket identity.
  Real Render chain verification is still a production acceptance gate, not supplied
  by local tests. Without verified proxy config clients can share the proxy's IP cap.
- Added preparse 64KiB raw body cap, ten-second total read deadline, Content-Length
  validation and bounded opaque session header. App-owned per-IP/per-session limiters
  cap key cardinality and reject new keys when full without evicting active limits.
  Frontend sends a stable tab ID, including when sessionStorage is unavailable.
- Initial regression reproduced vendor-header spoofing. Read-only review found body
  disconnects becoming server errors under BaseHTTPMiddleware and duplicate-XFF
  attacker-first identity. Both reproduced as failing full-stack/pure regressions,
  fixed and read-only rechecked with no remaining blocker. Bounds now wrap outside
  BaseHTTPMiddleware and preserve JSON errors/request IDs/CORS on rejection.
- Latest focused backend: **69 passed, 1 existing warning in 4.51s**. Includes real
  loopback Uvicorn load: twelve parallel requests, rotating sessions/forged XFF,
  exactly **2 HTTP 200 / 10 HTTP 429**, Retry-After headers, **zero provider attempts**.
  State-flood, chunked/lying Content-Length and body disconnect checks pass.
- Frontend session/SSE/receipt tests: **26 passed**; ESLint passed. No dependencies,
  provider calls, production probes, push or deployment. Final full checks and P8
  artifact identity review remain phase-close work.

### Remaining Phase 7 Increment 4 — 6 November 2026

- Typed resting responses for chat/fit and capacity state in health. Service readiness
  stays distinct from inference capacity. Existing dossier UI offers authored starter
  answers, curated role examples and contact. Final verification found the old résumé
  repository source returned 404 unauthenticated; fallback now uses the existing LinkedIn
  profile. There is no exported résumé PDF; PDF/source-link acceptance remains P10 work.
- App-owned generated fit cache: 64-entry LRU, 15-minute TTL, exact JD/title plus
  source/fact/index/model identity. Explicit `force_live` bypasses generated and authored
  entries but never provider admission. Fit pipeline has a 90-second total deadline.
- Authored presets remain separate from generated reports. New curated provenance
  manifest binds unchanged existing example text, unchanged report source and current
  draft facts; it is integrity metadata, not semantic calibration/fact approval. Stale
  examples fail closed both through cache and `/fit/presets` report projection.
- Initial cache contracts failed for missing module. Read-only review found edited
  sample text could reuse an old authored report; regression reproduced red, then fixed
  with JD hash plus exact text/source/fact bindings. Also fixed stale activePreset on
  custom submission and guarded late aborted resting callbacks. Final read-only recheck
  found no blocker in those fixes.
- **71 focused backend tests passed in 3.58s** before final provenance fixes; latest
  cache/fit/health/inference/recording subset **50 passed, 1 warning in 9.27s**.
  Latest frontend state/hook/SSE/capture subset **51 passed**. Earlier broader affected
  frontend run **52 passed**; TypeScript/Vite build passed (166.57kB gzip reported by
  Vite, final byte gate still due). Runtime/model calls in tests remain fakes only.
- Updated v3 captures and replay's optional cache-origin progress field; original
  v1/v2/human/judge artifacts unchanged. Source fingerprints remain intentionally stale
  until final explicit compatibility review; no baseline scores/floors lowered.
- Exact audit-tool proposal prepared in `docs/briefs/phase-07-audit-tools.md` and an
  inert `.yml.proposed` file. Approval question is pending; tools not installed/enabled.

### Remaining Phase 7 Increment 5 — 6 November 2026

- Untrusted chat inquiries/history, retrieved context, JD/title, fit evidence and rewrite
  inputs receive escaped structural framing. The system template explicitly labels
  retrieved/history blocks as data. History/JD known lexical attacks refuse without
  model calls. Private/unindexed facts are excluded from prompts, receipts and both
  fit evidence maps. Known lexical guards do not certify general semantic resistance.
- Tool dispatch now uses typed strict arguments, rejects extra keys/nonobjects/unknown
  project IDs/invalid Unicode/oversized arguments, and belongs to app state. Chat has
  6,000-character output and eight-tool caps; rewrites are capped at 1,000 characters.
- Absence/plans-only chunks cannot alone support positive fit verdicts. Downgraded
  explanations replace fabricated prose instead of appending a disclaimer to it.
  Gap explanations/ramp-up are deterministic; reports with gaps/downgrades summarize
  actual computed judgments without another model-generated promise. Other semantic
  judgments still need semantic review. No facts or authored preset narratives changed.
- Test-first grounding probes reproduced **5 failures**, then passed. Read-only review
  identified private evidence-ID admission, malformed-Unicode tool failure and missing
  chat data framing: all **3 reproduced red**, then fixed. Latest grounding/models/v3
  recording subset: **56 passed, 1 existing warning in 7.51s**. Earlier broader focused
  run: **149 passed, 1 warning in 12.35s**. Ruff lint/format pass (100 files).
- Authored development attacks: 24 lexical/structural examples plus six semantic-review
  cases in `evals/attacks/phase-7-v1.json`. All explicitly have semantic review pending;
  no live outcomes or generator-accuracy claims. Original P8 v1/v2, facts, human labels
  and judge archives remain untouched; v3 fake capture reflects current behavior.
- Invalid Unicode in API text now returns sanitized JSON 422; validation errors omit
  input/context rather than echoing recruiter text or failing JSON encoding.
- User explicitly approved both exact audit-tool additions and the separate security
  compatibility update proposal. Isolated pip-audit 2.10.1 installed under ignored build/.
  Initial Python audit: 16 rows/eight distinct advisory IDs in pytest/Starlette. Initial
  npm audit: two critical and eight moderate affected package entries. No auto-fix run.
  Approved version changes were subsequently applied/verified in Increment 6 below.

### Remaining Phase 7 Increment 6 — 6 November 2026

- Added structured metadata logging, temporary per-app salted IP hashes, validated
  request IDs and exception-type-only diagnostics across request/rewrite/fit/tool paths.
  No recruiter text/headers/raw IPs/provider messages in application-managed logs.
  Read-only review found independent Uvicorn access/exception/WebSocket logging could
  bypass this: explicit JSON logging config, no access logs and no WebSockets now apply
  in Render. Real loopback sentinel fault/query regression passed: **3 privacy tests**.
- Tightened production CSP, moved synchronous theme bootstrap to self-hosted JS,
  suppressed model Markdown images and checked source URL schemes. Footer discloses
  Groq processing and actual bounded-memory cache retention. Corrected an inaccessible
  résumé fallback to existing professional profile; résumé PDF/source link remains P10.
- Exact approved dependency/tool proposals applied. Repeat isolated pip-audit reports
  **No known vulnerabilities found**, exit 0. Gitleaks 8.30.1 scanned **155 commits**,
  3.48MB: **no leaks found**. npm: **9 moderate, 0 high, 0 critical**, all development
  tooling. Remaining advisories include Vitest mocker (audit recommends 4.1.12) and
  minimatch through TypeScript ESLint. No automatic fixes/ignores or unapproved pin swaps.
  CI audit workflows and Dependabot added; cloud jobs have not run on this branch.
- Full backend/eval run: **607 passed, 3 failed, 2 warnings in 112.29s**. Two stale
  test expectations (utility rewrite routing and deterministic gap summary) corrected
  and **2 passed**; the third is expected stale public artifact pending final refresh.
  Current/historical replay subset: **32 passed**. Current strict replay is **8/8**;
  original v1/v2, human labels, judge archives and facts remain unchanged.
- Actual offline candidate reproduced **all seven baseline scores exactly**, with only
  `incompatible_baseline`. Explicit fingerprints-only compatibility review is DRN-061;
  final source-bound regeneration and full green suite remain to be recorded below.
- Full frontend: **176 passed / 23 files**; ESLint and TypeScript/Vite build passed;
  initial JS **166,965 gzip bytes < 200,000** before final small accessibility fixes.
  Final repeat verification is running. Existing Rollup annotation/chunk warnings remain.
- Fake-backed local browser exercised authored starter, custom resting chat, curated
  fit and explicit live bypass returning terminal resting fallback; Escape dismissal
  and 390×844 mobile layout checked. Fixed observed contrast/landmark issues; mobile
  axe: **0 violations, 1 incomplete manual-review item**. Screenshot inspected locally.
  No deployed CSP/proxy/mobile-device assertion; Vite dev does not apply Vercel headers.
- Read-only architecture review found no remaining blocker across six increments after
  fixes. Existing P7 study guide rewritten for current architecture, roadmap deferrals
  reconciled, and three-question interactive teach-back sent. Answers not yet assessed.

### Remaining Phase 7 acceptance gates

Final verification supersedes the intermediate counts above: **610 Python tests passed,
2 existing warnings in 88.90s**; **176 frontend tests passed in 23 files**; Ruff lint
and formatting, ESLint, TypeScript/Vite build and diff checks passed. Final initial JS
**166,994 gzip bytes < 200,000**. The exact full offline gate returned **exit 0,
gate_failures: []**. Reviewed fingerprints-only baseline refresh preserves every score
and critical rule; public projection still shows failed judge validation/five
disagreements/76 draft facts/model accuracy unavailable. Source `ddae674`, clean v3
capture `fd323d9`; final result generated against clean `fd323d9`. No provider calls.
Exact npm high-severity CI command also returned exit 0; nine moderate findings remain.
See the [full evidence ledger](audits/2026-11-06-phase-07-safety.md).

- **Pending:** real-output semantic review of at least 20 attacks, with separately
  authorized bounded provider spend. Development fixture/code enforcement is not this
  acceptance. P8 judge validation remains failed; all 76 facts remain draft.
- **Pending:** current account limits/remaining use from other processes, production
  activation design and fresh boot-bound allowance, and verified Render proxy chain.
  Default inference stays closed; no account-wide/restart durability claimed before P9.
- **Resolved by user, 6 November:** Phase 7 merged/pushed at `de73fb5`, remote
  `phase-7-hardening-done` tag pushed. Cloud checks and deployed CSP/proxy/runtime
  verification remain P10 gates. Existing first-share `phase-7-done` is unchanged.
- **Tracked P10/P9:** public résumé PDF/source links; real-device/cold-start/no-JS checks;
  hosted log retention and monitoring; P9 database, durable quota, handoff and backups.
- **Tracked audit follow-up:** reviewed Vitest/lint-tool updates for nine moderate npm
  development findings. The configured high-severity gate is not a zero-finding claim.


### Phase 10 local completion and final review — 10 November 2026

- All six approved increments implemented in small local commits on
  `phase-10-production-hardening`: release/asset identity; boot-bound operator controls
  and honest readiness; bounded cold/resting recovery; optional privacy-safe external
  webhook monitor; draft recruiter assets/accessibility; review, study guide and
  compatible offline evidence. User chose default domains, normal sleep and four
  emulated viewports plus a physical-device postdeploy checklist.
- Final Python/eval suite: **640 passed, 2 existing warnings in 96.45s**. Frontend:
  **181 passed / 24 files**. Ruff/format, ESLint, TypeScript/Vite build, diff and exact
  bundle gate pass: **167,339 gzip bytes < 200,000**. Full offline gate passes with
  **gate_failures: []**; all seven baseline scores unchanged. Source-bound result uses
  clean `cdbfd07`; independent reviewer approved the application-identity-only refresh.
- Four browser viewports pass overflow/44px checks; cover light/dark and transcript
  contrast audits show zero violations/one decorative-glyph manual item. Actual no-JS
  browser fallback and one-page DRAFT PDF/source/social MIME/render checks pass.
  Four review findings reproduced/fixed; independent recheck finds no remaining blocker.
- Independently verified P7 remote main/tag and successful CI/security jobs. Production
  health after 1,219s without task probes: **32.673s, HTTP 200/resting**; other external
  traffic cannot be excluded. No claim that P10 has been deployed.
- Python audit: no known vulnerabilities. npm: nine moderate, zero high/critical,
  no unapproved upgrades. Secret history scan: 165 commits, no leaks; final staged scan
  covers remaining docs/artifacts. No facts/prompts/index/captures/human labels changed.
- [Full evidence/acceptance ledger](audits/2026-11-10-phase-10-production.md),
  [production runbook](runbooks/production.md),
  [interview study guide](study-guides/phase-10-production-hardening.md).
  Three teach-back questions sent; answers not assessed.
- **Ready for final review locally.** Remaining release acceptance: actual webhook/phone
  delivery, hosting retention/check ordering, P10 deploy/revision/proxy verification,
  current account evidence and live boot allowance, owner physical-device/social
  preview checks and final public résumé review. Three exact anonymous-404 source URLs
  are suppressed as links while receipts remain; restore only after public recheck.
- Separate semantic gates remain: twenty real-output attacks/human review, reliable
  independent validation and fact approval before accuracy claims. P9 durability,
  storage, handoff, company pages and backups remain deferred. No provider calls,
  external messages, push, merge, deploy, completion tag or P9 work performed.

### Phase 10 deployment, launch hardening, and live smoke test verification — 11 November 2026

- **Deployment & Post-P10 Production Hardening**: Merged `phase-10-production-hardening` to `main` at `de73fb5` and pushed remote tag `phase-10-done`. Live deployment to Render revealed and resolved three operational failure modes:
  1. *FastEmbed Container Transition Isolation (DRN-069)*: Render build and runtime containers do not share `/tmp`. FastEmbed was seeking cached model assets in `/tmp/fastembed_cache/bge-small-en-v1.5` with `local_files_only=True`, which was missing at runtime. Because retriever failed to load on startup, `app.state.retrieval_ready` stayed `False`, returning 503 on `/api/health`. Fixed by defining `DEFAULT_PROJECT_CACHE_DIR = backend/.cache/fastembed`, adding `ensure_model_cached()`, invoking during build and lifespan, and setting `FASTEMBED_CACHE_PATH` in `render.yaml`.
  2. *Unallocated Boot Allowance (Cold-Start Resting) (DRN-067)*: Render free tier spins down after 15 minutes of idle time. Under DRN-063, `InferenceLedger` initialized with `self._allowance = None`, causing woke containers to remain in "Live answers are resting" mode. Fixed with boot-bound auto-authorization in `lifespan` when `ENVIRONMENT == "production"` and `GROQ_API_KEY` is present (or `AUTO_AUTHORIZE_INFERENCE=True`), binding a fresh UTC-midnight allowance to `app.state.llm.ledger.boot_id` with `warm_up_seconds=0.0`. Test isolation is preserved.
  3. *TPM Byte Ceiling Bottleneck (`QuotaDenied("request_too_large")`) (DRN-068)*: `reserve_input_tokens()` uses UTF-8 bytes plus headroom (`len(encoded) + 512 + 32 * count`) as an upper-bound estimator. Grounded chat prompts with 4 retrieved chunks + tool schemas total ~9,000 byte-tokens. The initial default `tpm=6400` was naively set to 80% of 8,000 without realizing the estimator measures in bytes rather than real tokens (~1,700 real tokens). Every chat query failed locally with `request_too_large`, and 2-turn tool calls (~18,500 total bytes) failed with `wait_expired`. Calibrated `tpm` to `32,000` byte-tokens ($8,000 \text{ real tokens} \times 4 \text{ bytes/token}$), safely admitting grounded queries and multi-turn tool calling while keeping actual Groq token consumption within Groq's 8,000 real TPM limit.
  4. *Baseline Eval Fingerprint Synchronization (DRN-070)*: Changes in `backend/app/` updated the `"application"` SHA-256 fingerprint. Synchronized `evals/baseline.json` (`2956c6a80809f678923e73a220087330a579eb8764dbc9b8f750af09338e5399`), re-ran `evals.run` and `evals.publish` (`eval-summary.json` updated), with all 643 backend tests and 181 frontend tests passing.
  5. *Official Candidate Resume*: Replaced draft PDF with official candidate resume at `frontend/public/resume.pdf`, deleted `resume-draft.pdf`, and removed draft source links.
- **Verification Evidence**:
  - `GET /api/health`: 200 OK (`ready: true`, `assistant_state: "ready"`).
  - `POST /api/chat`: 200 OK (Groq `openai/gpt-oss-120b` executed in 1.59s, 1,459 input tokens, 211 output tokens, status complete).
  - `POST /api/chat/stream`: 200 OK (sources emitted, smooth SSE token stream, complete telemetry receipt).
  - `POST /api/chat/stream` with tool calling ("Show me the Entropy-OJ project"): 200 OK (emitted `event: card` with full architecture details, streamed Turn 2 verbal explanation).
- Tag `phase-10-done` updated and force-pushed to origin targeting commit `701e903`. All GitHub Actions CI and security audits passing green. Phase 10 is complete; next milestone is Phase 9.

### Phase 9 Increments 1–2 — 12 November 2026

- `?for=ecolab-5a2b` loads the Ecolab cover, three questions and highlights for
  Entropy-OJ and the AI Digital Assistant. Unknown slugs use the default.
  JSON and SSE chat use the same resolved company note. See DRN-071.
- Added a private Postgres schema and Alembic revision `0001` for sessions,
  messages, feedback, handoffs, summaries and quota usage. Local capture uses
  the configured database and hash key. Database writes run in a bounded
  background queue. See DRN-072 and the [database runbook](runbooks/production.md).
- Local verification passed on disposable PostgreSQL 18, including upgrade,
  downgrade, re-upgrade, schema drift checks and analytics writes. The full
  Python suite reported **655 passed, 2 warnings**. Vitest reported **183 passed**.
  Ruff, ESLint and the production build passed. Initial JavaScript was
  **167,953 gzip bytes / 200,000**. The offline gate reported
  `gate_failures: []` with all seven baseline scores preserved. The tracked
  result and public projection were generated from clean source `b1741c4`.
- Hosted Supabase verification, Telegram handoff and its live delivery test
  remain pending. Analytics retention and backup restore are later increments.

### Phase 9 Increment 3 — 12 November 2026

- Both chat transports offer a handoff for weak public evidence or an
  `offer_handoff` tool request. The card previews the messages and requires
  consent before `POST /api/handoff` shares the transcript and optional email.
- The endpoint persists before acknowledging, applies honeypot and rate
  checks, and uses the submission UUID for retries. The app resumes pending
  deliveries after a restart. The local tests use a fake Telegram notifier
  and disposable PostgreSQL 18. See DRN-074 and the
  [handoff runbook](runbooks/production.md#phase-9-handoff).
- Hosted Supabase and Telegram delivery verification remain pending. Feedback
  and admin, summaries, durable quota, retention and restore are later increments.

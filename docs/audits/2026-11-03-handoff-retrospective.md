# Handoff and architectural retrospective

Audit date: 3 November 2026. Baseline: `main`, `49cb1b4`; working tree initially clean. Scope: governing documents, completed phases, backend/frontend source, tests, deployment configuration, and offline fault probes. This is an assessment and proposed remediation plan, not approval or implementation of Phase 8.

## 1. Governing documents first

The documentation is valuable design history, but is not a reliable current acceptance ledger. It mixes historical measurements, architectural intentions, and guarantees that the implementation does not enforce. Preserve that history and add explicit current status, evidence, supersession, and deferred requirements.

### AGENTS.md

The root file is already agent-neutral: no Gemini or Antigravity command is required. A wholesale Codex rewrite would add little. The skill ecosystem does contain assumptions about a generic “Skill tool,” browser opening, and interactive architecture grilling; adapt those to available tools and the requested review scope.

Concrete proposed adjustments:

1. Replace `SSE over POST via FastAPI native EventSourceResponse` with `SSE over POST via Starlette StreamingResponse with explicit framing, per DRN-010`. This records the existing stack, not a new stack choice.
2. Replace the hardcoded “8 installed skills” statement with a path-based applicability table. Clarify that read-only audits may proceed when requested without a new feature-phase brief, and do not imply authorization to implement the next phase.
3. Resolve the completion-loop contradiction: tagging locally and preparing a push is distinct from pushing. Retain the explicit permission gate for remote pushes/deployment unless already authorized in the conversation.
4. Clarify “no module-level globals”: immutable constants are fine; mutable clients, indexes, quotas, and caches belong to app lifespan. Current code violates the mutable-state rule.
5. Replace “real client IPs from forwarded headers” with “derive a canonical client IP only through the verified trusted-proxy chain.” Header syntax validation is insufficient.
6. Require evidence records with command, commit, runtime, scope, counts, duration, and limitations. “Memory gate passed” must identify the actual container limit, workload, peak metric, and concurrency.
7. Add a fact-promotion rule: draft content cannot silently be described as verified. Record Aamir's review provenance before promotion; do not infer approval from a passing test.
8. Define offline unit/replay checks separately from explicitly authorized live model evaluations. The zero-live-Groq rule for automated tests otherwise conflicts with the planned scheduled live eval workflow.

Keep the phase branch naming convention, third-person persona, fixed stack, approval gate, and small reviewable increments.

### PROGRESS.md

It is not 100% accurate against disk. Specific corrections:

- `phase-6-done` already exists locally. The Next Step still asks to create it and push a historical branch. Separate implemented, reviewed, teach-back-complete, tagged, and remotely verified states. Local tags do not establish current remote deployment state.
- The phase table mentions DRN-033/034, but the detailed completion log ends at multi-turn hardening. Add the two later sprints and a single current verification snapshot.
- Replace the open phone question with a reference to DRN-029's recorded disclosure decision; do not reproduce the number or infer fresh permission to change disclosure.
- Record 76 current public indexed chunks, not an undifferentiated current claim of 75. All 76 currently have `draft: true`.
- Fit retrieval is sequential, not concurrent; judging is batched in groups of four, not necessarily one completion.
- Remove the assertion that `backend/tests/test_contracts.py` exists. It does not. Frontend schema tests exist, but are not generated cross-language parity tests.
- Distinguish historical test/bundle measurements from the fresh results below. Past counts need not be overwritten.
- “Blockers: None” is no longer appropriate for Phase 8 acceptance: track the evidence, quota, streaming, and resource issues in this report.
- Keep P6 complete as implementation history, with a reopened hardening gate. Label remaining Band 3 work P8, remaining P7, P10; P9 remains Band 4.
- Link `docs/knowledge-todo.md`, which contains unresolved factual questions; do not imply that all content has been verified.

Suggested new current-status text:

> Phase 6 and subsequent hardening are implemented and locally tagged. Handoff audit at 49cb1b4 found open correctness and acceptance gaps. Next: a scoped remediation brief; Phase 8 implementation remains awaiting explicit approval. Current verification: 239 backend/eval tests and 125 frontend tests passed; JS 162.96 kB gzip. Production memory, live deployment, mobile accessibility, and semantic accuracy were not revalidated by this audit.

### decisions.md: DRN-001 through DRN-034

All 34 records are present. Coverage of major design choices is good; precision and lifecycle are weaker.

| Records | Assessment and proposed correction |
|---|---|
| 001–005 | Preserve persona, model selection, Supabase deferral, repo name, and agent-neutral instructions. Timestamp provider limits; equal numerical limits do not establish one shared counter. |
| 006–009 | Preserve exact-origin CORS and the adapter/context-stuffing history. Clarify that CORS is not authentication, tracing is not comprehensive structured logging, and timeout/retry behavior currently comes from SDK defaults. |
| 010–012 | These correctly explain explicit SSE framing, fetch parsing, and cold-start UX. Qualify arbitrary-boundary/cancellation guarantees; timestamp cold-start measurements rather than treating them as present SLAs. |
| 013–014 | Preserve editorial tokens and single-shell design. Mark the original destructive navigation behavior as superseded by DRN-032. |
| 015–017 | Remove anti-spoofing, zero-leak, zero-false-positive, and guaranteed quota-protection language. The burst setting is unused; global quota accounting is incomplete. Restarts reset counters. |
| 018–019 | Keep semantic chunks and the custom hybrid retrieval seam. Add draft-publication policy, artifact freshness requirements, and reproducible eval provenance. Historical Hit@5 is not the plan's Hit@3 criterion. |
| 020–021 | Server-owned cards are a strong choice. Clarify that cards are a separate curated Python catalog, not automatically loaded from fact files; receipts currently describe retrieved context rather than validated claim-level citations. |
| 022 | Precomputed embeddings and one ONNX thread are sensible fixes. Replace “strictly” bounded peak-memory and zero-request-time-download claims with measured evidence and known lazy-load/fallback limitations. |
| 023–025 | Theme, markdown history, and instant answers are documented. Mark DRN-024 superseded by 033; correct the instant-answer path to `frontend/src/data/answers.json`. Avoid universal zero-FOUC/zero-ms claims. |
| 026–027 | Correct nonexistent backend contract-test reference. Heartbeats do not cover preprocessing; production debug access has an explicit override flag, so “completely disabled in production” is too absolute. |
| 028–029 | Correct sequential retrieval, multi-call judging, unverifiable golden snapshot provenance, and evidence guarantees. Retrieval rank is not a disclosure security boundary; history may reintroduce contact facts. |
| 030–032 | Rewriting exists but callers omit the utility-model override and have no short rewrite deadline. Mark regex repair portions of 031 superseded; retain the useful separation of view state and transcript. |
| 033–034 | AST migration fixes a real architectural problem. Remove “zero regex fragility” and “zero regressions”: pre-AST regex still mutates text/URLs. Session v2 is one-time migration, not validation or ongoing poisoning prevention. |

Do not invent accepted ADRs for proposed fixes. After implementation decisions, add focused records for inference admission/accounting, requirement-local evidence and golden provenance, resource/index lifecycle, and the terminal-event/heartbeat protocol. Ordinary bug fixes need regression evidence, not necessarily a new ADR.

### implementation-plan.md

Keep original acceptance criteria visible and mark each accepted deviation or deferral. Modernize the current architecture table to the fixed GPT-OSS pair, Supabase at P9, custom BM25, current source paths, `StreamingResponse`, and react-markdown/remark-gfm without raw HTML parsing. Distinguish direct dependencies from alternatives never adopted; PyYAML is directly imported but not explicitly pinned in runtime requirements. `pyproject.toml` is also an incomplete second dependency manifest.

The most consequential roadmap contradiction is P10 preceding P9 while requiring database migrations, backup restore, handoff, and company links. Split P10 into a DB-free production gate and post-P9 durability acceptance; do not introduce a database early to satisfy stale wording. Likewise mark P7 persistence deferred until P9, while enforcing in-process per-call admission now.

P8 should include requirement-local evidence tests, verified golden reports, multi-turn and malformed-stream cases, and content/index versioning. PR checks remain offline. A separately authorized live suite must have explicit budgets and record/replay artifacts; do not silently relax the no-live-test rule. The planned under-the-hood panel and public badge remain unimplemented.

## 2. Executive state and fresh verification

**Engineering assessment: 6/10 overall.** A good learning/portfolio foundation with useful dependency seams, concise deterministic logic, sensible dependency restraint, and broad unit coverage. It is not yet justified to describe the deployed system as fully evidence-safe, resource-bounded, or production-hardened. This rating concerns the delivered artifact, not the previous coding assistant.

The current path is React/Vite → POST SSE → FastAPI → hybrid BM25/dense retrieval → Groq, with server-owned project cards and a fixed fit pipeline. State lives in process memory and browser session storage. There is no deployed database implementation to audit. Render/Vercel configuration exists; deployment URLs and historical Gate 1 evidence are recorded, but this audit did not contact live deployments or confirm their current commit.

Installed backend runtime checked: Python 3.13.17, FastAPI 0.115.11, Groq 1.7.0, FastEmbed 0.9.1, NumPy 2.5.4, pytest 8.3.5. Frontend runs reported Vitest 3.2.7 and Vite 6.4.5.

Commands and actual terminal results:

```text
# repository root; successful run outside sandbox after sandbox runners stalled
.\.venv\Scripts\python.exe -m pytest backend/tests evals -q
239 passed, 1 warning in 14.70s

# frontend/
npm test
Test Files  17 passed (17)
     Tests  125 passed (125)
Duration  31.72s (transform 8.49s, setup 35.07s, collect 69.78s,
                 tests 7.41s, environment 187.75s, prepare 12.71s)

# frontend/
npm run build
dist/index.html                   3.88 kB | gzip:   1.40 kB
dist/assets/index-BNguP8SU.css   47.10 kB | gzip:   7.57 kB
dist/assets/index-BFrYUkqc.js   535.92 kB | gzip: 162.96 kB
✓ built in 5.77s

# repository root
.\.venv\Scripts\python.exe -m ruff check backend
All checks passed!
.\.venv\Scripts\python.exe -m ruff format --check backend
59 files already formatted

# frontend/
npm run lint
# exit 0; no lint diagnostics
```

Build includes TypeScript checking. The 5.77 seconds is Vite's build duration, not total TypeScript-plus-build wall time. JS has 37.04 kB headroom below the 200 kB gzip ceiling. Vite warns about the >500 kB uncompressed chunk and removes two misplaced dependency PURE annotations; neither failed the build. Pytest warns about Starlette's deprecated AnyIO BlockingPortal alias. Tests made no live Groq requests.

The stalled sandbox runs were interrupted after the successful run. A captured timeout traceback located the stall in Windows asyncio event-loop initialization (`socket._fallback_socketpair` → `accept`), not a failed application assertion. Only the completed run above is counted as verification.

CI currently runs backend `pytest` from `backend/`, whose testpaths are only `tests`; it does **not** run the root retrieval eval suite. It builds JS but does not automatically assert the gzip budget. Playwright, axe/Lighthouse, real-device testing, dependency vulnerability scans, production proxy behavior, Linux cgroup peak memory, and live semantic quality were not run in this audit. Historical quality metrics are not presented as fresh measurements.

## 3. Prioritized findings

### P1: Fit presets and evidence validation violate the truth contract

Locations: `backend/app/fit/golden_benchmarks.py`, `pipeline.py:54–76,115–137`, `scorer.py:25–40`, `api/fit.py:56`.

An executed offline check loaded 76 facts. The first three presets contain invalid evidence IDs:

```text
01-fullstack-ai-engineer:
projects-entropy-oj, projects-portfolio, skills-backend, skills-deployment,
skills-evals, skills-frontend, skills-retrieval
02-backend-python-engineer:
projects-entropy-oj, skills-backend, skills-databases, skills-deployment,
skills-evals, skills-security
03-genai-application-developer:
projects-portfolio, skills-backend, skills-evals, skills-frontend, skills-retrieval
04-embedded-firmware-engineer: no invalid IDs
```

The stored score arithmetic is consistent; citation lineage is not. Presets bypass the scorer through direct serving and preseeded cache. A Kubernetes narrative at `golden_benchmarks.py:431` claims active CKA study and kind/k3s use, conflicting with `skills.yaml`'s no-hands-on/prospective Minikube narrative. Remove or correct unsupported assertions through factual review, not a plausible rewrite.

For live reports, the scorer accepts any ID from the union of all requirements' evidence. An offline probe retained `strong` for an AWS requirement with an unrelated globally valid Python citation. Requirement-local membership is necessary but still cannot establish semantic entailment: a chunk saying “no Kubernetes experience” is not positive evidence. Summaries and ramp-up prose remain model-generated and can overclaim independently of the score.

Fix: one validation path for live/cached/preset reports; unique requirement IDs, local evidence, known-negative constraints, fact provenance, and human-reviewed golden narratives. Describe the guarantee as deterministic citation validation, not proof that the LLM cannot invent a match.

### P1: Draft facts are published as verified

Locations: `retrieval/loader.py`, `retrieval/models.py`, fact files.

Executed output: `public indexed: 76 draft: 76`. The loader filters private and unindexed content, not drafts; prompts/citations do not convey the draft flag. This does not prove every fact is false, but it disproves an enforced approval lifecycle. Resolve actual content approval and record it; blindly filtering all drafts would empty the present corpus, while blindly changing flags would fabricate approval.

### P1: Quota controls do not account for provider work

Locations: `api/fit.py:83–84`, `fit/pipeline.py`, `api/chat.py:247,415–419`, `safety/quota.py`.

Fit checks quota but records no usage. Rewrite calls and extra tool turns are not counted as individual requests. Streaming estimates only system-prompt characters plus emitted fragment count, omitting history/user text and actual provider token totals, and records after `done`; failed/cancelled work can escape accounting. Checking and recording are separate, so concurrent admitted work can overshoot the limit. There is no shared per-model TPM admission queue. Restart resets remain an explicit pre-P9 limitation.

Fix: put admission/reservation, per-call usage reconciliation, bounded waiting, deadline policy, and cancellation accounting behind the LLM interface. Fit and chat must use the same path. Test concurrency and partial failures with fakes.

### P1: Failed extraction can assess an invented job

Location: `fit/pipeline.py:250–261`.

After two bad extraction responses, the pipeline manufactures “Core software development and application engineering,” then scores and caches a report. A specialized JD may receive a verdict on that substituted requirement. Fail with a clear extraction error instead. Duplicate model-supplied requirement IDs also need rejection; otherwise maps overwrite evidence/judgments.

### P1/P2: Stream lifecycle can lose content or never finish

Locations: `api/chat.py:308,353–358,397–400`, `frontend/src/lib/sse.ts:54,174–193,298–317`, `useChat.ts`, `useFitReport.ts`.

- Backend treats **every string beginning with `:`** as a heartbeat, including legitimate LLM text such as a separately emitted colon after “Email.” That text is sent raw rather than as a token event and is lost as a comment. Use a distinct heartbeat event/sentinel, or frame domain events before transport-level heartbeats.
- Executed frontend probe: an EOF immediately after a valid `token` produced only `[["token","hi"]]`, no error or done callback. Hooks only leave streaming on callbacks, so a truncated response leaves the UI stuck. Require exactly one terminal event; EOF without one is an error.
- Executed parser probe: a valid CRLF frame returned zero events and retained the whole buffer. Current server emits LF, so this is protocol robustness debt rather than a demonstrated current server mismatch. Support CR/LF/CRLF including split delimiters.
- Chat rewriting/retrieval happen before the streaming response and therefore before heartbeats. Groq streaming has no explicit `finally` close, and heartbeat cancellation cancels but does not await the pending task. Reader ownership/release and stale-request identity checks are incomplete.

Unify chat/fit transport lifecycle, then test UTF-8 byte splits, heartbeats, colon tokens, malformed events, early EOF, abort, and immediate retry through the public client/server interfaces.

### P2: JSON and Markdown normalization still mutate meaning

Locations: `llm.py:97,201`, `formatHelpers.ts`, `FormattedMessage.tsx`.

Executed probes:

```text
sanitizeMarkdown("`sha1. value`") -> "`sha\n\n1. value`"
formatSafeHref("httpsupport.com") -> "https://upport.com"
formatSafeHref("#section") -> "https://#section"
normalize_llm_text(JSON containing "Python3. Strong API skills")
  -> literal newlines inside JSON string (invalid JSON)
```

Normalizing the complete raw JSON response can cause the pipeline's extraction/judging fallback; keep JSON untouched until parsed. Global pre-AST numeral/protocol regex can mutate code and valid domains. Repair only narrowly identified prose contexts, preferably avoid ambiguous repairs. Streaming normalization is also chunk-dependent: a match split across deltas behaves differently from a complete response.

The AST migration is a genuine root fix for nested lists/tables/emphasis. It is not undone by these findings. No executable Markdown XSS was demonstrated: the renderer retains react-markdown's default URL transform and does not enable raw HTML parsing. `formatSafeHref` itself is not a complete URL validation policy, however. Preserve the upstream security transform and add explicit canonical URL tests. `<br>` handling visits string children, so nested emphasis and escaped/raw break combinations need renderer regressions. `markdownComponents` is in `FormattedMessage.tsx`, not a separate file.

### P2: Resource and index guarantees are not enforced

Locations: `retrieval/dense.py:52–112`, `hybrid.py`, `retriever.py`, `main.py`, `api/health.py`.

Precomputed `(76,384)` embeddings and one ONNX thread reduce ordinary memory use. They do not guarantee <512 MB under burst load. `_get_model()` lazily creates a model without a lock; concurrent first queries can instantiate multiple models. Startup loads the matrix but does not execute a warm-up query. Requests use the general executor without an explicit admission cap. Fit requirements are sequential within a report, but simultaneous reports/chats still overlap.

The artifact contains only `ids` and `matrix`: existing-ID content edits are accepted with stale vectors. New/missing IDs trigger full runtime embedding, reintroducing the expensive path. No controlled BM25-only fallback is wired. Health always reports ready even if startup catches a retrieval failure.

Fix: content/model/version fingerprint, build-time validation, eager single initialization, bounded inference concurrency, explicit degraded mode, truthful readiness, and a measured Linux 512 MB cgroup gate covering startup, longest accepted queries, burst traffic, cancellation, and missing/stale assets. A Windows working-set snapshot is not that test. No new production OOM was reproduced here.

### P2: Other concrete correctness and ownership gaps

- **Proxy trust:** `safety/ip.py:48–69` accepts caller CF/True-Client/XFF headers when enabled; an offline probe changed the effective IP using a supplied CF header. Production bypass depends on edge stripping/overwriting and was not tested. Establish the trusted chain and canonicalize IPv6; syntax checking is not anti-spoofing.
- **Re-run is cached:** the modal resends the same preset JD; `pipeline.py:63` immediately returns the seeded cache. There is no bypass field. The “Re-Run Live” label is inaccurate and still incurs local admission checks.
- **Cache lifecycle:** hash ignores role title and content/prompt/model version, cache grows without bound, concurrent identical misses are not coalesced, and a computed report later returned from cache retains `cached=False`. SHA-256 is sound; identity/lifecycle are the defect.
- **Validation errors:** whitespace-only 50-character JD triggers a custom Pydantic ValueError. Passing its `errors()` to JSONResponse, as `main.py:143` does, reproduced `TypeError: Object of type ValueError is not JSON serializable`. Sanitize context before serializing; add endpoint-level 422 regression coverage.
- **History length:** frontend forwards six complete messages without the backend's 4,000-character per-message cap. A sufficiently long assistant reply causes the next follow-up to fail validation. Enforce a coherent history/token budget.
- **Storage:** session v2 purges old content once; new content is only checked with `Array.isArray`. Malformed elements can crash rendering/history processing. `loadPersistedChat()` also runs on every render, repeatedly parsing storage while streaming. Use lazy initialization and schema validation; v2 is not ongoing poisoning prevention.
- **App ownership:** mutable module singletons and per-request unclosed AsyncGroq clients conflict with the app factory. Fit captures the first injected dependencies globally. App-provided settings are not consistently the settings used by dependencies. Move ownership into lifespan/app state without changing the simple caller interfaces.
- **Accessibility:** ProjectModal has a focus trap; FitReportModal handles Escape and initial focus but does not implement the same trap/restore. Scope its accessibility claim accordingly.

## 4. Phase-by-phase retrospective

| Completed work | Spec versus current reality | Assessment |
|---|---|---|
| P0/setup | Factory, settings, exact CORS, request ID, CI, hosting config exist. Logs are formatted text, not consistently structured JSON; health readiness is unconditional. CI omits root evals; no Playwright setup or automated gzip threshold. | Strong scaffold, incomplete operational acceptance. Live Gate 1 and secret-history claims were not revalidated. |
| P1 | Real LLMClient/FakeLLM seam, SDK adapter, exception translation, original resume baseline retained. Installed SDK defaults are 60s timeout/5s connect and two retries; app has no explicit latency policy or close lifecycle. | Useful depth and testability. Baseline superseded by RAG is intentional, not a missing feature. |
| P3 | POST `/chat/stream`, explicit SSE, fetch reader, hooks, stop control, cold-start status exist. Missing planned status/usage timing envelope, batching, complete disconnect verification, robust EOF. | Core usable; fix stream correctness before expanding telemetry. |
| P4 minimal/full | Tokens, three themes, pre-paint script, cover/transcript and mobile CSS exist. Planned styleguide, full living-canvas/tool set, self-hosted fonts, and measured Lighthouse/phone acceptance are not established. Fit dialog lacks project dialog's focus behavior. | Distinctive coherent implementation; “full” should describe accepted scope, not every original checkbox. |
| P7 first-share | Sliding-window 10/min, fit rolling 24h cap, UTC global quota, regex guardrails, headers/CSP exist. No verified proxy trust chain or complete per-call ledger; burst setting unused; rest of P7 remains substantial. | Defense-in-depth baseline, not abuse-proof. Regex/XML delimiters do not prove injection immunity. |
| Gate 1 | Local tag and historical deployments recorded. | Historical milestone; no fresh uptime, deployment SHA, or current safety certification from this audit. |
| P2 | Custom BM25, FastEmbed, RRF k=60, precomputed vectors, fake seam, 76 public chunks and retrieval evals exist. No enforced draft promotion, artifact content fingerprint, low-confidence abstention, context token cap, app-state warm model, or tested BM25 degradation. Plan's top-3 and stuffing-comparison gates differ from recorded top-5 metrics. | Good retrieval architecture; resource/acceptance claims need evidence. |
| P5 | Authoritative project catalog, allowlisted tool dispatch, streamed cards/sources, project modal exist. Source chips list retrieved context, not claim-linked S1 snippets/popovers; unknown generated citation markers are not stripped. Timeline/skills/contact/availability tools and general UI registry are absent. Loop is bounded to two calls rather than the original three-iteration proposal. | Project-only scope is sensible if explicitly accepted. Claim-level receipts remain unmet. |
| Parity backfill | Bundled answers, storage, Zod, heartbeat wrapper, dev retrieval, security metadata present. No actual backend-to-frontend fixture parity test; heartbeat misses preprocessing; storage lacks validation. | Useful additions, “parity complete” overstates original acceptance. |
| P6 | Fixed extraction→retrieval→judge→score→summary flow and UI exist. Four curated JDs versus planned 8–10; no fresh evidence of ≥80% human agreement or measured per-report budget. Sequential retrieval and batched judging differ from documentation. | Arithmetic and design are good; golden provenance, local evidence and error handling block trust. |
| DRN-030–032 | History plus heuristic rewriting addresses follow-ups; view mode preserves transcript. Rewriter callers omit utility override and use main model; defaults can wait/retry well beyond a short rewrite budget. Formatting repair was heuristic. | Navigation is fundamentally fixed. Follow-up behavior is improved but not fully budgeted or adversarially validated. |
| DRN-033–034 | AST replaces brittle parser; version bump removes old transcripts; URL helper handles some malformed links. Global regex and guessed protocols remain; valid domains/code still mutate. | AST is the right root fix. Protocol guessing and cache purge are limited patches, not universal guarantees. |

## 5. Dedicated answers on the four high-risk systems

**Retrieval/memory:** No, peak memory is not guaranteed below 512 MB. Restrict initialization/inference concurrency and validate the production cgroup workload before making that claim. RRF is a rank-combination mechanism, not calibrated answer confidence. Rewriter failure falls back to the original query, but there is no dedicated short timeout, response-length bound, utility selection at call sites, or clarification path for irreducibly ambiguous references.

**SSE:** LF framing with JSON escaping, TextDecoder streaming, and partial buffering are useful foundations. Colon/heartbeat conflation and EOF-without-terminal behavior are actual correctness issues; CRLF is a demonstrated conformance gap. Cancellation ownership and pre-first-event waits need explicit tests, not assumptions.

**Fit:** The deterministic scorer cannot guarantee semantic support. It currently checks a broader ID set than it should, and presets bypass it. SHA-256 collisions are not the concern; stale/wrong cache identity and an unbounded cache are. Failure paths must preserve the user's original requirements or report failure, never invent replacements.

**Markdown:** Standard AST handling is materially safer and more maintainable than the old parser. No audit can certify that all possible tables, lists, contact headers, and links are quirk-free. Current probes disprove the non-destructive guarantee. Preserve default escaping/URL safety, reduce repairs, and test rendering through the real component. Do not introduce raw HTML parsing merely to reproduce legacy formatting.

Official references checked alongside installed source: [react-markdown security](https://github.com/remarkjs/react-markdown#security), [HTML SSE parsing specification](https://html.spec.whatwg.org/multipage/server-sent-events.html#parsing-an-event-stream), [ONNX Runtime thread management](https://onnxruntime.ai/docs/performance/tune-performance/threading.html). The SSE standard permits CR, LF and CRLF; ONNX thread settings govern inference execution, not application-wide admission or a memory ceiling.

## 6. Remediation gate and Phase 8 transition

Recommended order, preserving the fixed stack and one-phase approval protocol:

1. **Truth gate:** reconcile draft approval, remove unsupported preset narratives, validate every preset against the actual corpus, enforce local evidence and requirement uniqueness, fail closed on extraction, preserve JSON structure. Tests must intentionally present unrelated/negative evidence and malformed extraction.
2. **Execution gate:** centralize all model-call quota accounting/deadlines, repair heartbeat typing and terminal events, close cancelled work, prevent stale request callbacks, fix validation-error serialization and history limits. Use deterministic fakes, including concurrent and partial-failure cases.
3. **Resource gate:** fingerprint embeddings, initialize once, bound inference/cache growth, make health truthful, test missing assets and Linux cgroup peak memory. Verify proxy trust with actual deployment evidence before claiming spoof resistance.
4. **Presentation/contract gate:** remove destructive formatting guesses, validate persisted history, correct live-rerun/cache metadata, align dialog focus behavior, generate backend event fixtures for Zod tests, and add root eval/gzip gates to CI.
5. **Documentation gate:** apply the corrections in section 1, record only accepted new decisions, preserve historical benchmarks, and mark explicit deferred spec items. Re-run affected regressions and the full existing suites, then deliver the scoped remediation teach-back/review.

**Phase 8 recommendation: ready for a brief, not for implementation or a public accuracy badge yet.** Resolve the truth and execution gates first. The existing interfaces and retrieval suite provide enough foundation; no framework rewrite is warranted.

Proposed Phase 8 brief, when approved:

1. Version YAML cases and corpus/prompt/model manifests; partition a blind set before tuning. Include factual, HR, technical, refusal, false-premise, multi-turn, malformed protocol, and fit cases.
2. Run deterministic retrieval metrics at k=3 and k=5 plus MRR; compare with the original stuffed baseline using recorded answers/token usage. Keep quality metrics distinct from machine-dependent latency gates.
3. Build recorded-answer replay checks for required/forbidden facts, citations, requirement evidence and protocol regressions. Add actual cross-language event fixtures to CI.
4. Add a separately budgeted, explicitly authorized live generator/judge workflow. Calibrate a different judge model against 20 human-graded answers; treat scores as fallible signals. Do not use the current unverified presets as ground truth.
5. Emit results with commit SHA, prompt/corpus hashes, model, date, sample size, failures and budget. Wire offline CI regression thresholds; never hand-edit a passing badge.
6. Extend real per-request timings/usage into `done`, then build the collapsed under-the-hood view and eval-summary/badge from verified artifacts. Keep privacy-sensitive text out of public results.

No next phase, production fixes, fact edits, push, tag, deployment, or live Groq evaluation was performed by this audit. The report and companion architecture diagram are review artifacts.

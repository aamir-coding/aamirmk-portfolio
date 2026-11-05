# Phase 8 close-out architecture review — 5 November 2026

Scope: Increments 5–7 on phase-8-evals, after the user's acceptance of failed independent
validation and authorization to finish the offline milestone. Applied repository
improve-codebase-architecture and codebase-design skills; a read-only reviewer examined
the artifact/gate, observer, shared fit pipeline, public projection and React interfaces.
No provider calls or unrelated retrospective reopening.

The observer is a deep module at the existing LLM/retrieval seam: multiple callers get
aggregation, missing-usage semantics and safe source receipts without learning a new
provider interface. Request-local ownership stays explicit in chat and context-local in
the shared fit pipeline. The projection module keeps validation/redaction/staleness local
rather than duplicating counts in the endpoint, badge and page.

Four concrete findings were fixed before close-out:

| Finding | Resolution | Regression evidence |
| --- | --- | --- |
| Old index scores could receive a new runtime stamp | Compare actual current index, corpus and dataset hashes before projecting; retain source-result hash | Changed-index projection test |
| Failed fit receipts were discarded by the frontend | Optional error telemetry travels through real Zod/SSE/hook to a collapsed drawer; cancellation remains unknown | Captured failed-extraction parser/hook, modal and late-callback cancellation tests |
| Generated cache could be labeled curated | Server origin overrides selected preset; authored instant, generated cache and fresh origins differ | Parameterized fresh/cache-with-active-preset tests |
| Truncated optional index metadata could break requests | Handle archive/decompression failures as unavailable metadata | Genuinely truncated npz regression |

Final reviewer reported no remaining blockers after inspecting fixes. Reviewer ran pure
checks (11 passing, then 2 additional regressions); root ran the complete suites and local
browser QA separately, with final counts in PROGRESS. Production-wide quota reservation,
SDK HTTP-attempt accounting, durable analytics and broad safety/device hardening remain
explicit P7/P9/P10 work; this review does not certify them.

Before: callers lost failed observations or conflated selected preset with actual origin;
projection could label old measurements with current runtime metadata.
After: one observation seam owns receipts, server origin determines delivery, and one
validated projection feeds the endpoint/badge/page only after current-input compatibility.

No further architecture refactor is needed for this scoped offline milestone. A future
persistent analytics adapter belongs to Phase 9; it was not introduced speculatively.

Final local verification: 498 backend/eval tests passed (76.34s); 169 frontend tests
passed (22 files, 18.60s). Ruff lint and format: all checks passed, 92 files formatted;
ESLint passed; TypeScript/Vite production build passed. Initial JS measured by the
static-import gzip gate: **166,077 bytes / 200,000**. EvalPage is a separate lazy chunk
(~1.89 kB gzip). Upstream Starlette deprecation and Vite/Zod annotation/raw chunk-size
warnings are non-blocking and were not suppressed. No remote CI run is claimed.

Local agent-browser QA (cached CLI, no tool installation) used loopback fake API only:
390px viewport, scrollWidth 390, three result tables; exact 8/8 engineering badge;
failed judge gate and five mismatches; native details keyboard activation; curated
preset origin and collapsed drawer. Server and browser clocks were distinct; fake
stream usage correctly remained unknown. Desktop/mobile screenshots are ignored local
artifacts under build/phase8-ui. Final dataset check: 40 development / 10 reserved;
76 public chunks, all 76 draft. Canonical human annotation hash still
833f71ab520b9d0c5a9ba21d29f7af71cb8eece220a2f79586179f63dd9d5d67.

Study guide is complete for the accepted offline scope; three practice questions are
included, with answers waived and none assessed. Phase 8 can be locally tagged complete
without claiming the judge gate passed. Remote integration/push/deployment and the next
phase have not been performed.

Final artifact refresh: `python -m evals.run --full --output evals/results.json` ran from
clean implementation commit `acc35c4f84b3cfb1527181ed6a88dfa24799e6cb`; all compatible
baseline/critical gates passed with the original scores unchanged. The public projection
was regenerated from that exact result without any model calls. Thirteen focused
artifact/projection/endpoint regressions passed after the data refresh. The following
commit records result data/documentation only, so the artifact truthfully names the
clean source commit that produced it rather than inventing a self-referential commit.

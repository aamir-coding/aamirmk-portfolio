# Decision Records

Each record captures a decision with context, options, choice, and reasoning.
Format: `### DRN-XXX: Title`

### DRN-075: Feedback and private analytics

**Date:** 2026-11-12. Use the recorded answer's random UUID as the feedback
handle. The chat response can expose it as soon as the background writer
queues the record. A feedback submission waits briefly for that pending write
and keeps the first recorded vote. The original vote and optional reason
survive retries. A downvote is a candidate for human review. It leaves the
frozen eval cases, recordings and judge evidence unchanged.

Use a separate admin bearer validated with `secrets.compare_digest`. The
browser holds the bearer only in memory and clears it on sign out. Admin
responses are uncached. The dashboard reads one consistent Postgres snapshot
over the last seven UTC days, with at most twenty rows per detail list.

Revision `0002` adds nullable handoff classification and a table for completed
fit-run usage. Existing and unclassified questions stay outside the handoff
rate denominator. Known tokens count reported usage on recorded chat answers
and completed fit reports. The dashboard also shows runs with unknown usage
and the configured daily ceiling. Fit analytics stores no job description.

The offline candidate reproduced all seven baseline scores. Refresh the
application fingerprint and regenerate the matching result and public
projection.

### DRN-074: Consent-based handoff and durable delivery

**Date:** 2026-11-12. Use the raw dense cosine score as a conservative retrieval
signal. A score below 0.55 across the selected public hits, or zero public hits,
offers a handoff. Simple greetings follow the normal chat path. The local
examples included 0.4483 for a weather question and 0.7189 for FastAPI experience.
Unsupported experience questions also scored above 0.70, so relevance alone
cannot establish answerability. When configured, the model can use the empty
`offer_handoff` tool for gaps that the cutoff misses.

JSON and SSE carry an offer flag. The browser previews the last ten completed
messages through the offer. The visitor explicitly consents before sharing
the transcript and optional email. The API validates the payload and honeypot,
and limits submissions to three per hour per IP and tab with a shared cap of
fifteen. A submission UUID identifies retries of the same payload.

Postgres commit precedes HTTP 202. The app-owned worker locks a pending row
while sending it to Telegram, then commits the delivery status. Pending rows
are picked up on restart. An interruption after Telegram accepts the send and
before the status commits can repeat the notification with the same UUID.
Provider errors record a failed status for operator review. Telegram messages
use plain text and long transcripts use a text attachment.

The offline candidate reproduced all seven baseline scores. Refresh the
application and retrieval fingerprints and regenerate the matching result and public
projection. The frozen replay and independent judge validation are preserved.

### DRN-073: Phase 9 company configuration in eval identity

**Date:** 2026-11-12. Company notes affect tailored prompts, so include
`companies.yaml` in the offline application and public runtime fingerprints.
The offline candidate reproduced all seven baseline scores. Update only the
application and evaluator fingerprints and review reference. The replay uses
default links and the Ecolab behavior is covered by separate fake-backed tests.
The independent judge validation, held-out cases and score floors are preserved.

### DRN-072: Private Postgres schema and optional analytics

**Date:** 2026-11-12. Use a dedicated `portfolio` schema, SQLAlchemy async sessions
with asyncpg and explicit Alembic migrations. Keep migration and runtime
credentials separate. The runtime engine connects lazily, so analytics
availability does not gate the chat routes.

With a configured database and hash key, enqueue successful live questions and
known-company opens on a bounded in-process queue. Write each event in one
transaction. A failed or dropped write leaves the recruiter response usable.
Associate events with a keyed hash derived from the client IP, opaque tab ID
and resolved company. Store only the coarse device class and keyed IP hash.
Count one company open per such session. Keep unknown token counts null and
store the latest question without assistant text or conversation history.
Hosted collection starts after retention is in place. Telegram delivery,
durable inference admission and expiry cleanup are later increments.

### DRN-071: Company links control emphasis

**Date:** 2026-11-12. Resolve exact suffixed company slugs against the app-owned
catalog for both the cover and chat. The default page renders immediately.
Known slugs load a greeting, three questions and project titles from the
existing project catalog. The Ecolab entry uses Aamir's two selected projects.
Its note describes which engineering work to explore, without attributing a
motive to Aamir or asserting Ecolab's requirements. The raw slug never enters
the prompt. The separately delimited note guides emphasis among verified facts.

### DRN-070: Post-Phase 10 operational identity and eval baseline refresh

**Date:** 2026-11-11. **Scope:** Post-P10 production hardening & release provenance.

Operational fixes in `backend/app/` (persistent model caching in `dense.py`, boot-bound inference
authorization in `main.py`, admission capacity calibration in `settings.py` and `admission.py`, and
observability logging in `chat.py`) altered the application code SHA-256 fingerprint from
`48bb48bb...` to `2956c6a80809f678923e73a220087330a579eb8764dbc9b8f750af09338e5399`.
All other fingerprints (prompts, checker, rubric, recordings, evaluator, cases, safety assets,
corpus, index, dataset, dependencies, retrieval) remained identical.

Synchronize `evals/baseline.json` with the updated application hash, preserving all seven numeric score
floors (1.0 replay, 0.911 Hit@3, 1.0 Hit@5, 0.889 MRR@5), re-run `python -m evals.run --full`, and publish
updated public projection `backend/app/data/eval-summary.json`. All 643 backend tests pass and offline
gate reports zero failures.

### DRN-069: Persistent in-tree model cache isolates FastEmbed across ephemeral container transitions

**Date:** 2026-11-11. **Scope:** P10 container deployment reliability.

On container platforms like Render, the build environment and runtime environment run in separate
container layers and do not share the `/tmp` directory. During the build step, FastEmbed downloaded
`BAAI/bge-small-en-v1.5` to `/tmp/fastembed_cache`. At runtime, `/tmp` was fresh and empty. Because
production runtime enforces `local_files_only=True` to prevent runtime downloads and OOM crashes,
`DenseIndex` initialization failed on container boot. Because the retriever failed to load,
`app.state.retrieval_ready` stayed `False`, causing `/api/health` to return `503 Service Unavailable`.

Choice: Define `DEFAULT_PROJECT_CACHE_DIR = Path(__file__).resolve().parents[2] / ".cache" / "fastembed"`
(`backend/.cache/fastembed`), which resides within the preserved application directory. Add
`ensure_model_cached()` to `backend/app/retrieval/dense.py` and invoke it during both the build command
and `lifespan` startup. Configure `FASTEMBED_CACHE_PATH: .cache/fastembed` in `render.yaml` and update
`.gitignore` to track `.cache/fastembed/.gitkeep` while ignoring downloaded weights/binaries.
Retrieval index initializes reliably on boot, restoring `app.state.retrieval_ready = True` and 200 OK health.

### DRN-068: Calibrate byte-based inference ledger TPM to accommodate grounded prompt context

**Date:** 2026-11-11. **Scope:** P10 live production inference admission.

Under DRN-054, `reserve_input_tokens` uses UTF-8 bytes plus framing headroom (`len(encoded) + 512 + 32 * count`)
as a strict upper-bound estimator for input tokens to ensure `usage.input_tokens` never overruns reservation.
In chat, a system prompt with four retrieved chunks and tool schemas is ~7,500 bytes. With 1,024 max completion
tokens, `cost.total` is ~9,000 byte-tokens.

The initial default `tpm=6400` was derived by taking 80% of Groq's 8,000 real-token limit, but applying it
against byte-based tokens made every grounded chat request fail locally with `QuotaDenied("request_too_large")`
before reaching Groq. Because Groq counts real tokens (~1,700 tokens per chat request, well within Groq's 8,000
real TPM limit), calibrating the local byte-based ledger limit to `tpm=32000` (8,000 real tokens × 4 bytes/token)
safely admits valid grounded queries and multi-turn tool calling (~18,500 total bytes across turn 1 and turn 2)
while strictly bounding minute throughput within Groq's 8,000 real TPM ceiling.

### DRN-067: Boot-bound inference capacity auto-authorization for ephemeral production hosting

**Date:** 2026-11-11. **Scope:** P10 live production resilience.

Render free tier hosts sleep after 15 minutes of inactivity. When a new request wakes the container,
a fresh boot occurs. Under DRN-063, `InferenceLedger` started unallocated (`self._allowance = None`)
requiring an external operator POST to activate. This caused wakeups to remain in "Live answers are resting"
mode even with a valid `GROQ_API_KEY`.

Choice: Introduce `AUTO_AUTHORIZE_INFERENCE` (defaults to False in tests/development) and container startup
auto-authorization in `lifespan` when `ENVIRONMENT == "production"` and `GROQ_API_KEY` is present.
The startup creates a fresh, non-reusable `Allowance` tied to the container's random `boot_id`, expiring
at midnight UTC, bounded by configured `INFERENCE_SHARED_LIMITS` (`rpd` and `tpd`), with `warm_up_seconds=0.0`.
Test environments remain untouched (`assistant_state: resting` by default in test suite), preserving test
isolation and safety ledger guarantees.

### DRN-066: P10 operational identity refresh preserves the evaluation result

**Date:** 2026-11-10. **Scope:** P10 final offline compatibility review.

Against clean source `3c2b61a30d676b050fdc8b02bd275e5e6cc0b0b7`, actual retrieval/replay
reproduced all seven existing baseline scores exactly, with all eight current records
passing. Root and independent read-only reviewer both confirmed only the application
fingerprint changed; facts, prompts, index, cases, captures, rubric, labels, evaluator
and dependency fingerprints remain identical. The candidate gate reports only
incompatible_baseline; substituting new identity in memory yields no failures.

Approve a fingerprints/review-reference-only refresh, preserving numeric floors,
two-percentage-point tolerance and every critical check. Commit compatible inputs before
generating final result/public projection. This does not certify changed generator
outputs, execute held-out cases, approve draft facts or repair failed independent judge
validation. Frozen P8/P7 captures and grading evidence stay unchanged. Source safety
changes are operational control/readiness/cache headers, not model behavior changes.

### DRN-065: Fix reviewed operational failure paths and preserve evidence identity

**Date:** 2026-11-10. **Scope:** P10 review and launch assets.

Read-only review reproduced invalid-secret exposure in settings validation errors,
anonymous starvation of the shared operator bucket, sticky chat resting after health
retry and naive persisted monitor timestamps. Hide settings input in error strings;
separate valid/invalid auth into two bounded 30/minute buckets; make explicit refresh
clear stale chat resting and retry abort-guarded health; validate aware checkpoint time.
Regression tests reproduce the actual paths, including webhook failure/retry/lock cleanup.
DRN-063's original single bucket is superseded by these two buckets. No spending rule
or ledger implementation changed.

The user chooses existing domains, normal Render sleep, optional ALERT_WEBHOOK_URL
and no new notifier dependency. Generic JSON and a Discord content adapter carry only
fixed metadata, with mentions disabled. No external message or schedule was enabled.
The user requests four emulated viewports and a physical-device postdeploy checklist;
physical-device evidence is not claimed from emulation.

Prepare a clearly marked DRAFT public resume/PDF from existing sources; omit phone,
unreconciled externship dates, honours/metrics and claims of implemented P9 features.
Correct the cover's AMU/Aligarh text to existing MSRUAS/Bengaluru evidence. No fact
file or approval flag changes. Use an absolute 1200×630 PNG social URL. Public source
checks found anonymous 404s for the portfolio repositories and obsolete GitHub profile;
preserve receipt metadata but suppress those exact inaccessible destinations in source
chips/project repository links. Recheck the documented list before restoring links.
LinkedIn's 999 automated response is unverified access, not proof of a broken profile.

Browser-measured touch/contrast issues are fixed using existing tokens, including
explicit-light mode when the OS is dark. Keep original frozen captures/human/judge
evidence. Operational source changes invalidate evaluation identity; review new
fingerprints only after all seven original scores reproduce unchanged.

### DRN-064: On-demand health recovery and an external deterministic monitor

**Date:** 2026-11-10. **Scope:** P10 Increments 3–4.

Keep Render sleep. Browser health checks are cancelled at 90 seconds with explicit
manual retry; no background polling or provider probes. Abort and unmount guard late
updates. Missing capacity is conservatively resting; unready payloads cannot show Ready.
Authored answers and contact remain useful while warming/unavailable. Remove historical
25-second promises rather than presenting old measurements as current evidence.

The external monitor validates HTTP and typed health with a 90-second total deadline,
8KiB body cap and no redirects. Two consecutive bad observations trigger incidents,
successful delivery deduplicates, recovery is immediate, and new incidents cool down
15 minutes. Resting is expected unless explicitly monitoring a live window. Persist
only bounded typed status/delivery metadata under an exclusive local lock, with target
and policy binding. Failed delivery remains pending; default dry-run does not acknowledge.
Optional HTTPS webhook sends only service/event/time and never remote text or secrets.
No schedule/channel/notification is enabled before owner choice and delivery approval;
this is not an in-API scheduler, account telemetry or durable P9 state.

### DRN-062: Verify committed release assets and distinguish readiness from capacity

**Date:** 2026-11-10. **Scope:** P10 Increments 1–2, approved phase brief.

Render explicitly provisions the existing pinned model, then verifies corpus, matrix
and cached model compatibility using a local query; it never repairs the committed
index during deployment. The build writes an ignored release receipt using Render's
full commit SHA. Frontend builds similarly emit a revision receipt from Vercel/GitHub
metadata; local unknown identity is explicit. Health publishes only revision/index
identity and service/capacity state, never boot ID or allowances. Startup warms retrieval
off the event loop; failure yields unready HTTP 503, while exhausted/closed inference
alone remains a healthy HTTP 200 with resting capacity. This avoids restart loops.
Provider outage is not inferred from a locally ready ledger. CI/dashboard ordering
still requires account-setting evidence; a blueprint does not establish it.

### DRN-063: Opt-in operator adapter preserves one-shot boot allowance semantics

**Date:** 2026-11-10. **Scope:** P10 Increment 2.

Use a distinct SecretStr operator credential (43–128 URL-safe characters) and constant-time
byte comparison. No credential means 404. Controls reject Origin and duplicate auth
headers, have a bounded per-app global 30/minute limiter including failed auth and
no-store responses, and are absent from public OpenAPI. GET returns private boot/status;
POST delegates strict Allowance validation and one-shot authorization to the existing
ledger. Reject grants above configured shared ceilings; preserve freshness, UTC expiry,
cooldown, unknown charges and closed restarts. No reusable environment spending grant,
new ledger, browser admin UI, storage or live activation is introduced. Operators must
use HTTPS ingress and separately verify remaining account capacity/other processes.
Semantic evaluation and production spending require their existing concrete approvals.

### DRN-050: Frozen validation outcome is a quality result, not a retryable error

**Date:** 2026-11-05
**Authorization/execution:** Aamir authorized validation01–08 against existing human grades, the exact calibrated strict recipe/20b/low/1,024 settings, actual-use reconciliation, zero visitors and recoverable retries. No instructions, schema, human labels or prior calibration judgments changed. Fresh input proof binds the prior judge hash and exact recipe. The reviewed numeric plan allowed 12 attempts/four recoveries, 96,000 tokens; prior 90,256 includes all historical unknown reservations, daily maximum 186,256. Eight calls completed without a failure/retry, 8,382 reported tokens, no new unknowns.
**Outcome:** Support 8/8, Completeness 6/8, Behavior 7/8, Tone 6/8. The80% per-axis gate therefore fails Completeness/Tone. Coverage is sufficient: all 8human labels per axis are binary, balanced 4 pass/4 fail, no missing model grades. A model `uncertain` completeness label is a valid judgment and counts as disagreement; it is not a malformed response to resample.
**Choice:** Preserve the failed report and all five disagreements. The user's permission to resolve execution errors does not authorize selecting favorable valid judgments. Do not tune and reuse this now-exposed validation set as independent evidence. Further calibration requires a reviewed new validation version with independently supplied human grading under the frozen rubric's policy. No new run, human-label edit, accuracy badge or calibration-success claim follows from this failure. This judges authored examples, not actual generator accuracy or truth of 76 draft facts. Increment 5/phase completion remain pending.

---

### DRN-049: Explicit axis independence and completed-run actual-use accounting

**Date:** 2026-11-05
**Authorization:** Aamir explicitly requested a fresh twenty-answer rerun with Behavior limited to third-person identity, injection resistance and refusal boundaries. False or unsupported content must affect Support, not automatically fail Behavior. This supersedes the earlier runtime's first-person `I refuse` example and false-premise wording. Human labels, corpus, packet and validation assignments remain unchanged; do not adjust them to improve agreement.
**Prompt/provenance:** Update the requested `judge-v4-strict.txt` with the explicit axis rule. Compact surrounding instructions without truncating evidence or dropping independent tone/completeness checks. Archive the prior exact runtime prefix and response format under its existing run; reconstructing their combined hash matches the old recipe fingerprint. New instructions get a new fingerprint; the fresh run imports no previous labels or judgments. Maximum complete input bound 6,973 <= 6,976, including schema.
**Quota:** Completed runs with recorded recoveries can now use explicit actual-use reconciliation. All original plan/approval/receipt/result/ledger bindings, finite client chronology, usage/cap checks and verified process exit remain required. An unknown request with a recorded completion time must have a matching recovery-journal attempt/task/reason within the original allowance; an unfinished unknown remains allowed only as a terminal stopped call. Every unknown reservation stays fully charged. Regression cases reject missing proof, fabricated usage and reversed chronology. Original artifacts are unchanged.
**Budget:** Prior completed strict run charges 19,363 known + 14,067 unknown-reserved; all prior daily charge is **71,238** across 51 attempts, including all 29,579 unknown reservations. Fresh plan: 20 answers plus up to 2 recoveries, 106,000 input + 22,528 output = **128,528**, zero visitors. Base input bounds total 91,643; two worst-case extras require 105,595 <= 106,000. Projected daily maximum **199,766 tokens / 73 attempts**. The existing 200,000 daily ceiling, 8,000 TPM, low effort and 1,024 output cap remain unchanged. New hard expiry 17:55:11 IST is anchored to the current rerun authorization, not an extension of an old window. Calibration development agreement and separate validation remain distinct; no result is guaranteed or badge approved.

---

### DRN-048: User-authorized bounded recovery to collect all twenty answers

**Date:** 2026-11-05
**Authorization:** Aamir explicitly directed continuing through failures without returning after each one, until all twenty calibration answers are collected. This supersedes the earlier stop-and-request-approval recovery workflow, not the daily quota ceiling, output cap or evidence/provenance rules.
**Choice:** Use strict response schema and versioned v4-strict criteria. Add opt-in `judge_recovery_attempts` (default zero, maximum four) and `request_bound` input reservations (default remains full cap). Reserve the unchanged conservative byte-plus-overhead bound for each exact request, enforce its 6,976 maximum, and compare actual usage with that reservation. No reservation is refunded. Retain the same attempt ledger, deadline and quota counters on recovery; journal each failed attempt, preserve unknown usage/full request reservation and require a rolling minute after client completion. Retry only JSON validation, typed contract failure, 429, 5xx or network/timeout errors. Authentication, missing usage, reservation overruns and exhausted budgets do not auto-retry. Production paths are unchanged.
**Bound:** Complete twenty-item base input bound totals 91,243. Four worst-case recoveries add 27,904; required input 119,147. Approved continuation plan reserves 135,424 input + 24,576 output = **160,000** across maximum 24 attempts to obtain twenty grades. Prior daily charge remains 37,808 including both unknown calls' full 15,512. Total conservative daily ceiling remains **197,808 / 53 attempts**, zero visitors. Preflight reserves the complete slice plus all recovery slots; SDK retries remain disabled. This is bounded execution under the continuation instruction, not unbounded spending or permission for validation calls. New hard window is anchored to the continuation at 15:52:18 IST, expires 16:37:18 IST.

---

### DRN-047: Strict schema after a recorded JSON-mode validation failure

**Date:** 2026-11-05
**Outcome:** V4/JSON-object run `calibration-2026-11-05-v4` at clean `1e470bb` stopped on attempt five with `BadRequestError`, HTTP 400, `json_validate_failed`. Four valid grades match all human axes; sixteen answers are missing. Known usage: 2,972 input + 885 completion = 3,857. Final usage unknown; full 8,000 reservation retained. No retry, continuation, validation or complete judge artifact. The code identifies output validation failure, not the exact malformed output or the older lost 400's cause.
**Choice:** Preserve used v4 prompt/receipt/result/progress unchanged. Prepare separate `judge-v4-strict.txt` with the same user criteria and explicit support/completeness. Use documented `json_schema`/`strict:true`, derived from typed `JudgePayload`/`Labels`, not JSON-object mode. Remove schema titles/string constraints outside the provider subset; local validation retains nonblank rationale. Full inputs/maps and human grades stay unchanged. This is offline preparation, not a new live approval.
**Provenance:** Effective judging fingerprint binds instructions **and actual response schema**. Runner snapshots/sends/hashes the same pair. Prior reuse rejects schema changes even if prefix/settings stay unchanged. Regression tests reproduced both missing schema invalidation and mismatched emitted fingerprints, then verified fixes. Earlier configurations are not mixed into strict results.
**Budget:** V4 reconciliation charges 3,857 known + full 8,000 unknown = 11,857. Across all four runs: 29 attempts, 22,296 known and two unknown requests retaining 15,512. Prior daily charge 37,808; separately approved twenty-call strict run could reserve 160,000 for **197,808 daily tokens / 49 attempts**, zero visitors. Strict full input bound 6,953 <= 6,976 includes schema; per-call reservation remains 8,000. Another run requires new exact-plan/budget approval/window and confirmed capacity; the stopped approval is not reused. Strict structure does not certify semantic agreement or guarantee provider success.

Official basis: [Groq strict structured outputs](https://console.groq.com/docs/structured-outputs), installed SDK 1.7.0 and offline MockTransport checks.

---

### DRN-046: Explicit v4 judging and actual-known accounting with unknown reservations

**Date:** 2026-11-05
**Context:** Aamir approved twenty fresh v4 calibration calls, fixed 20b/low effort/1,024 output, actual-usage reconciliation, zero visitors and >180,000 remaining tokens. V3's abbreviated axis instructions and ID-only rationale example are a plausible contributor to disagreement, not a proven sole cause. The final HTTP 400 body was lost; do not assert its cause.
**Choice:** Runtime v4 explicitly grades the supplied answer, defines behavior/tone with the user's exact examples, and requests reasons per axis rather than an ID list. Append frozen support/completeness definitions without duplicating behavior/tone. Preserve frozen v1 authoring template, packets, human labels, evidence and all previous runtime versions. Effective prompt hashes prevent mixing configurations. The user explicitly requires `I refuse` among persona-failure examples; retain that stricter interpretation despite its risk of flagging a legitimate first-person assistant refusal under the older rubric. Do not silently edit human grades to resolve this tension.
**Item 20:** Installed Groq SDK 1.7.0 with MockTransport serializes the complete item-20 payload and low/JSON-object/1,024 settings without unsupported raw-reasoning/tool parameters. Full input bound is 6,953; input plus output is at most 7,977 by the unchanged reservation policy, well below the documented 131,072 context/65,536 output model limits. No frozen content is shortened or rewritten. This excludes the documented context ceiling as an explanation, not every provider-side 400; existing safe error diagnostics remain enabled.
**Accounting/budget:** Add an explicit opt-in reconciliation purpose for reported calls plus a terminal unknown call's full reservation. Validate original approval/plan/receipt/result/ledger, chronology, finite times, model/caps and sequence; reject unknown usage masquerading as reported, nonterminal unknowns and lifecycle uncertainty. Preserve receipts/results and original reservations. V3 charges 14,341 reported + 7,512 unknown-reserved = 21,853. With earlier 4,098, prior daily charge is 25,951 across 24 attempts. New per-call cap: 6,976 input + 1,024 output = 8,000 TPM, zero visitors; twenty calls reserve 160,000. Projected local daily maximum: **185,951 tokens / 44 attempts**. New in-run attempts still reserve full caps and never retry automatically. Fresh immediate authorization receives a hard 45-minute deadline anchored at 13:51:03 IST, expiry 14:36:03 IST, without extending the old expired window. No validation calls or success claim are authorized by this preparation.

Official checks: [Groq 20b limits](https://console.groq.com/docs/model/openai/gpt-oss-20b), [JSON modes](https://console.groq.com/docs/structured-outputs), [reasoning controls](https://console.groq.com/docs/reasoning).

---

### DRN-045: Preserve partial calibration and safe provider-error diagnostics

**Date:** 2026-11-05
**Evidence:** The approved schema-v3 run at clean `be132d5` made twenty attempts. Nineteen returned schema-valid grades and 14,341 reported tokens; request 20 returned HTTP 400 with no reported usage. The adapter discarded exception details, so the exact cause is unknown. No retry occurred. Partial development agreement is 17/19 support, 19/19 completeness, 13/19 behavior and 14/19 tone. Even a matching final grade leaves behavior/tone below 80% on this calibration slice. This is not validation or generator accuracy.
**Choice:** Preserve exact receipt/result/progress and a hash-bound summary with every disagreement. Do not produce a complete `judge.json`, edit human grades, assign a missing grade or mix configurations. Keep the unknown request's full 7,512 reservation and the stopped run's conservative hold; fully-reported reconciliation cannot apply. The twenty-attempt approval is consumed. Review instructions, axis separation and rationale quality before more spending.
**Offline follow-up:** Typed per-attempt metadata retains exception class, validated HTTP status and three allowlisted codes. Exclude arbitrary exception text, response body, headers, failed generation and hidden reasoning. Unknown usage and retry/stop behavior remain unchanged. A fake SDK `BadRequestError` regression verifies retention. This fix does not reconstruct the historical HTTP 400 body or establish its cause.

---

### DRN-044: User-authorized actual-usage reconciliation and zero visitor reserves

**Date:** 2026-11-05
**Context:** Aamir explicitly prioritized same-day calibration, authorized reconciling both aborted runs to four calls/4,098 reported tokens, zeroing visitor allowances, and executing schema-v3 with low effort/1,024 output. He confirmed more than 195,000 tokens/990 requests remaining and a quiet 45-minute window. This supersedes the earlier conservative holds/reserves for this requested run; it is not a provider-account measurement by Codex.
**Choice:** Add separately named `actual-usage-reconciliation.json` records, with explicit purpose, actor/reference, verified exit and original receipt/result/ledger hashes. Reuse all existing complete-ledger, known-usage, model/cap, approval-binding and chronology checks. Permit only known post-response task/contract/incomplete-output stops; lifecycle/unknown usage is still ineligible. Retain original receipts, results and prior reconciliation unchanged. Records retain 30,048 original attempted reservations but explicitly set daily charges to the fully reported 4,098 tokens/four calls. Missing or invalid records retain holds or fail closed. Future in-run admission remains reservation-based, with no automatic refund or retry.
**Budget:** Permit nonnegative visitor fields and set all four to zero only in the approved standalone run budget. Prior daily charge: 4,098 tokens/four requests; new run ceiling: 150,240 tokens/20 attempts; total local projection: **154,338 tokens/24 requests**, within confirmed 200,000/1,000 caps and the user's remaining-capacity statement. Per-call 6,488 input + 1,024 output = 7,512 remains below 8,000 TPM. Global visitor/production traffic is not controlled by this standalone runner; the user's quiet-window statement is binding. Source/inputs/approval, cooldown, one-shot IDs, known-usage checks and all failure stops remain enforced. The 45-minute window is anchored at 07:05:28 UTC (12:35:28 IST), never extended by preparation.

---

### DRN-043: Explicit judge output shape and post-response failure evidence

**Date:** 2026-11-05
**Context:** The approved low-effort/1,024-output recovery at clean `d609e12` stopped after one response (625 input/131 completion tokens, finish reason `stop`) with a generic task error. The version retained neither the original exception nor final response. An output cutoff is excluded by the recorded finish reason; the exact cause is unknown. A malformed JSON contract is a plausible failure mode, not a recovered historical fact.
**Choice:** Retain the actual v2 template/run unchanged. Add runtime v3 with an explicit nested `labels` object and string `rationale`, neutral `LABEL` placeholders, unchanged full evidence and rubric definitions. Effective-prompt hashes invalidate older plans/results. Capture future final judge content before typed validation; malformed payloads stop without retries or accepted grades and retain structured issues with input/context excluded. Other failures retain safe exception class/task ID only. Raw exception messages, provider credentials, hidden reasoning and visitor transcripts are outside this capture scope.
**Evidence/limits:** Fake-provider regressions cover flat labels, nested rationale and invalid JSON. These reproduce the diagnostics gap; they do not establish which error occurred in the lost live response. Current full prompts still fit the unchanged 6,488 input reservation. Both live runs remain incomplete and archived, totaling four calls/4,098 actual tokens. This generic task-error stop does not qualify for DRN-042 reconciliation. No new provider call or authorization is implied by the offline fix.

---

### DRN-042: Explicit reconciliation of a fully reported stopped evaluation

**Date:** 2026-11-05
**Context:** After learning that the old local hold blocked same-day recovery, Aamir explicitly requested immediate execution and reaffirmed capacity. The stopped run's three attempts all had reconciled reported usage; no unknown provider consumption or live process remained. Holding twenty potential attempts as if they had all occurred obscured the distinction between authorization ceiling and spent reservations.
**Choice:** Add an opt-in, separately recorded operator reconciliation only for fully reported incomplete-output stops. Preserve and hash the original receipt/result/ledger; bind them to the original approval's exact plan, validate chronology and sequential finite attempt times, approved model/caps, per-model aggregate ceilings, and process exit. Retain every attempted input/output reservation in full. The old run therefore remains charged three requests/22,536 reserved tokens, rather than only 3,342 actual tokens. Release only unattempted potential reservations, with explicit actor/reference and immutable proof. Missing/uncertain/stale/forged/lifecycle records keep the full hold or fail closed.
**Limits:** No receipt deletion, per-attempt refund, generic retry, approval reuse, cooldown bypass or production-wide quota fix. The fresh account-capacity statement and original visitor reserves remain necessary; other provider traffic is not independently observed. Reconciliation plus a distinct approved plan permits the requested immediate recovery without inventing a new quota day. The quiet-window expiry is anchored to the user's confirmation, not extended by preparation. Original partial grades remain diagnostic and are not mixed with the new configuration.

---

### DRN-041: Fit the approved 1,024-token output cap without weakening input guards

**Date:** 2026-11-05
**Context:** Aamir approved the low-effort recovery and requested `max_completion_tokens`/`per_call_output` of 1,024. The previous 7,000 input reservation plus 1,024 output plus 400 visitor TPM exceeded the confirmed 8,000 TPM limit. The previous stopped run's same-day hold also remains active; the current date is still 5 November UTC.
**Choice:** Keep all answers, evidence, human labels, case/split files, frozen authoring template and rubric unchanged. Add a separately versioned concise runtime prefix (`judge-v2.txt`), retaining evidence-only grounding, injection resistance, semantic/requirement-local citation support, known negatives, plans versus experience and independent labels. Append the same four rubric defining sentences verbatim. Remove repeated JSON schema examples/workflow wording; retain the existing JSON payload with complete evidence. Bind the effective runtime prompt into planning inputs as well as judge artifacts.
**Budget:** The largest full prompt reservation becomes 6,369 under the unchanged byte-plus-overhead policy. Reserve 6,488 input + 1,024 output = 7,512 per call; twenty calls still reserve exactly 150,240 tokens (129,760 input + 20,480 output). Add the existing 400 visitor TPM to get 7,912 < 8,000. Daily visitor reserve stays 20,000, so the previously confirmed 170,240 daily capacity requirement is unchanged. No tokenizer estimate, visitor reserve, quota limit or old receipt is weakened to admit the larger output cap.
**Timing/limits:** This is offline preparation for the user's amendment, not another live attempt. The old hold remains until the next local UTC budget day, 05:30 IST on 6 November, and a start-window preference is pending. Do not silently reinterpret current capacity/quiet-window confirmation as an arbitrary later execution time. No new provider calls, scheduling action, validation execution or accuracy claim is made by this change. The larger cap reduces one constraint but cannot guarantee complete output.

---

### DRN-040: Explicit judge settings after a bounded incomplete calibration run

**Date:** 2026-11-05
**Evidence:** Aamir confirmed the numeric twenty-call calibration proposal and account capacity. The clean `1927818` run made three real 20b requests, all with reported usage: 2,306 input + 1,036 completion = 3,342 tokens. Two grades parsed; the third reported the full 512 completion tokens and failed the runner's completion-status gate. It stopped without a retry or higher limit. The exact third finish reason was not retained by that version; do not retroactively assert it. Partial receipt/result are archived unchanged, never promoted to a complete judge artifact or an accuracy result.
**Choice:** Keep the approved stop, output ceiling, retry prohibition and quota holds intact. In the offline follow-up, record `Attempt.finish_reason`, make `reasoning_effort: low` explicit for future evaluation judging only, and require typed judge configuration (model, temperature, effort, JSON format, output cap) in plan v2, results and judge artifacts. Validation must match calibration settings exactly, including output cap. Old plans and unrecorded configurations fail closed; do not guess the original provider-default effort. Production generation settings, frozen prompts/rubric, examples, splits and human grades remain unchanged.
**Why:** Missing output and known usage are separate outcomes. The existing gate prevented an incomplete response from becoming a grade, but the missing finish metadata limited diagnosis. Explicit low effort is a supported Groq control and a bounded mitigation for future output pressure, not a demonstrated cure or evidence of better judging. Mocks verify request construction and failure behavior; they cannot prove that the next real response will fit or agree with a human.
**Budget/provenance:** No unused part of a stopped authorization is silently reused. Preserve original build receipts for local quota accounting and archive copies for reproducibility. The conservative local ledger still charges the full approved ceiling for a stopped run; that is not actual provider consumption. A restart needs a new run ID, matching clean-source plan, fresh capacity verification and new approval, normally in a later UTC budget day. Recalibrate all twenty under one explicit configuration; the two old grades are diagnostic evidence only. The eight validation calls, held-out questions and publication remain outside this authorization.

---

### DRN-039: Independent human grading and a separately authorized bounded runner

**Date:** 2026-11-04
**Context:** Increment 4 is authorized offline; Aamir will supply human grades in a copied JSON file. No live Groq budget exists. Fake/curated contract captures cannot establish model accuracy or judge agreement, and the production quota guard misses individual provider calls.
**Choice:** Freeze 20 authored calibration answers and eight separate development validation answers by semantic group, with complete draft evidence, case/item/corpus/rubric/prompt hashes and a write-once packet lock. Include explicit negative/fit and intentionally defective examples without pre-filling human labels. Keep human answers in a separate attributed annotation file; do not promote underlying facts or case labels. Judge support, completeness, behavior and tone independently. Compare the validation slice only after twenty human calibration grades and twenty judge calibration outputs exist. Require >=80% agreement on every axis, eight binary validation grades per axis and both pass/fail classes. Report confusion counts, denominators, abstentions, missing labels and human overrides. Judge uncertainty is disagreement; human uncertainty is excluded and can leave insufficient coverage. Fake judging remains diagnostic even at perfect agreement. Do not tune against validation outcomes.
**Prompt/provenance:** The 20b evaluation judge sees authored answers and the same complete evidence/local maps as the human, without human labels or other judge outputs. Compact defining rubric sentences plus explicit support/negative/identity instructions avoid sending human workflow procedures to the model. Fingerprint the exact rendered system instructions, snapshot them for a run, and reject prior calibration after any effective prompt change. This supplements the static prompt/rubric hashes. The authored validation slice is separate from the repository's ten reserved held-out cases, which remain unexecuted. Small obvious counterexamples and same-family 120b/20b bias limit the evidence; no statistical confidence or generator accuracy is inferred.
**Runner seam:** Default CLI is offline; a draft plan is a proposal, never consent. Live execution requires an exact plan/budget hash, explicit separate approval/reference, fresh exact-account-limit evidence, a short authorization window, clean compatible source/data/runtime/grading inputs and explicit visitor/draft/reservation-policy acknowledgments. Run actual nonstreaming chat/tool/rewrite logic or an isolated fresh fit pipeline. One standalone `MeteredLLM` admits every complete call, including extraction retries, rewrite, tool turns, alignment and summary. Reserve full approved per-model input/output ceilings before attempts, never refund them, and separately retain reported usage. Serialize requests across both models, pace with conservative shared-minute reservations and reserve visitor capacity plus declared prior daily consumption. Pin Groq's host, disable SDK retries, cap output and own client closure.
**Failure/lifecycle:** Stop on caps, deadlines, unknown/inconsistent usage, provider errors, cancellation, model mismatch or truncated output; application fallbacks cannot reset the stopped ledger. Cap runtime at authorization expiry and UTC midnight. Persist a one-shot receipt before client creation and known ledgers before awaiting closure, including close cancellation. Atomic local results, an exclusive workspace lock, unique run IDs, a 60-second cross-run cooldown and conservative prior-use charges prevent local budget resets. Interrupted runs charge full approved ceilings; midnight-crossing receipts count on intersecting days. Source/input drift fails certification. No automatic resume, lock deletion or uncertainty reset.
**Limits:** UTF-8 payload bytes plus overhead are a conservative reservation policy, not exact tokenization or a provider-enforced input limit; reported excess stops further calls but cannot undo already consumed tokens. Live approval must acknowledge this. Native ONNX work cannot be forcibly cancelled by asyncio. The runner cannot observe other workspaces/visitor consumption and does not fix production-wide quota accounting. Combined certified result/publication/CI contracts remain Increment 5. Human grades, genuine judge outputs/agreement and live budget approval are pending; no model accuracy, held-out outcome, fact approval, badge, schedule, push or deployment is supplied by this increment.

---

### DRN-038: Recorded contract replay with explicit evidence limits

**Date:** 2026-11-04
**Context:** Increment 3 needs reproducible answer checks and backend-to-frontend event contracts without authorized live answers or human-calibrated labels. Existing fit cache flags and curated reports cannot establish fresh generation or semantic correctness.
**Choice:** Capture actual chat/fit/preset endpoints through fresh application instances with injected fake model/retrieval adapters and request guards, fresh tool registries and isolated fit caches. Skip production lifespan deliberately; contract capture is not startup QA. Commit raw endpoint bodies with case ID/version/hash, corpus/dataset/prompt/source fingerprints, capture timestamp and commit/dirty provenance. Track origin (`fake`, `curated`, future `live`) independently of delivery (`fresh`, `cached`, `preset`); record fake adapter attempts and synthetic usage as fake, never provider measurements. Offline bundles reject live records. Use production Pydantic models and scorer to inspect saved bodies; consume the same bodies through real frontend Zod schemas and streaming clients under mocked fetch.
**Failure behavior:** Validate case/split/transport binding and immutable expectations before interpreting expected errors. Preserve the validated stream prefix on malformed/truncated output: forbidden text, size limits and citation identity still apply; incomplete required-answer/refusal obligations are explicitly unavailable. Check requirement-local citation membership separately from intrinsic positive-evidence and configured negative-only rules. Curated reports without retrieval traces cannot claim local membership, but still face intrinsic citation/score checks. Never turn an unavailable check into an accuracy pass. Stale corpus/dataset recordings fail closed; prompt changes are disclosed without pretending old outputs were regenerated. Replay failures retain categories; provenance/execution errors leave previous output untouched.
**Limits:** Eight captures cover four unique development cases; 36 have no recording. Seven are fake, one is curated. Lexical constraints and narrow known-negative rules cannot establish semantic entailment. All 76 fact chunks remain draft, judging remains pending, and no held-out case is executed. The existing cached report flag remains unreliable and is exposed as a warning, not repaired by fixture metadata. Curated local evidence and comparable authorized live stuffed/RAG answers/usage remain unavailable. Combined result provenance/CI gates are Increment 5 work; request telemetry is Increment 6. No dependency, live runner, provider budget, public badge or production safety claim is added.

---

### DRN-037: Retrieval metrics with honest denominators and portable gates

**Date:** 2026-11-04
**Context:** The legacy benchmark used alternative source IDs for Hit@5 and a machine-dependent latency assertion. Phase 8 needs distinct top-three/top-five metrics, without converting alternative sources into exhaustive relevance labels or scoring skipped behaviors as successes.
**Choice:** Use shared pure ranking metrics for the CLI and legacy aggregate regression. Report Hit@3/@5, explicitly truncated MRR@5, and macro Recall@3/@5 only over `all_relevant` labels. Alternative-source cases do not contribute to recall; no-source cases have no score. Exclude protocol, requirement-extraction JDs and histories requiring recorded rewriting from the raw-query retrieval diagnostic. Retain excluded counts/reasons and all legacy individual top-five regressions. Portable gates are Hit@3 >=0.90 and MRR@5 >=0.80, plus every legacy Hit@5. Report warmed latency and nearest-rank percentiles separately; the previous default mean <25 ms assertion becomes an opt-in, separately recorded `--max-mean-ms` benchmark gate.
**Provenance and failure:** Validate frozen evidence before loading cached ONNX assets. Report the two overlapping development sets separately, with per-category denominators and measured/skipped cases. Record source commit/dirty state, retrieval-code hash, frozen dataset/corpus/index identities, runtime/library versions and RRF configuration. Abort on retrieval/provenance failure without overwriting a previous complete artifact; completed gate failures remain valid diagnostics with nonzero exit status. Test through the real retriever interface using injected fakes and clocks. No new dependencies, Groq path, held-out execution or badge publication is added.
**Limits:** Source membership and retrieval quality do not prove semantic answer support. Recall presently has only two eligible provisional development cases; do not present its perfect score as broad evidence. Reserved cases remain author-visible and unexecuted. Full combined result/CI/publication contracts remain Increment 5. The user's waiver of teach-back answers does not waive human calibration or live-run budget approval.

---

### DRN-036: Frozen evaluation inputs and fail-closed embedding provenance

**Date:** 2026-11-04
**Context:** Phase 8's offline brief was approved. The legacy 45-question retrieval set is known development material, every public fact is still draft, and the existing embedding archive bound IDs to vectors without validating same-ID content changes.
**Choice:** Create 40 development cases and 10 newly authored held-out cases, grouped before tuning. Preserve provisional labels and draft facts. Freeze case/group/split hashes plus corpus/index snapshots; reject duplicate IDs, group/conversation overlap, copied legacy inquiries and unknown/nonpublic source labels. Default loading excludes held-out content; explicit reserved validation checks structure/provenance only. Separate all-relevant source sets from acceptable alternatives and semantic expectations from literal substring checks. Text fingerprints normalize Git CRLF/LF differences; the NPZ uses exact byte and matrix hashes.
**Index implementation:** Share artifact validation and embedding-input construction between builder/runtime. Rebuild vectors from cached local model assets, embedding corpus/input/model-asset/matrix fingerprints, FastEmbed version, UTC build time and source commit/dirty state in the archive. Production runtime rejects legacy/stale/corrupt artifacts instead of re-embedding the corpus, and uses local-only query model loading with asset fingerprint verification. Keep fake model injection. Isolate FastEmbed 0.9.1's private resolved-directory accessor in one helper. Move CI's previously implicit model-asset acquisition to an explicit setup step; no live Groq workflow is added. Pin the already-used PyYAML dependency.
**Trade-offs and limits:** A reserved set visible to its author is not an independently blind benchmark; paraphrase grouping still needs manual review. Hashes establish identity, not fact approval, semantic entailment or authenticity. Initial index provenance records `88fae8c` plus a dirty working tree, not a clean-commit accuracy run. Production concurrency/readiness/resource bounds and quota accounting remain separate work. No judge calibration, live result, public accuracy badge, new framework or database is introduced. Approval to start Phase 8 does not complete the pending remediation teach-back/tag.

---

### DRN-035: Requirement-local evidence and explicit failure/stream completion

**Date:** 2026-11-03
**Context:** Handoff review found cross-requirement citation acceptance, invented fallback requirements, unsupported preset narratives, colon/heartbeat conflation, silent premature EOF and nonserializable validator context.
**Choice:** Keep the fixed pipeline and existing stack. Validate evidence against a requirement-ID-to-retrieved-IDs map, with unique extracted IDs. Retain one extraction retry and then emit `extraction_error` without a report/cache entry. Preserve raw JSON-mode responses before parsing. Curated snapshots cite actual facts, use conservative narratives, compute scores through the scorer, and disclose manual provenance in the UI. Heartbeats use a distinct marker internally and SSE comments at both chat/fit transports. The shared frontend reader treats EOF before a valid terminal event as failure and owns reader cancellation/release. Validation responses omit exception context while retaining the 422 envelope/request ID.
**Alternatives:** Continue global citation checks and generic fallback requirements; recognize heartbeat strings by their prefix; silently accept EOF. Rejected because they produce misleading matches, lose valid text, or leave UI loading indefinitely.
**Limits:** Requirement-local membership establishes lineage, not semantic support. The snapshots are not independently calibrated evaluation ground truth. Draft approval, semantic judges, quota accounting, cache bypass/versioning and resource bounds remain tracked in PROGRESS.md. This record qualifies DRN-028's anti-overclaiming and authoritative-benchmark claims and DRN-026's stream lifecycle claims.

---

### DRN-001: Assistant Voice

**Date:** 2026-10-23  
**Context:** The AI assistant needs a consistent voice. Options range from speaking *as* Aamir to speaking *about* him.  
**Options:**  
A. Third person — "Aamir built…" with "I'm Aamir's AI assistant" identity  
B. First person — AI speaks as Aamir ("I built…")  
C. Hybrid — introduces itself as assistant, then uses Aamir's name naturally  
**Choice:** A — Third person  
**Why:** Honest (recruiters know it's AI), matches the trust line, avoids uncanny valley of pretending to be a person. User's choice.

---

### DRN-002: LLM Model Selection

**Date:** 2026-10-23  
**Context:** Need to choose Groq models for main answers and utility calls.  
**Options:**  
A. `openai/gpt-oss-120b` for everything  
B. `openai/gpt-oss-120b` for answers, `openai/gpt-oss-20b` for utility  
**Choice:** B — Use 120b for main chat, 20b for utility (query rewriting, JD extraction)  
**Why:** Both have the same rate limits (30 RPM, 1K RPD, 8K TPM, 200K TPD), but the 20b model is cheaper per token. Using two models also provides failover: if one model's quota is hit, the other has its own limits. Model IDs in config.  
**Updated:** 2026-10-23 — user confirmed 20b also exists and works.

---

### DRN-003: External Postgres Provider

**Date:** 2026-10-23  
**Context:** Need a free-tier Postgres for Phase 9+.  
**Options:**  
A. Neon — 0.5 GB, pauses after 5 min idle  
B. Supabase — 500 MB, 2 free projects, good dashboard  
C. Defer decision  
**Choice:** B — Supabase, deferred to Phase 9  
**Why:** More storage, good DX. Not needed until Phase 9 (handoff, analytics). App designed DB-free until then.

---

### DRN-004: Monorepo Name

**Date:** 2026-10-23  
**Context:** Plan says `portfolio-assistant/`, workspace is `aamirmkh-portfolio/`.  
**Choice:** Keep `aamirmkh-portfolio` as-is.  
**Why:** Already set up, no reason to rename.

---

### DRN-005: Agent Instructions File

**Date:** 2026-10-23  
**Context:** Need a root instruction file for AI agents.  
**Options:** AGENTS.md vs CLAUDE.md  
**Choice:** AGENTS.md  
**Why:** Standard convention, read natively by the agent tools.

---

### DRN-006: CORS Configuration Architecture

**Date:** 2026-10-24  
**Context:** The frontend (hosted on Vercel) and backend (hosted on Render) reside on distinct origins. We need robust CORS handling without wildcard exposures.  
**Options:**  
A. Wildcard `allow_origins=["*"]`  
B. Explicit allowlist loaded via environment variables and parsed in `Settings`  
**Choice:** B — Explicit allowlist  
**Why:** Security best practice. Prevents unauthorized cross-origin requests while facilitating local development (`localhost:5173`) and production deployment (`*.vercel.app`).

---

### DRN-007: Request Tracing via X-Request-ID

**Date:** 2026-10-24  
**Context:** Need structured traceability across request lifecycles and error logs.  
**Choice:** Middleware generating UUIDv4 or propagating client-supplied `X-Request-ID`.  
**Why:** Enables end-to-end correlation between client errors, server logs, and frontend status reporting.

---

### DRN-008: Deep LLM Adapter Interface (Protocol Seam)

**Date:** 2026-10-26  
**Context:** Need an abstraction over the Groq API that decouples FastAPI endpoint logic from SDK internals, ensures deterministic test isolation without live API keys, and provides a clear extension point for tool loops and model failover.  
**Options:**  
A. Direct SDK calls inside endpoint handlers  
B. Generic multi-provider wrapper framework (e.g. LiteLLM, LangChain)  
C. Thin in-house protocol `LLMClient` with a single `complete()` method  
**Choice:** C — Thin in-house protocol `LLMClient`  
**Why:** Complies with no-LangChain hard rule and deep-module engineering standard. `GroqLLM` encapsulates `AsyncGroq`, timeout/retry, token counting, and error mapping. `FakeLLM` satisfies the identical protocol for sub-second, zero-cost CI tests. Injected via FastAPI `Depends`.

---

### DRN-009: Context-Stuffed System Prompt Baseline (Phase 1)

**Date:** 2026-10-26  
**Context:** Need to ground conversational responses in verified facts prior to building Phase 2 hybrid RAG.  
**Options:**  
A. Early RAG prototype with chunks and vector store  
B. Context stuffing full résumé markdown into the system prompt  
**Choice:** B — Context stuffing full résumé into system prompt  
**Why:** Résumé context is ~1,380 prompt tokens, fitting comfortably within Groq's 8,000 TPM limit for `openai/gpt-oss-120b`. Enables immediate end-to-end conversational capability and prompt verification (third-person persona, honest "I don't know" fallback) without adding retrieval complexity prematurely. Excludes phone number per hard safety rules.

---

### DRN-010: Native Starlette StreamingResponse for SSE over POST

**Date:** 2026-10-27  
**Context:** Need to stream token chunks from FastAPI to React via Server-Sent Events (SSE). The endpoint accepts JSON bodies via HTTP POST (`/api/chat/stream`).  
**Options:**  
A. Add third-party dependency `sse-starlette`  
B. Use built-in Starlette/FastAPI `StreamingResponse` formatted as SSE frames (`event: ...\ndata: ...\n\n`)  
**Choice:** B — Native `StreamingResponse`  
**Why:** Avoids adding unnecessary external dependencies to the pinned requirements. Provides 100% direct control over SSE framing, in-stream error events, and flush headers (`Cache-Control: no-cache, no-transform`, `Connection: keep-alive`, `X-Accel-Buffering: no`).

---

### DRN-011: Hand-Built Streams API SSE Client over POST

**Date:** 2026-10-27  
**Context:** Browser-native `EventSource` only supports GET requests and cannot send JSON payloads or custom headers. We need an SSE client that works over HTTP POST for conversation requests.  
**Options:**  
A. Pull in `@microsoft/fetch-event-source` or third-party client library  
B. Hand-built client `streamChat()` in `frontend/src/lib/sse.ts` using `fetch()`, `ReadableStreamDefaultReader`, and `TextDecoder`  
**Choice:** B — Hand-built client  
**Why:** Follows project principle "build core pieces by hand before adopting frameworks". Keeps initial JS bundle lean (73 KB gzipped, well inside our <200 KB budget). Guarantees strict TypeScript type safety, cleanly handles chunk buffering across arbitrary byte boundaries, and integrates directly with React's `AbortController` for instant user cancellation.

---

### DRN-012: Latency-Aware Cold-Start UX for Render Free Tier

**Date:** 2026-10-27  
**Context:** Render free-tier web services spin down after 15 minutes of inactivity and require ~25s (up to 33s) to boot on initial request. Users might perceive the application as unresponsive during this window.  
**Options:**  
A. Generic loading spinners without explanation  
B. Background health check on page load with latency timer (>2.5s) triggering a transparent status pill and notice banner  
**Choice:** B — Background health check & latency-triggered status pill  
**Why:** Sets honest recruiter expectations upfront. The application immediately displays "Waking Up (Render ~25s)" if the initial connection takes > 2.5s, reassuring visitors that the service is booting rather than broken.


---

### DRN-013: Minimal Editorial Dossier Design System Architecture

**Date:** 2026-10-27  
**Context:** Need a distinctive, professional visual system that presents Aamir's verified technical portfolio without falling into generic AI chatbot aesthetics (e.g. rounded SaaS cards, purple/teal glow gradients, Anthropic terracotta clones) while strictly adhering to our <200 KB gzipped bundle budget.  
**Options:**  
A. External UI / CSS component libraries (Tailwind, Radix, Shadcn)  
B. CSS-in-JS framework (Emotion, Styled Components)  
C. In-house pure CSS design tokens (`tokens.css` + `chat.css`)  
**Choice:** C — In-house pure CSS design tokens  
**Why:** Maintains zero runtime dependencies, strictly preserves our bundle budget (73.74 KB gzipped JS, 3.30 KB gzipped CSS), and gives complete control over light/dark theme variables, hairline dossier borders, fluid typography scales, and WCAG accessibility standards.

---

### DRN-014: Cover State Hero & Graceful Mode Orchestration

**Date:** 2026-10-27  
**Context:** Recruiters arriving at the portfolio need an immediate, authoritative overview of Aamir's identity, verified technical stack, and suggested inquiry directives before entering an active conversation transcript.  
**Options:**  
A. Multi-route SPA with separate `/` and `/chat` paths and route transitions  
B. Unified shell state machine with smooth in-place Cover-to-Chat transition and header reset control  
**Choice:** B — Unified shell state machine  
**Why:** Eliminates client-side router overhead and layout shift (CLS). Provides an intuitive "← Dossier Overview" control that allows recruiters to return to the executive profile at any time without losing context.


---

### DRN-015: Proxy-Aware Sliding Window Rate Limiting Architecture

**Date:** 2026-10-27  
**Context:** Groq free-tier has a 30 RPM limit. We must prevent any individual visitor or scraper from exhausting the API or disrupting service for others, while correctly resolving real client IPs behind cloud reverse proxies (Render load balancers).  
**Options:**  
A. Direct socket IP extraction (`request.client.host`) and fixed-window bucket counters  
B. Proxy-aware IP extraction with RFC header parsing (`X-Forwarded-For` chain, `CF-Connecting-IP`) and in-memory sliding-window limiter (`app.safety.rate_limiter`)  
**Choice:** B — Proxy-aware extraction with sliding-window limiter  
**Why:** Fixed windows allow boundary bursts (e.g. 20 requests in 2 seconds across a minute boundary). Sliding windows enforce a strict rolling rate (10 RPM per IP, with 15 burst allowance). Standard RFC headers (`Retry-After`, `X-RateLimit-*`) provide clear client feedback, and periodic stale key eviction guarantees zero memory leaks.

---

### DRN-016: Two-Tier Prompt Injection Defense & Delimiter Isolation

**Date:** 2026-10-27  
**Context:** Untrusted user inquiries could attempt prompt injection (e.g. "ignore previous instructions", "reveal system prompt", DAN jailbreaks, XML breakout).  
**Options:**  
A. Upstream LLM moderation call (e.g. Llama Guard)  
B. System prompt instructions only  
C. Pre-call deterministic regex guardrails + structural XML delimiter boundary fencing (`<user_inquiry>`)  
**Choice:** C — Pre-call deterministic regex + structural XML fencing  
**Why:** Upstream LLM classification consumes API quota, introduces 500ms+ latency, and adds financial cost. System prompt instructions alone remain vulnerable to jailbreaks. Deterministic regex rejects known imperative override patterns at 0 token cost and sub-millisecond speed, while XML delimiter fencing prevents prompt leakage without false-positives on legitimate recruiter inquiries about prompt engineering or systems architecture.

---

### DRN-017: Global UTC-Rollover Daily Quota Guard

**Date:** 2026-10-27  
**Context:** Groq free tier imposes hard daily limits (1,000 RPD, 200,000 TPD). Traffic surges or repeated testing could drain the account and break the assistant for everyone.  
**Options:**  
A. External database or Redis tracking  
B. In-memory `DailyQuotaGuard` with UTC-midnight calendar rollover and proactive 80% safety cap (800 RPD / 180,000 TPD)  
**Choice:** B — In-memory `DailyQuotaGuard` with UTC rollover  
**Why:** Avoids adding external database dependencies prior to Phase 9. Protects the developer account from total depletion, fails open safely on server restarts, and returns standard HTTP 429 errors with `Retry-After` seconds to UTC midnight when capacity is reached.


---

### DRN-018: Structured Knowledge Base Frontmatter & Chunking Strategy

**Date:** 2026-11-01  
**Context:** The assistant previously stuffed Aamir's entire plain-text résumé into the system prompt (~1,380 tokens per request). This bloated prompt size, risked hallucinating beyond the résumé, prevented fine-grained source attribution, and made it impossible to distinguish between public factual chunks and sensitive runtime policies (such as salary deflections and the recruiter phone-sharing policy).  
**Options:**  
A. Fixed character/sentence sliding-window chunking without metadata  
B. Single monolithic Markdown knowledge file with section header splitting  
C. Curated frontmatter chunks (YAML frontmatter + Markdown content) parsed into immutable Pydantic `FactChunk` models, with draft flags, explicit semantic tags, and private/unindexed segregation.  
**Choice:** C — Curated frontmatter chunks with Pydantic validation  
**Why:** Preserves complete conceptual units (e.g. whole debugging stories, full HR Q&As, project architectures) without chopping sentences mid-thought. Enables granular source section mapping (e.g. `X7`, `J8`, `B1`), allows unverified metrics to be identified in `knowledge-todo.md`, and enables `boundaries.md` to be loaded as prompt instructions while strictly excluded from the public retrieval index.

---

### DRN-019: In-Process Hybrid Retrieval (BM25 + fastembed ONNX + RRF) behind Retriever Protocol

**Date:** 2026-11-01  
**Context:** Need a fast, accurate retrieval system that can run entirely within Render's free tier 512 MB RAM limit, handle exact technical keyword recall (`ETIMEDOUT`, `BullMQ`, `Monaco Editor`, `9.77`) alongside semantic intent ("What did Aamir do at his internship?"), and remain 100% offline and deterministic in CI without external vector database SaaS costs or credentials.  
**Options:**  
A. External Vector DB SaaS (Qdrant Cloud / Pinecone) via remote API  
B. Full PyTorch / Transformers in-process embedding pipeline (~1.5+ GB RAM)  
C. In-process hybrid engine: custom Okapi BM25 ($k_1=1.5, b=0.75$) + FastEmbed ONNX runtime (`BAAI/bge-small-en-v1.5`, 384 dimensions) + Cormack's Reciprocal Rank Fusion ($k=60$) behind an async `@runtime_checkable` `Retriever` protocol seam.  
**Choice:** C — In-process hybrid retrieval with Protocol seam  
**Why:**
1. **Memory Gate Passed:** Total container WorkingSet after loading the ONNX model and indexing all 75 facts is 227.75 MB (<50% of Render's 512 MB cap, leaving >284 MB headroom).
2. **Speed:** Average retrieval latency is 9.39 ms on CPU (p95 11.01 ms), well below the 25 ms ceiling.
3. **Retrieval Quality:** Achieves 100.0% Hit Rate@5 (45/45 queries) and 0.8778 MRR on the labeled evaluation set.
4. **Architectural Seam:** Clean dependency injection via `get_retriever()` enables `FakeRetriever` in unit tests (0.68s execution) and allows plugging in an external `QdrantRetriever` after Gate 2 without modifying a single line of endpoint code.

---

### DRN-020: Server-Supplied Generative UI via Function-Calling Seam

**Date:** 2026-11-02  
**Context:** Recruiters asking about projects should see structured, interactive technical cards with verified metrics, architecture flows, and repository links. If the LLM generates the JSON card directly in completion text, it could hallucinate metrics, fake repository URLs, or invent unsupported features.  
**Options:**  
A. Generative card schemas emitted directly by the LLM in markdown or JSON codeblocks  
B. Server-supplied generative UI: model triggers an abstract function call (`show_project_card(project_id)`), and the server supplies immutable `ProjectCardData` loaded directly from verified facts on disk  
**Choice:** B — Server-supplied generative UI via function-calling seam  
**Why:** Strictly enforces Design Principle 2: "The model selects, your server supplies. Cards and facts come from your data files, never from generated text, so the UI cannot hallucinate a project." The model only decides *which* project to present, while the verified facts, benchmark metrics, live URLs, and architectural blueprints are 100% authoritative and tamper-proof.

---

### DRN-021: Dual-Event SSE Stream Protocol for Citations and Cards

**Date:** 2026-11-02  
**Context:** Need to stream structured citations and generative UI card schemas alongside token-by-token prose over Server-Sent Events (SSE) via POST (`/api/chat/stream`).  
**Options:**  
A. Bundle all metadata into the terminal `done` event only  
B. Stream separate structured event frames (`event: sources`, `event: card`, `event: token`, `event: done`)  
**Choice:** B — Multi-event SSE stream protocol  
**Why:** Emits source receipts and interactive project cards immediately upon resolution before or alongside streaming tokens. Allows the frontend UI to display receipt chips and cards immediately without waiting for long token generation to finish, while keeping streaming text parsing clean and zero-overhead. Also includes sources and cards in `done` for robust client state reconciliation.

---

### DRN-022: Precomputed Dense Embeddings & Single-Thread ONNX Runtime for 512MB RAM Gate

**Date:** 2026-11-02  
**Context:** When testing live chat endpoints on Render's free tier (512 MB cgroup memory cap), the service was killed with an OOM error (`Ran out of memory (used over 512MB)`) resulting in frontend `Notice: Failed to fetch`. Profiling revealed that dynamic runtime embedding of all 75 facts spawned multi-core ONNX thread arenas, peaking at 1,229 MB of RAM. Additionally, FastEmbed downloaded ~130 MB of model weights from HuggingFace on the first live request within the HTTP request cycle.  
**Options:**  
A. Increase Render plan to paid 1GB/2GB tier  
B. Drop dense semantic retrieval and use BM25 only  
C. Precompute fact chunk embeddings offline (`facts_embeddings.npz`, 103 KB), enforce `threads=1` on ONNX Runtime (`TextEmbedding`), pre-warm index in FastAPI `lifespan`, and pre-cache model during Render `buildCommand`.  
**Choice:** C — Precomputed offline embeddings + single-threaded ONNX session + build-time model download  
**Why:**
1. **Memory:** Precomputed `.npz` loads in ~5ms using only ~3 MB RAM. At runtime, the server only embeds the single query string (1 sentence) using 1 ONNX thread, keeping peak process memory strictly at ~208 MB (<41% of Render's 512 MB cap, leaving >300 MB of headroom).
2. **Speed:** Eliminates the 12-second CPU freeze on boot/first-query. Retrieval latency stays at 16.39 ms average on CPU.
3. **Retrieval Quality Preserved:** Retains 100.0% Hit Rate@5 and 0.8778 MRR with zero accuracy degradation.
4. **Resilience:** Model download happens during Render build time; zero network downloads or unauthenticated HuggingFace requests occur inside HTTP request handling.

---

### DRN-023: Three-State Theme Engine (System / Light / Dark) with Pre-Hydration FOUC Prevention

**Date:** 2026-11-02  
**Context:** The minimal Phase 4 implementation only responded to `@media (prefers-color-scheme: dark)`. Recruiters evaluating the portfolio couldn't manually toggle themes, test both palettes, or override system defaults. Furthermore, client-side React theme state can cause a Flash of Unstyled Content (FOUC) if theme tokens are swapped after hydration.  
**Options:**  
A. Rely on an external React theming library (e.g. `next-themes` or custom Context provider)  
B. OS media query only without user override  
C. In-house CSS token bridge (`[data-theme="light"]`, `[data-theme="dark"]`, `@media (prefers-color-scheme: dark)`) paired with `useTheme` hook, local storage persistence, and a synchronous pre-hydration `<script>` in `index.html`.  
**Choice:** C — In-house CSS token bridge with pre-hydration script  
**Why:**
1. **Zero Runtime Overhead:** Theme switching occurs via CSS custom properties on `:root` without triggering React component tree re-renders or hydration waterfalls.
2. **Zero FOUC:** An inline vanilla script in `index.html` inspects `localStorage` and sets `data-theme` prior to DOM paint, completely eliminating visual flicker on cold reloads.
3. **Accessible Three-State Cycle:** Supports `system` (auto OS detection), `dark`, and `light` modes with clear `aria-label` indicators and keyboard navigability.

---

### DRN-024: Zero-Dependency Editorial Prose Formatter & Mobile Bottom-Sheet Ergonomics

**Date:** 2026-11-02  
**Context:** Assistant completions contain structured markdown formatting (code blocks, inline code, bold highlights, bullet lists, numbered sequences, blockquotes). Rendering raw text within a single `<p>` tag diminished technical authority, while pulling in heavy markdown libraries (e.g., `marked`, `react-markdown`, `remark`) would inflate bundle size and risk breaking our <200 KB gzipped budget. Furthermore, large architectural modals centered on mobile screens felt cramped and awkward.  
**Options:**  
A. Import `react-markdown` and syntax highlighter (~35–50 KB gzipped)  
B. Leave responses as plain unformatted whitespace pre-wrap  
C. In-house zero-dependency regex tokenizer (`FormattedMessage`) + mobile bottom-sheet modal drawer (`100dvh`).  
**Choice:** C — Zero-dependency tokenizer + mobile bottom-sheet modal  
**Why:**
1. **Bundle Budget Preserved:** Initial JS bundle remains featherweight at **77.35 KB gzipped** (well under the 200 KB ceiling). Zero external markdown or parsing dependencies.
2. **Editorial Typographic Scale:** Formats code blocks, quotes, lists, bold accents, and inline code with strict 72ch line-length constraints, high contrast, and smooth streaming cursor attachment.
3. **Mobile-First UX:** Automatically transforms the architectural inspection modal into a native-feeling bottom sheet on screens <= 640px while maintaining full keyboard trapping and Escape key dismissal on desktop.


---

### DRN-025: Bundled Instant Answers & SessionStorage Hydration for Zero-Latency Cold-Start UX

**Date:** 2026-11-02  
**Context:** Render's free tier spins down idle backend web services after 15 minutes of inactivity. When a recruiter opens the portfolio and clicks an initial prompt suggestion (e.g., "Who is Aamir?", "Tell me about his AI Engineer background"), the container spin-up takes 30–50 seconds. Waiting almost a minute on a first click degrades user trust and engagement. Additionally, refreshing the browser or navigating tabs wiped the active conversation history, frustrating recruiters conducting multi-turn explorations.  
**Options:**  
A. Display an indefinite loading spinner while the backend wakes up; do not persist chat across page reloads  
B. Keep the container warm 24/7 with an external cron service (violates zero-cost free-tier constraints)  
C. Client-side bundled instant answers for canonical starter prompts (`frontend/src/data/instantAnswers.ts`), paired with `sessionStorage` chat history persistence and a global `Ctrl+K` / `Cmd+K` keyboard shortcut.  
**Choice:** C — Bundled instant answers + `sessionStorage` conversation hydration + `Ctrl+K` hotkey  
**Why:**  
1. **0ms Perceived Latency:** Recruiters who click high-intent prompt chips receive immediate, authoritative dossier summaries and project previews instantly, without waiting for the server spin-up.
2. **Tab-Scoped History Persistence:** Using `sessionStorage` restores the conversation transcript seamlessly on browser reload while strictly scoping user chat data to the active tab session (cleared automatically on tab/window close, preserving visitor privacy).
3. **Power-User Ergonomics:** Registering a global `Ctrl+K` / `Cmd+K` listener focuses the chat input from anywhere in the document, matching modern developer-tool conventions.

---

### DRN-026: Zod Runtime Boundary Contracts & Non-Blocking SSE Heartbeats

**Date:** 2026-11-02  
**Context:** In a decoupled FastAPI + React architecture, TypeScript interfaces exist purely at compile-time and vanish after compilation. If backend response schemas drift or yield unexpected fields, the frontend can experience unhandled runtime exceptions. Furthermore, cloud reverse proxies (Render, Cloudflare, AWS ALB) aggressively terminate idle HTTP/1.1 and HTTP/2 streaming connections after 15–30 seconds of inactivity if no bytes are transferred (e.g. while the LLM engine queues or processes reasoning tokens).  
**Options:**  
A. Rely solely on static TypeScript types and let proxy timeouts trigger generic client-side fetch retries  
B. Use heavy WebSocket protocols with client-server ping/pong frames  
C. Zod runtime boundary validation on the frontend (`contracts.ts`) + FastAPI asynchronous SSE comment heartbeats (`: ping\n\n`) every 15 seconds during stream idle periods.  
**Choice:** C — Zod runtime boundary validation + non-blocking SSE comment heartbeats  
**Why:**  
1. **Fail-Safe Runtime Deserialization:** Zod schemas (`ChatSourcesEventSchema`, `ChatCardEventSchema`, `ChatTokenEventSchema`, `ChatDoneEventSchema`) validate every event frame arriving across the network. If malformed data arrives, safe fallbacks prevent entire application crashes.
2. **Proxy Keep-Alive Without Stream Pollution:** Per the W3C Server-Sent Events specification, lines starting with a colon (`:`) are comments and are ignored by compliant SSE parsers. Emitting `: ping\n\n` periodically keeps intermediate TCP sockets and Cloudflare reverse proxies alive without polluting user transcripts or client state.
3. **Contract Parity Test Suite:** Backed by `backend/tests/test_contracts.py` ensuring Pydantic models and frontend schemas remain strictly synchronized across commits.

---

### DRN-027: Protected In-Process Dev Retrieval Inspection Endpoint & Source URL Lineage

**Date:** 2026-11-02  
**Context:** Evaluating and tuning hybrid retrieval (BM25 + dense ONNX embeddings with Reciprocal Rank Fusion) requires deep visibility into chunk scores, rank fusion weights, and raw retrieved passages. Triggering a full chat completion for retrieval inspection wastes LLM tokens and adds latency. However, exposing internal retrieval endpoints in production could leak private drafting notes or unreleased project data. Furthermore, retrieved citations previously lacked canonical `source_url` metadata, leaving recruiters unable to click directly into Aamir's GitHub repositories or live project demos from source chips.  
**Options:**  
A. Log retrieval rankings to standard server stdout only  
B. Expose an unauthenticated public `/api/debug/retrieve` endpoint across all environments  
C. Mount a dedicated `GET /api/debug/retrieve` endpoint protected by environment guards (`ENVIRONMENT != "production"`, returning 404 in production), and enrich all 75 fact chunks with verified `source_url` metadata pointing to live repositories.  
**Choice:** C — Environment-guarded dev retrieval inspection endpoint + enriched `source_url` fact metadata  
**Why:**  
1. **Zero Production Attack Surface:** In production (`ENVIRONMENT=production`), the debug route is completely disabled and returns an immediate 404 Not Found response, preserving security and preventing reconnaissance.
2. **Fast Diagnostic & Eval Loop:** In development/staging, developers can instantly test queries against the full hybrid retrieval pipeline (`top_k`, reciprocal rank scores, chunk IDs) in sub-20ms without invoking the LLM.
3. **Verifiable Lineage:** Every source citation now links directly to verified GitHub repositories, papers, or project documentation, satisfying the core portfolio rule: "Every claim has a receipt."


---

### DRN-028: Fixed-Stage Pipeline vs. Free-Roaming Agent for JD Fit Evaluation

**Date:** 2026-11-02  
**Context:** When a recruiter pastes a job description to assess candidate fit, we could either give an LLM agent free-roaming search and tool-calling capabilities, or execute a deterministic, multi-stage pipeline. A free-roaming agent risks unpredictable execution times (15–60s), unbounded token consumption, looping, and hallucinations where the model overclaims candidate qualifications to sound helpful.  
**Options:**  
A. Autonomous tool-calling agent with retrieval loop  
B. Single-prompt stuffed evaluation (paste entire JD + all candidate facts into one prompt)  
C. Deterministic 5-stage pipeline: structured requirement extraction, per-requirement hybrid retrieval, batched LLM judging, deterministic anti-overclaiming invariant enforcement, and executive summary synthesis.  
**Choice:** C — Deterministic 5-stage pipeline  
**Why:**  
1. **Predictable Latency & Bounded Cost:** Extraction uses the lightweight utility model (`openai/gpt-oss-20b`) with structured JSON schema. Per-requirement hybrid retrieval runs concurrently across threads. Judging is batched into a single completion, keeping the entire pipeline within ~3–6 seconds.
2. **Anti-Overclaiming Invariant:** The judge cannot invent matches. If the model claims `strong` or `partial` alignment for a requirement but cites no valid retrieved evidence chunk ID, the deterministic scorer (`scorer.py`) automatically downgrades the verdict to `gap` and marks `downgraded = True`.
3. **Honest Ramp-Up Narratives:** Known gaps (Kubernetes, AWS/GCP, Kafka, C++, LangChain) are grounded in verified ramp-up narratives in `skills.yaml` (`skill-ramp-up-narratives`), turning potential rejection points into credible engineering growth narratives.
4. **Idempotent SHA-256 Caching:** Identical job descriptions produce an identical SHA-256 hash, returning cached evaluations in sub-10ms without consuming daily LLM quotas.
5. **Fit Rate Limiting:** A dedicated daily quota (`FIT_RATE_LIMIT_DAILY = 5` per client IP) protects Groq free-tier rate limits from automated abuse.
6. **Pre-Evaluated Golden Benchmarks for Curated Roles:** Rather than burning live Groq tokens or faking progress timers when recruiters click curated sample roles, 4 authoritative golden benchmark reports (`backend/app/fit/golden_benchmarks.py`) are pre-evaluated, SHA-256 matched, and pre-seeded directly into the pipeline cache and exposed over `GET /api/fit/presets`. In the UI, recruiters receive an instant snapshot labeled `[VERIFIED GOLDEN BENCHMARK (CACHED SNAPSHOT)]`, a collapsible `“📄 View Evaluated Job Description”` preview, and a `“🔄 Re-Run Live Pipeline”` button for complete transparency. Custom pasted JDs always invoke the live 5-stage SSE pipeline.


---

### DRN-029: Authoritative Contact Number Disclosure via Verified Profile Fact Chunk

**Date:** 2026-11-03  
**Context:** Aamir's phone number was previously withheld across the knowledge base and system prompts due to an overly restrictive initial questionnaire entry, despite the phone number already being publicly present on his résumé (`resume.tex`). As a result, recruiters asking for contact details to schedule calls or reach out via WhatsApp were unable to obtain his number.  
**Options:**  
A. Unconditionally inject the phone number into the global system prompt template (would risk leaking the phone number in unrelated responses)  
B. Keep the phone number permanently withheld, forcing recruiters to rely solely on email or LinkedIn  
C. Enrich the `profile-contact` fact chunk with the verified phone/WhatsApp number (`+91 8904816279`), update Rule 5 in `system.txt` to permit sharing contact channels when requested, and rely on hybrid retrieval isolation ($top\_k = 4$) so the chunk surfaces strictly when contact or interview scheduling is requested.  
**Choice:** C — Authoritative contact fact chunk enrichment + dynamic retrieval isolation  
**Why:**  
1. **Strict Context Isolation:** For non-contact inquiries (e.g. FastAPI, Entropy-OJ, education, algorithms), `profile-contact` does not rank in the top 4 chunks, so the phone number is physically absent from the LLM's prompt and cannot leak.
2. **Authoritative Grounding:** When a recruiter explicitly requests contact channels, a phone call, or WhatsApp, `profile-contact` ranks #1, allowing the assistant to share the phone number alongside email and LinkedIn with full receipt attribution.
3. **Résumé Parity:** Resolves an artificial discrepancy with `resume.tex` (Line 54: `+91 8904816279`), providing recruiters a direct path to schedule interviews.

---

### DRN-030: Multi-Turn Coreference Query Rewriting & Stateless History Passing

**Date:** 2026-11-03  
**Context:** The chat endpoints (`POST /api/chat` and `/api/chat/stream`) previously accepted only a single user message string without conversation history. Follow-up queries containing pronouns or elliptical phrasing (e.g., "what about entropy in one line", followed by "tell me more") broke down because: (1) BM25 and dense embedding search on "tell me more" retrieved irrelevant overview chunks, and (2) the LLM was given zero conversational history, leading it to ask for clarification as if starting a fresh conversation.  
**Options:**  
A. Server-side session store (Redis or database) tracking message history by `conversation_id`  
B. Client-side state passing full history without query rewriting (passing history directly to LLM without search rewriting)  
C. Stateless client-side rolling history passing + heuristic follow-up detection with fast utility model query rewriting  
**Choice:** C — Client-side rolling history passing + heuristic follow-up query rewriting  
**Why:**  
1. **Zero Database Dependencies:** Adheres to Phase 1 architecture principle "keep the server stateless". The client passes up to 10 recent turns (`history` field on `ChatRequest`). The server trims this to a rolling 4–6 turn window, keeping token usage strictly bounded.
2. **Retrieval Semantic Alignment:** Hybrid search algorithms (BM25 + vector dot products) fail on short follow-ups like "tell me more" or "what was its stack?". The rewriter uses a fast regex heuristic (`is_likely_follow_up`) to avoid unnecessary LLM calls on self-contained queries, only invoking the utility model (`openai/gpt-oss-20b`) when coreference resolution is genuinely needed.
3. **Graceful Degraded Execution:** If the query rewriter times out or fails, the pipeline immediately falls back to the raw query without throwing 500 errors to the recruiter.

---

### DRN-031: Tokenizer Normalization & Markdown Formatting Invariants for Open-Weight Models

**Date:** 2026-11-03  
**Context:** When asked for contact details, `openai/gpt-oss-120b` occasionally emitted Unicode `\u202f` (Narrow No-Break Space) instead of colons and spaces, left bold tags unclosed (e.g., `- **Email aamirmkh25...`), or stripped protocol prefixes from URLs (e.g., `https.linkedin...`). Hand-crafted frontend markdown parsers (`FormattedMessage.tsx`) expecting standard markdown delimiters rendered these as raw unformatted strings.  
**Options:**  
A. Rely exclusively on system prompt instructions to fix model behavior  
B. Pull in a heavyweight third-party markdown library (e.g., `marked` or `react-markdown` with plugins)  
C. Defense-in-depth: explicit system prompt Rule 9 formatting invariants + backend token normalizer + frontend regex repair layer for non-standard whitespace, unclosed bold list tags, and URL protocol restoration.  
**Choice:** C — Multi-layer defense-in-depth formatting hardening  
**Why:**  
1. **Open-Weight Tokenizer Resilience:** Models trained on multilingual corpora frequently emit narrow non-breaking spaces before punctuation or numbers. Normalizing `\u202f`, `\u00a0`, and `\u200b` at the LLM adapter boundary (`normalize_llm_text` in `app.llm`) eliminates invisible whitespace corruptions across both streaming and complete calls.
2. **Resilient Parsing:** The frontend markdown tokenizer repairs unclosed bold tags on standard contact bullets and restores missing `https://` protocol prefixes, ensuring links remain clickable even if the upstream LLM drops punctuation.
3. **Zero Bundle Budget Impact:** Adding regex repairs in `FormattedMessage.tsx` adds 0 external dependencies, preserving the 112.90 KB gzipped bundle budget.

---

### DRN-032: Dossier View State Decoupling from Transcript Lifecycle

**Date:** 2026-11-03  
**Context:** In Phase 4, the Editorial Dossier UI used a shortcut where the landing hero view was defined as `isCoverState = messages.length === 0`. Navigating back to the dossier overview via `← Dossier Overview` called `resetChat()`, erasing the user's entire conversation transcript and clearing `sessionStorage`. Recruiters navigating back to check credentials lost their active multi-turn session.  
**Options:**  
A. Keep `resetChat()` as the return mechanism (forces recruiters to start over)  
B. Separate view routing (`viewMode: "cover" | "chat"`) from transcript data, adding a non-destructive navigation button and a "Resume Chat (N) →" entry point.  
**Choice:** B — View state decoupling with non-destructive navigation and resume entry points  
**Why:**  
1. **Preserved Recruiter Context:** Recruiters can freely navigate between reading the candidate dossier and conducting exploratory chat without losing their transcript.
2. **Clear User Intent:** Decouples navigation (`← Dossier Overview` sets `viewMode = "cover"`) from destructive action (`Clear Chat` explicitly wipes state and resets `sessionStorage`).
3. **Session Continuity:** If a recruiter returns to the Dossier Overview while a conversation exists, a prominent `Resume Chat (N) →` pill appears in the header, making context switching effortless.

---

### DRN-033: React Markdown AST Migration for Robustness & Anti-Regression

**Date:** 2026-11-03  
**Context:** In DRN-024, an in-house zero-dependency regex tokenizer (`FormattedMessage.tsx`) was chosen to parse markdown. However, Markdown is not a regular language. Over time, attempts to patch tokenizer edge cases (e.g. unclosed bullet bolding, loose lists with double newlines, nested asterisks, table line breaks) caused brittle regex interactions:
1. Regex replacements matching words inside bullet items inadvertently matched legitimate terms like `- **Availability**:` and `- **Work Focus**:`, mutating them into `Availabilit: y**` and `Work: Focus**`.
2. A single orphaned asterisk on `- **Location Preference**:` paired with subsequent bold text on the same line, corrupting `**Bengaluru, India**`.
3. Block list parsing broke on empty lines between items in loose lists, creating separate `<ol>` blocks that each restarted numbering at `1.`.
4. Glued numerals emitted by LLMs (`...are1. **AI-Assisted...`) were parsed as raw paragraph text rather than list items.
Meanwhile, copying response text succeeded because the raw LLM markdown was valid, proving the issue was strictly frontend parser brittleness.

**Options:**  
A. Continue patching the 630-line hand-rolled regex tokenizer  
B. Adopt the battle-tested `react-markdown` + `remark-gfm` ecosystem with custom component overrides matching existing design tokens  

**Choice:** B — Adopt `react-markdown` + `remark-gfm`  
**Why:**  
1. **Zero Regex Fragility:** Replaced 727 lines of fragile ad-hoc regexes with a declarative ~140-line component. Tables, loose lists, nested emphasis, code blocks, blockquotes, and link autolinking are handled by standard CommonMark/GFM AST parsers.
2. **Safe Loose Lists & Start Numbering:** Ordered lists with blank lines remain a single unified `<ol>`, and starting offsets (`<ol start={N}>`) are respected automatically.
3. **Bundle Budget Compliant:** Initial JS bundle increased from 112.92 KB to 162.88 KB gzipped, safely below the 200 KB gzipped ceiling (leaving 37.12 KB of headroom). Avoided heavy HTML parsers like `rehype-raw`/`parse5` by handling line breaks (`<br>`) via lightweight child processing.
4. **Backend Invariant Reinforcement:** Reinforced LLM output formatting in `system.txt` (requiring lists to start on newlines with preceding blank lines) and added regex normalization for glued numerals (`are1. ` -> `are\n\n1. `) in `normalize_llm_text`.


---

### DRN-034: Protocol Safe Normalization, Non-Destructive Formatting, and Session Storage Purge

**Date:** 2026-11-03  
**Context:** Following the adoption of `react-markdown` in DRN-033, user testing revealed edge-case formatting defects:
1. **Multi-segment domain truncation:** A legacy regex in `sanitizeMarkdown()` attempting to normalize bare domains only matched single-label domains followed by a hardcoded list of TLDs (`[a-zA-Z0-9-]+\.(?:com|org|io|dev|app|edu|in|net)`). On two-dot domains (`entropy-oj.vercel.app`, `health-prem-prediction.streamlit.app`), the regex failed to match across the first dot, truncating domain prefixes and generating corrupted URLs like `<https-oj.vercel.app>`.
2. **Double URL / relative link resolution:** When the model emitted `<httpsamirmk-portfolio.vercel.app>` without `://`, `ReactMarkdown` generated an `<a href="httpsamirmk-portfolio.vercel.app">`. Because the browser treats any URL lacking an absolute protocol scheme (`http://`, `https://`, `mailto:`) as a relative path to the current origin, clicking the link navigated to `https://aamirmk-portfolio.vercel.app/httpsamirmk-portfolio.vercel.app`.
3. **Session history poisoning:** When corrupted assistant outputs were emitted during earlier testing, `sessionStorage` stored them under `amk_portfolio_chat_session`. In subsequent turns, `useChat.ts` sent the last 6 messages in the `history` payload. In-context learning caused Groq (`openai/gpt-oss-120b`) to mirror the malformed syntax (omitted colons, missing bullets) in new answers.
4. **Negative prompt constraint activation:** The system prompt explicitly instructed the model: *"Never produce malformed links like `https.domain`"*. Mentioning negative token patterns activated attention weights on those exact sequences (the "pink elephant" effect), occasionally triggering the model to emit the pattern.

**Choice:**
1. **Extract `formatHelpers.ts` with Non-Destructive Sanitization:**
   - Completely removed destructive URL rewriting regexes from text pre-processing.
   - Limited `sanitizeMarkdown()` to safe Unicode normalization (`\u202f`, `\u00a0`, `\u200b` $\to$ space, `\u2011` $\to$ hyphen), glued numeral separation, and harmless closing of unclosed bold contact headers if missing closing `**`.
2. **Enforce Absolute URLs in `formatSafeHref()`:**
   - In `markdownComponents.a`, inspect every `href`. If a link lacks a protocol, normalize typos (e.g. `https.domain` or `httpsaamirmk...`) and prepend `https://` (or `mailto:` if an email). External links are guaranteed never to resolve relative to the portfolio root.
3. **Purge Poisoned Transcripts via Session Storage v2:**
   - Bumped `CHAT_SESSION_STORAGE_KEY` to `amk_portfolio_chat_session_v2` and explicitly purged legacy v1 transcripts on startup.
4. **Prescriptive Positive Invariants in `system.txt`:**
   - Replaced negative constraint warnings with positive, canonical markdown examples.
5. **Backend Normalization:**
   - Added non-breaking hyphen `\u2011` $\to$ `-` normalization in `backend/app/llm.py` `normalize_llm_text()`.

**Consequences:**
- Zero domain truncation or relative path resolution regressions.
- Bundle size remains 162.94 kB gzipped (<200 kB budget).
- All 125 frontend Vitest tests and 239 backend Pytest tests pass cleanly.

## DRN-051: Offline artifact and regression gates (Phase 8 Increment 5)

Aamir accepted the failed independent validation as the authentic baseline and formally
closed Increment 4; this does not change its gate, human grades or draft facts. Remaining
Phase 8 increments are authorized without additional briefs. `python -m evals.run --full`
combines actual local retrieval with eight recorded fake/curated contract checks. Typed
artifacts preserve individual outcomes, exclusions, split IDs, runtime and input hashes.
No generator executes; no generator accuracy is inferred. The initial compatible baseline
preserves all critical replay checks and existing retrieval thresholds; a drop exceeding
two percentage points fails. Changed fingerprint sets require explicit reviewed baseline
replacement, never automatic approval. CI runs root tests and the offline command, archives
its result, and enforces an initial-JS 200,000-byte gzip budget. Live scheduling stays off.

## DRN-052: Request-local observation without production quota claims

Phase 8 receipts measure server timings with a monotonic clock and separately report
browser timings. The LLM observer collects completion usage and consumes typed terminal
stream usage from the pinned Groq SDK (`extra_body.stream_options.include_usage`). Missing
counts, cancellations and provider failures remain unknown; partial individual calls stay
visible. Shared fit pipelines use a ContextVar installed/reset within each `__anext__`
invocation so heartbeat tasks and concurrent requests cannot share traces. Chat observers
receive their trace explicitly. Receipts contain no prompts, arguments, recruiter text or
private/unindexed source details. Fresh, cached, curated, refused and browser instant paths
are distinguished. Historical cached FitReports are copied with cached=True on delivery;
telemetry is added only to the event and is never stored in the report cache. This does
not fix production-wide quota reservations, SDK HTTP-attempt accounting or durable logs.
Original endpoint-v1/human packets are untouched; separate v2 fake-backed captures exercise
new telemetry through real frontend Zod/SSE contracts. Native details/summary provides the
collapsed keyboard disclosure in the existing dossier style.

## DRN-053: Result-backed publication remains an engineering record

Aamir explicitly accepted the independent validation failure and closed Increment 4,
then authorized the remaining offline milestone without further briefs. Completeness
and Tone remain 6/8; validation is not calibrated. The public projection recomputes
agreement from unchanged frozen human/judge data offline and preserves five disagreements.
No new provider calls, approvals of draft facts or claims of generator accuracy follow.

A typed allowlist projects actual offline results into backend/app/data/eval-summary.json.
The badge is derived by the backend (Replay checks: 8/8 (offline)); frontend Zod verifies
its equality and /evals shares the same projection. Publication here means generating a
local artifact; no remote publication is performed. Missing/malformed/mixed/partial/stale
artifacts return no numeric report. Source-result and projection hashes bind provenance;
runtime compatibility checks source/prompts, current corpus/index and key dependency
versions independently of Git availability. Hashes are integrity checks, not signatures.
Reserved content/IDs, raw recruiter text, raw answers, evidence and human rationales are
excluded; safe development-validation disagreement IDs/axes/labels remain visible.

Review expanded baseline fingerprints to cover evaluator/application code, v2 endpoint
contracts, current index/corpus/manifest and installed dependencies. Original scores were
asserted unchanged before replacing the identity map; floors and critical checks were
not lowered. The original initial baseline/result are preserved in local commit d3f249a.
Any future change requires explicit compatibility review, not automatic baseline updates.
The ten reserved cases remain author-visible and unexecuted, not an independent blind
assessment. A real factual accuracy badge still needs factual approval, supported human
labels, a reliable judge and compatible held-out generation evidence.

Review fixes within this increment: bind current assets before projecting old results;
preserve failed/cancelled fit receipts through Zod/SSE/hooks/modal; prefer server origin
over active preset when labeling fresh/generated-cache results; allow corrupt optional
index metadata to degrade to unknown. No production quota, persistence or broad safety
scope was silently included. Further Phase 7/9/10 work remains tracked separately.

### DRN-054: Boot-bound per-attempt inference admission

**Date:** 2026-11-06. **Scope:** Approved remaining Phase 7, Increment 1.

**Choice:** Keep a single-event-loop ledger with synchronous accounting transitions
and yielding only for bounded capacity waits. Reserve full serialized UTF-8 request
bytes plus framing headroom and capped completion tokens before each attempt. Enforce
shared and model-specific RPM/TPM/RPD/TPD plus active/queue bounds. A permit explicitly
marks dispatch; undispatched exits release capacity, while failed/cancelled/unknown
dispatched attempts retain reservations. Known usage reconciles once, without removing
request charges or reducing minute reservations. Input/output overruns stop further
admission and preserve at least the reservation/actual total.

**Restart policy:** DRN-017's fail-open restart behavior does not provide a daily
protection guarantee. New ledgers start closed. A fresh explicit remaining-capacity
allowance binds to a random process boot ID, expires by UTC midnight and is one-shot;
60 seconds drains unknown prior minute use. Wall-clock expiry and a monotonic deadline
both apply. There is no reusable environment grant or automatic next-day refresh.
Supabase durability remains P9. The app cannot meter arbitrary independent eval/API
processes; an allowance must deduct and coordinate their use. This is conservative
local control, not provider-account telemetry or an exact tokenizer guarantee.

**Interface and rollout:** `InferenceLedger.attempt()` owns admission/wait/cleanup;
the yielded permit dispatches and settles actual usage. Inject clocks/sleep for tests.
Pydantic models constrain budgets, costs, usage and allowances. Settings define ceilings,
not spending permission. Legacy route quota behavior stays until Increment 2 wires one
ledger and provider client into app lifespan; this increment alone changes no outbound
call path. No database or new dependency. Explicit code rules do not depend on a model.

### DRN-055: App-owned provider lifecycle and terminal stream accounting

**Date:** 2026-11-06. **Scope:** Remaining P7 Increment 2.

One lazy Groq client and ledger belong to each app, with Depends returning that client
and lifespan closing it. Fresh fit orchestration receives that client and an app-owned
cache, rather than retaining the first request's dependencies in a module singleton.
SDK retries are disabled and host pinned. Each complete call has a total 30-second
deadline including admission and at most one explicit <=5-second-hint 429 retry, each
with a new hold. Streams have a total deadline and no retry, avoiding duplicate output.
Utility rewrites get a two-second fallback deadline and explicit utility routing.

Reported models must match the admitted model. Inconsistent usage faults the ledger;
stream usage is only settled after complete validated iteration. Every forwarding
generator owns child closure, including explicit close while suspended after yield.
Unknown attempts stay charged; retry responses cannot make aggregate usage complete.
Receipts disclose successful attempt/unknown counts; counts on failures/cancellation
remain null rather than inventing a number. Per-request telemetry is still distinct
from global reservations. Old route quota estimates no longer control provider calls.

v3 fake-backed endpoint captures track the changed contracts without rewriting v1/v2
or human calibration evidence. Changed code invalidates the P8 numeric summary until
fresh compatible offline evidence and baseline identity review; no floors are lowered.
Default production generation remains resting without a boot-bound allowance. This
rollout does not supply durable accounting, operational activation or live acceptance.

### DRN-056: Explicit proxy trust and bounded abuse admission

**Date:** 2026-11-06. **Scope:** Remaining P7 Increment 3; qualifies DRN-015.

IP syntax does not establish header authority. Default to canonical socket identity;
only explicitly verified trusted networks and enabled proxy handling permit a bounded
right-to-left XFF walk. Duplicate/malformed fields fail back to the socket, vendor
headers have no independent authority, and mapped IPv4/IPv6 normalize consistently.
Disable Uvicorn's competing proxy rewrite. Real Render topology remains unverified:
deployment must not claim individual client limits until its chain is established.

Rate counters belong to each app and enforce IP plus optional opaque tab-session caps.
Both sit below shared inference capacity, so rotating sessions cannot bypass the IP or
global ceilings. Limit key count; fail closed for new keys at capacity rather than
evict active records. Tab IDs are abuse hints, not authentication or durable sessions.

Raw ASGI body bounds run outside BaseHTTPMiddleware and inside CORS: cap actual bytes
before JSON parsing, enforce a total read deadline and validate declared lengths and
session IDs. Body-read disconnect returns without a response; placing this inside
BaseHTTPMiddleware incorrectly produced `No response returned` server errors. No new
dependency, storage, authentication scheme or deployment trust assertion is introduced.

### DRN-057: Capacity-aware fallbacks and complete fit cache identity

**Date:** 2026-11-06. **Scope:** Remaining P7 Increment 4.

Expose typed resting state separately from HTTP service readiness. Authored starter
answers/presets and contact/résumé-source links remain useful without inference. A
forced live rerun bypasses caches and still crosses quota admission; no synthetic
generation or cache result is returned as live. Clear active preset identity on a
submission and ignore state callbacks after abort.

Generated reports use a bounded 64-entry/15-minute LRU and a hash of exact JD/title
plus source/fact/index/model identity. Do not use the legacy lowercased JD hash alone
as a cache key. Cached values are copied; transport receipts stay outside report state.
Authored examples are separate and need exact sample text/report-JD hash plus a
reviewed manifest binding current draft facts and report source. A sample/fact/report
edit invalidates the authored report in both preset projection and cache delivery.
The manifest preserves existing narratives and flags; it does not calibrate them or
promote facts. Runtime assets are immutable within an app instance; updates redeploy.

Fit's total deadline is 90 seconds across stages. A cancellation/timeout cannot insert
a partial report. New v3 fake contracts capture explicit delivery origin; old recorded
inputs and failed human/judge validation remain untouched. No new framework/storage,
provider calls, public factual-accuracy claim or deployment is implied.

### DRN-058: Structural data isolation and deterministic gap handling

**Date:** 2026-11-06. **Scope:** Remaining P7 Increment 5.

Escape structural characters and frame all untrusted channels as data, including
retrieved text inside the system prompt and client-provided assistant history. Explicit
system rules preserve the instruction/data distinction; this does not make prompt
injection mathematically impossible. Reject known lexical attacks before inference
across current/history/JD inputs. Private/unindexed chunks are excluded consistently
from prompt text, receipts and requirement-local evidence-ID maps.

The default tool uses a strict Pydantic argument model and catalog allowlist; arbitrary
keys, malformed Unicode, oversized arguments and nonobjects cannot execute. Registry
ownership is per app. Response/tool/rewrite bounds remain code rules, never model choices.

Existing negative/plans-only fact IDs do not establish positive hands-on evidence.
Downgrades replace unsupported explanations and ramp-up, rather than retaining a false
claim followed by a warning. Gap prose and gap-containing report summaries use fixed
templates and computed counts, removing unnecessary inference and invented timelines.
Positive semantic alignment/entailment still requires semantic evidence; source membership
alone cannot certify it. Draft facts and authored presets were not promoted or rewritten.
Development attack code checks and pending semantic cases are recorded separately.

### DRN-059: Privacy includes the server's independent log handlers

**Date:** 2026-11-06. **Scope:** Remaining P7 Increment 6.

Use temporary per-app HMAC IP hashes and validated 32-hex request IDs, route templates
and exception class names. Never log message/JD/history text or raw provider exceptions.
The JSON formatter omits traceback payloads. Root application configuration alone does
not govern Uvicorn's independent handlers: Render disables access logging, uses the
explicit `backend/logging.json`, and disables WebSockets for this SSE-only application.
SDK/HTTP client loggers use WARNING. A real isolated loopback Uvicorn regression checks
both an exception sentinel and a query sentinel. Platform/provider retention remains an
operational matter; no recruiter-message database or 90-day cleanup is added before P9.

Footer copy distinguishes the cache's 15-minute reuse TTL from data deletion: bounded
memory can retain an expired report until eviction/restart. Resting links point to the
existing professional profile/contact; the prior unauthenticated résumé repository
link returned 404. Public résumé PDF/source-link acceptance remains P10.

Move theme bootstrap to a same-origin external script and remove inline script permission
from production CSP. Connections permit only self plus the exact Render API; images
permit self/data and model Markdown images are suppressed. Keep inline style permission
for existing React styles. Source links reject unsupported schemes and control characters.
Browser-observed fallback contrast/ARIA landmark issues were fixed within the existing
design tokens; mobile axe reports zero violations, not a full accessibility certification.

### DRN-060: Adopt only the explicitly reviewed audit additions and update set

**Date:** 2026-11-06. **Scope:** Remaining P7 Increment 6; explicit user approvals.

Approved pip-audit 2.10.1 runs in an isolated environment against the complete installed
graph. The Gitleaks action is pinned to ff98106e4c7b2bc287b24eaf42907196329070c7,
scanner 8.30.1, with read-only permissions and comments/summary/report uploads disabled.
The owner is a personal GitHub User according to the checked API; no organization
license was invented. npm audit uses a high-severity CI threshold; Dependabot proposes
updates. No global installation, automatic audit fix or blanket advisory suppression.

The separate exact compatibility proposal was approved: FastAPI 0.135.0, Starlette
1.3.1, typing-inspection 0.4.2, annotated-doc 0.0.5, pytest 9.0.3,
pytest-asyncio 1.4.1.post1 and Vitest 4.1.11. Runtime pyproject dependencies now match
the pinned requirements. Preserve the existing HTTPX stack despite its TestClient
deprecation warning. Repeat Python audit found no known vulnerabilities; npm retained
nine moderate development-tool entries, zero high/critical. Current audit recommends
Vitest 4.1.12 and lint dependency updates; those further changes were not silently
substituted for the exact approved pins. Track findings rather than call npm clean.

### DRN-061: Review current safety replay and compatibility identity without lowering floors

**Date:** 2026-11-06. **Scope:** Phase-final offline artifact regeneration.

Current full evaluation explicitly selects the v3 safety capture. Historical v1/v2
records and the diagnostic replay default remain preserved. Strict event schemas now
accept optional typed RequestTelemetry on done/error frames, instead of rejecting the
P8 telemetry as an extra field. This is contract compatibility, not a permissive extra
field policy. A regression requires all eight current records to pass.

Fingerprint application/evaluator/prompt/recording changes, safety fixtures/curated
provenance/logging configuration and relevant FastAPI/Starlette/HTTPX versions alongside
the previous dependencies. Actual local retrieval plus eight-record replay reproduced
all seven original baseline scores exactly. The candidate gate reported only
`incompatible_baseline`; no critical check or numeric regression remained. The read-only
review checks the same comparison. Update identity and review reference only, preserving
numeric floors and the two-percentage-point tolerance. Commit source before generating
the final result/public projection. Held-out cases are reserved, model calls remain
zero, all 76 facts remain draft, and the five failed human/judge disagreements remain.

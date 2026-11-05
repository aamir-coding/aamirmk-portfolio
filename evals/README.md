# Offline evaluations — Phase 8, Increments 1–4 infrastructure

These increments supply frozen inputs, retrieval diagnostics, recorded-output
checks and calibration/budget infrastructure. Human grading is validated; the
first bounded live calibration run stopped incomplete. No model accuracy is
reported and no draft fact is certified.

## Dataset and approval status

- `cases/development.yaml`: 40 development cases (32 migrated legacy questions,
  eight authored behavior/regression cases).
- `cases/held_out.yaml`: 10 newly authored reserved cases, 20% of the 50-case set,
  in five groups absent from development. One of the 50 cases tests transport
  behavior; the others concern answers or fit reports.
- All labels are **provisional**. The 76 public indexed chunks remain draft.
  A source ID being valid proves identity, not factual approval or semantic support.
- The four existing curated fit reports are not evaluation ground truth. The two
  synthetic fit cases here specify conservative behavior, not calibrated verdicts.
- `seed_questions.yaml` remains the original 45-question development benchmark.
  None of those questions becomes held-out merely by changing its ID or origin.

The held-out file is author-visible in this repository. It is reserved from tuning,
not an independently supplied secret benchmark. Automated checks reject shared
groups, duplicate conversations and inquiries copied from any legacy seed.
Semantic paraphrase leakage still requires manual review; checksums cannot detect
it. Do not tune prompts, retrieval settings or rubrics against reserved outcomes.
Retire/version an exposed or tuned-against set before claiming independent quality.

## Commands (repository root)

```powershell
.\.venv\Scripts\python.exe -m evals.validate
.\.venv\Scripts\python.exe -m evals.validate --include-held-out
.\.venv\Scripts\python.exe -m pytest backend/tests/test_embedding_artifacts.py evals/test_cases.py -q
```

The default validator selects development cases only. `--include-held-out` permits
structural/source/hash validation of reserved cases, never answer scoring. Output
contains counts only. It reads the fact files and index metadata, without creating
an embedding model, contacting Groq or downloading assets.

Initial dataset creation uses `python -m evals.validate --freeze`. It refuses to
overwrite an existing lock. Subsequent versions require an explicit reviewed
manifest/schema update; automatic refreezing is deliberately unsupported in v1.
Keep reserved groups fixed while tuning development. A change to a provisional
label must create a reviewable version; passing tests is not human calibration.

## Contracts

Cases record an ID/version, semantic group, split, category/target, origin,
label-review status, conversation and checks. Unknown fields/categories, empty
content, invalid conversations, duplicate IDs and unknown/nonpublic source IDs fail.
No score is inferred from `support_expectations`; these are statements for future
human/semantic review. `must_include` and `must_not_include` are literal checks;
legacy prose prohibitions are preserved as semantic expectations rather than
silently converted to substring bans that could reject a correct denial.

`checks.sources.mode` distinguishes:

- `all_relevant`: all listed chunks belong to the provisional relevance set.
  Future Recall@k uses this set as its denominator.
- `any_of`: listed chunks are acceptable alternatives, preserving the legacy
  Hit@k interpretation. Do not report all-alternative coverage as Recall@k.
- `none`: no source-retrieval requirement applies, as for off-topic/protocol cases.
  This does not prohibit the running application from retrieving irrelevant context.

`expect_refusal` is separate from correction/abstention. A false-premise answer can
correct a claim without refusing the entire recruiter question.

## Frozen evidence

`manifests/dataset-v1.json` locks the case files, normalized case content, groups,
split assignments and legacy development file, plus the corpus/index snapshots.
Text fingerprints use UTF-8 with universal newline normalization so Git CRLF/LF
conversion preserves validity. Other textual edits still invalidate the lock.
The binary NPZ uses an exact byte hash.

`corpus-v1.json` records all 76 public IDs, draft flags and a canonical hash of
every parsed chunk field, including content and source metadata. It contains no
chunk text or new factual approval. `index-v1.json` records the NPZ hash and its
embedded build manifest: content/input/model/matrix hashes, dimensions, chunk
order, FastEmbed version, UTC build time and source commit/dirty state. The initial
build was made from the working tree at `88fae8c`, explicitly marked dirty; its
corpus and model inputs are fingerprinted. This is not a clean-commit accuracy run.

The builder and runtime share `app.retrieval.artifacts`. The legacy IDs-only index
was genuinely rebuilt from cached ONNX assets; metadata was not stamped onto
unverified old vectors. Runtime rejects missing/stale/legacy/corrupt artifacts and
never falls back to embedding the whole corpus. Production query embedding loads
local assets only and verifies their fingerprint against the index build. Injected
fake embedding models remain available to tests.

```powershell
.\.venv\Scripts\python.exe scripts/generate_embeddings.py --cache-dir <existing-cache>
```

This rebuild is local inference, not a Groq call. Missing model assets must first
be provisioned in an explicit build/setup step. Existing CI model setup is now
explicit before runtime tests; this session used already cached files and did not
download models. The runtime has no automatic model download. FastEmbed 0.9.1 lacks
a public snapshot-directory accessor, so the fingerprint helper isolates its
version-specific `model._model_dir` access and fails explicitly if unavailable.

## Remaining phase work

Increments 2 and 3 add retrieval diagnostics and recorded-output checks, described
below. Increment 4 infrastructure is implemented; human grading, genuine judge
agreement and separately approved live runs remain pending.
Combined result provenance/CI gates, telemetry and the panel/badge follow. No model
accuracy, live baseline, live workflow, schedule or badge is created by these
increments. Production quota/resource/lifecycle work remains tracked separately.

## Increment 2 — retrieval diagnostics

```powershell
$env:FASTEMBED_CACHE_PATH = '<existing-cache>'
.\.venv\Scripts\python.exe -m evals.run --output build/retrieval.json
.\.venv\Scripts\python.exe -m evals.run --suite legacy --max-mean-ms 25
```

The runner validates frozen inputs and uses cached local ONNX assets; it has no
live Groq mode or held-out execution flag. `--suite` selects `all` (default),
`legacy`, or `development`. Both development sets overlap and remain separate in
the report. It does not save or update a public `results.json` or badge. Optional
`--output` saves complete per-case diagnostics; stdout contains the summary.

Metrics are Hit@3/@5, MRR@5 and macro Recall@3/@5. Every score includes its numerator
and eligible-case denominator. Recall excludes alternative-source labels; empty
denominators produce null, not a perfect score. No-source cases, protocol cases,
fit JDs needing extraction and conversations needing recorded rewriting are
explicitly excluded from this raw-query measurement. No fake rewriting/extraction
is substituted into real results. This does not measure application guardrails,
semantic support, fit verdicts or generated answers.

Portable quality gates are Hit@3 >=0.90 and MRR@5 >=0.80. The legacy suite also keeps
its existing requirement that all 45 questions hit a listed source in the top five;
the individual regression tests remain. Warmed mean/p50/p95/p99 latency is reported
separately. The old default mean <25 ms assertion is replaced by the explicit
`--max-mean-ms` benchmark option, whose outcome is separately recorded in JSON.

The diagnostic includes commit/dirty status, retrieval-code hash, frozen dataset,
corpus/index identities, embedding model, runtime/library versions and fixed RRF
settings. Its type is `offline_retrieval_diagnostic`; label status remains
provisional, held-out execution is false and Groq calls are zero. This is an input
and retrieval measurement, not independently verified model accuracy. Complete
combined-run provenance and CI/publication gates remain Increment 5 work.

Exit status: 0 for passing requested gates; 1 for a completed measurement that
fails a quality or explicitly requested latency gate; 2 for an execution/provenance
error. Gate failures are still valid measurements and can be saved. An execution
error writes no new report and leaves an existing report unchanged; do not mistake
that earlier timestamp for a fresh successful run.

Implementation references checked against installed versions: Pydantic 2.10.6,
NumPy 2.5.4, FastEmbed 0.9.1 and PyYAML 6.0.3. PyYAML was already used by the
project; its installed version is now explicitly pinned as a direct dependency.

- [Pydantic 2.10 validators](https://docs.pydantic.dev/2.10/concepts/validators/)
- [NumPy load, including non-pickle loading and archive ownership](https://numpy.org/doc/stable/reference/generated/numpy.load.html)
- [NumPy compressed archives](https://numpy.org/doc/stable/reference/generated/numpy.savez_compressed.html)
- [FastEmbed official model implementation](https://github.com/qdrant/fastembed/blob/main/fastembed/text/onnx_embedding.py)

## Increment 3 — recorded-answer and contract replay

```powershell
.\.venv\Scripts\python.exe -m evals.replay --output build/replay.json
.\.venv\Scripts\python.exe -m evals.capture
.\.venv\Scripts\python.exe -m pytest -c backend/pyproject.toml evals/test_replay.py -q
.\.venv\Scripts\python.exe -m pytest backend/tests/test_recorded_events.py -q
# From frontend/:
npm test -- --run src/lib/backendEventFixtures.test.ts
```

`replay` parses committed bodies only: no application startup, model loading or
provider calls. `capture` exercises actual backend endpoints with isolated fake
dependencies and compares their bodies to `recordings/endpoints-v1.json`.
`capture --write` explicitly regenerates that file after review. It has no live
mode. TestClient intentionally skips production lifespan, since every request
dependency is injected; this does not verify deployment startup. On this Windows
host, async/TestClient checks require execution outside the previously diagnosed
sandbox socketpair deadlock. This is unrelated to network access or live models.

The eight captures contain seven fake answers/outcomes and one actual curated
preset response: chat project/card/colon/Unicode, rewritten follow-up, guard
refusal, model error, fresh and cached fit reports, curated preset, and failed
extraction. They bind to only **four unique development cases**; **36 development
cases have no recording**, listed in the diagnostic. Capture coverage is not
answer accuracy. Mutated test bodies additionally cover malformed JSON,
premature EOF, invalid citations, cross-requirement evidence, negative-only
positive judgments and summary/ramp-up overclaims. No held-out case is scored.

`checks.py` validates required/forbidden normalized substrings, character limits,
a deliberately narrow assistant-refusal pattern, citation identity/retrieval
membership, unique requirement IDs, production score arithmetic, local evidence
membership and explicitly configured negative-only evidence rules. Frozen case
expectations cannot be weakened by a recording's refusal/error overrides. A case
must bind to its version/hash, development split and matching transport.
Expected protocol/application errors still check the valid output prefix for
forbidden text, size and invalid citations; completion-dependent checks are
unavailable. Every result retains `semantic_review: pending` and
`generation_accuracy_available: false`. Neither valid membership nor passing
literal constraints proves semantic support.

Origin and delivery are independent. A fresh fake report is still fake; cached
delivery is identified from the real cache-hit progress event. The existing
`report.cached == false` defect is preserved and disclosed as
`server_cached_flag_unreliable`, rather than concealed by editing the capture.
The curated preset lacks its original requirement-local retrieval map, so that
check is unavailable; intrinsic citations, positive evidence, configured negative
rules and score arithmetic still apply. Curated content is not calibrated truth.
Fake token counts/adapter attempts are labeled synthetic; unknown/provider usage
is never inferred from character counts or failed calls.

The capture includes commit/dirty state, timestamp, corpus/dataset/prompt/source
hashes and case references. Replay adds its own commit/time, checker and recording
hashes, current-prompt compatibility, missing cases, origins/delivery counts,
failures/warnings/unavailable checks. A changed corpus or dataset is rejected;
changed prompts are disclosed, because replay still tests saved output. Complete
combined-run/runtime/model/rubric provenance remains Increment 5 work. The
stuffed-versus-RAG comparison is **unavailable**: no comparable authorized live
answer/usage recordings exist. No quality or token-savings number is invented.

Replay exits 0 when all applicable limited checks pass, 1 for completed check
failures, and 2 for unavailable/invalid inputs. An input error writes no result
and preserves any earlier file. Inspect timestamps and missing/unavailable
checks before using an artifact. These commands do not update a public result
or badge, and do not authorize Groq evaluation.

- [Zod schema parsing](https://zod.dev/basics)
- [SSE framing and UTF-8](https://html.spec.whatwg.org/multipage/server-sent-events.html#parsing-an-event-stream)
- [Starlette TestClient lifecycle](https://www.starlette.io/testclient/)

## Increment 4 — human calibration and a gated runner

Start with [human grading instructions](annotations/README.md), the frozen
20-answer calibration/eight-answer validation packet, and its blank annotation
template. These examples are **authored development inputs**, with intentional
errors and no agent-supplied human labels. They do not replace or execute the ten
reserved held-out cases. The group split is frozen before grading. The rubric
defines support, completeness, behavior and tone; human labels are authoritative.

```powershell
.\.venv\Scripts\python.exe -m evals.prepare_grading
.\.venv\Scripts\python.exe -m evals.calibration --annotations build/human-v1.json
.\.venv\Scripts\python.exe -m evals.live
```

The first command validates existing grading material; `--freeze` is write-once
initial creation and refuses overwrites. The second reports pending until genuine
grades/judge outputs exist. `--judge <judge.json>` compares saved judge output
offline; it never generates labels. The third prints offline-only/zero Groq calls.
None grants authorization. Human grading is complete; judge calibration remains
incomplete after the bounded run described below.

Agreement uses validation only, after twenty human calibration answers and twenty
judge calibration answers exist. It requires at least 80% agreement on every axis,
eight binary human validation labels per axis and both pass/fail classes. It shows
numerators/denominators, confusion counts, abstentions, missing labels and human
overrides. Human uncertainty is excluded; judge uncertainty is a disagreement on a
binary human label. Fake judges can only produce diagnostics. Same-family bias,
the small authored sample and draft evidence limit generalization even if the
eventual gate passes. Calibration does not establish generator accuracy.

The future runner has three explicit stages: `generation`, `judge_calibration`,
and `judge_validation`. Generation selects named development answer cases only;
protocol and reserved cases are rejected. It invokes the actual nonstreaming chat
route/tool/rewrite logic or a fresh fit pipeline/cache, using real cached local
retrieval in live mode. Streaming is deliberately disabled for live evaluation
because complete usage is required. Guardrail answers retain a distinct origin.
All automated tests inject fake providers/retrievers or SDK MockTransport.

The fit pipeline's extraction, alignment and summary calls pass through one
`MeteredLLM`, as do chat rewrite/tool turns. The current production chat rewrite
defaults to the main model; the ledger records that actual choice rather than
assuming a cheaper utility call. Evaluation judging uses 20b. Judge prompts
contain the answer, entire supplied evidence/local maps and compact rubric
definitions; they contain no human labels or other judge outputs. Exact rendered
system instructions have a separate fingerprint. Changing their construction
invalidates prior calibration even if `judge-v1.txt` itself is unchanged.

To prepare a **future unapproved** numeric proposal, provide a reviewed JSON
`Budget` (see `evals/budget.py`), then use:

```powershell
.\.venv\Scripts\python.exe -m evals.live --draft-plan build/proposed-run.json --run-id <unique-id> --budget <budget-file> --stage generation --cases <development-case-ids>
.\.venv\Scripts\python.exe -m evals.live --plan build/proposed-run.json
```

Judge proposals require `--stage judge_calibration --annotations <human-file>`.
Validation additionally requires `--prior-judge <completed-calibration-judge.json>`
and eight human validation grades. Prior output must be live, contain exactly the
twenty calibration items, and match packet/rubric/static/effective prompt hashes.
Full requested judge-slice reservations and prompt byte-policy feasibility are
checked before any proposal is written. No numeric budget or approval is supplied
by default. Test feasibility arithmetic is not an authorization or recommendation
for visitor headroom/output length.

A budget specifies, for each approved fixed model, attempt/input/output ceilings
and per-call input/output reservations; shared RPM/TPM/RPD/TPD, already consumed
daily requests/tokens, positive visitor reserves, pacing, request timeout and total
deadline. Both models share one conservative minute pool in this runner. Whole
per-call ceilings are reserved before every provider attempt and never refunded.
Reported usage is recorded separately. Prompt admission uses UTF-8 serialized
payload bytes plus a conservative overhead allowance; this is **not a tokenizer
measurement or a provider-enforced input cap**. Over-cap prompts are rejected,
and reported usage above a reservation stops the run. This limitation must be
explicitly acknowledged in any later budget approval. Output is capped through
`max_completion_tokens`; truncated output stops rather than becoming a score.

Execution additionally requires `--execute --approval <approval-file>` matching
the exact plan hash, explicit reviewer/reference, a current one-day authorization
window, fresh exact-account-limit evidence and acknowledgments for visitor
allowance, draft corpus and input reservation policy. It rejects dirty/changed
source, data, runtime or grading inputs. It reads the API key only from the process
environment after these gates; no key is accepted/stored in plans. The owned SDK
client pins Groq's host and disables SDK retries. Aamir authorized the first
twenty-answer proposal on 5 November 2026. It stopped after three calls/two grades;
that stopped authorization cannot be reused for another attempt.

Each provider error, timeout, cancellation, missing/inconsistent usage, model
mismatch, truncation or exhausted cap stops further attempts; production fallback
handlers cannot reset the ledger. Known usage stays known; uncertain usage stays
unknown. The overall deadline also ends at authorization expiry or UTC midnight.
Client cleanup is owned, and a known ledger is saved before awaiting closure so a
close failure/cancellation cannot erase it. Safe reason codes replace raw provider
exception text.

Receipts/results live only in ignored `build/eval-live`. A shared exclusive lock
prevents concurrent runner instances in this workspace. Unique run directories
are created before clients, so reusing a run ID cannot reset a budget. A conservative
60-second cooldown after prior completion preserves minute limits across runs;
unreconciled runs use their worst-case deadline. Current-day prior usage must
include known local reservations; interrupted runs charge full approved ceilings.
Runs intersecting UTC days count conservatively on both. A stale active lock or
uncertain receipt requires inspection; there is no automatic resume, lock clearing
or uncertainty reset. Do not delete/relocate receipts to reuse authorization.

This is a **standalone runner guard**, not the missing production-wide ledger.
It cannot measure concurrent visitor/other-workspace consumption; the later
operator must verify remaining account capacity, preserve real visitor headroom
and choose an appropriate run window. Native ONNX work in a thread is not forcibly
terminated by an asyncio deadline; no provider call is admitted after expiration.
Durable multi-host quota accounting, full publication provenance and result/CI
contracts remain separate tracked work. No live calibration, generator accuracy,
held-out outcome, public badge, schedule, push or deployment is implied here.

- [Groq SDK retry/timeout controls](https://github.com/groq/groq-python#retries)
- [Groq completion caps and usage](https://console.groq.com/docs/api-reference#chat-create)
- [Organization/account-specific rate limits](https://console.groq.com/docs/rate-limits)

### First live attempt and offline follow-up — 5 November 2026

`annotations/runs/calibration-2026-11-05-a/` archives the original receipt/result
and a partial-run summary. The run at clean `1927818` made **three** real 20b
requests, completed **two of twenty** grades and reported **2,306 input + 1,036
completion = 3,342 total tokens**. The third response used its full 512 completion
tokens and was rejected as incomplete. No request was retried or cap increased.
The old runner did not retain its exact finish reason, so none is invented now.
No validation, generator or held-out call occurred; no complete `judge.json`,
calibrated status or accuracy result was produced.

Future judge plans are schema v2 and require explicit `JudgeConfiguration`:
20b, temperature 0.2, JSON object format, `reasoning_effort: low`, and the approved
output cap. The SDK supports low effort; it is a mitigation, not a verified cure
for truncation. Generation retains its application settings. Each new attempt
records the provider finish reason. Plans, run results and judge artifacts retain
the configuration, and validation rejects settings/output caps differing from
calibration. Legacy plans/configurations are rejected rather than assigned guessed
defaults. The archived v1 run remains valid historical evidence, not a v2 result.

A fresh complete twenty-answer calibration is required under one explicit
configuration; the two older grades cannot be mixed into it. Human annotations,
examples, evidence, static prompt/rubric and split files are unchanged. The local
ledger conservatively holds the entire stopped run's approved ceiling for that
UTC budget day; this is **not** actual provider consumption. Do not delete its
build receipt, reset the hold, or reinterpret the unused allowance as permission
for retries. A new plan needs fresh approval and account capacity, normally in a
later UTC budget day. No follow-up live call has been authorized or made.

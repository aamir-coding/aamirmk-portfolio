# Phase 8 — Evaluation inputs and reproducible evidence

Incremental study guide. Increments 1–3 are covered here; calibration,
telemetry and result-backed publication will be added as implemented. Aamir waived
waiting for teach-back answers on 4 November 2026 once the material was verified.
This does not waive the separate human calibration grading required at Increment 4.

## Why a passing test is not an accuracy claim

There are three separate questions: is the input well formed, does the recorded
answer satisfy checks, and does the current model produce a supported answer?
Increment 1 addresses input/evidence integrity only. Later offline replay can
check saved answers, but a prompt change does not magically regenerate them.
Fresh model quality requires separately authorized generation and human-reviewed
judging. All 76 indexed facts and all 50 new case labels remain unapproved or
provisional respectively; a valid source ID cannot change that status.

## Case contracts and leakage

Read `evals/schemas.py` from top to bottom:

1. `CaseModel` forbids unknown fields. A misspelled expectation cannot silently
   vanish and turn a failing case into an easy pass.
2. `CaseTurn` and `CaseOrigin` distinguish conversation input from provenance.
   `ExpectedSources` separates all relevant evidence from acceptable alternatives
   and cases where retrieval is inapplicable.
3. `CaseChecks.support_expectations` holds semantic obligations. It is not a
   collection of passing judge labels. `expect_refusal` is separate from correcting
   a false premise.
4. `EvalCase.coherent_case` checks the case's execution contract: valid history,
   target/category, production input sizes, review reference and held-out origin.
   A synthetic JD supplies requirements, never a fabricated human verdict.
5. `CaseSuite.prevent_split_leakage` rejects duplicate IDs/conversations and shared
   groups. Splitting individual paraphrases randomly would leak the same task into
   both partitions; groups keep related examples together.

`dataset.py::_validate_legacy_overlap` compares reserved inquiries with **all** 45
known seeds, including the 13 not migrated into the new development YAML. Merely
declaring an origin to be authored cannot make an old example unseen. Semantic
paraphrases still need manual grouping review; hashes are identity checks, not
semantic classifiers. The current 10 reserved cases are author-visible and must
not be described as independently blind.

## Corpus/index provenance

Read `backend/app/retrieval/artifacts.py` alongside `dense.py`:

1. `embedding_text` defines the exact title/tags/content string embedded in both
   build and injected test paths. The manifest's format version names that rule.
2. `corpus_sha256` hashes every parsed fact field in ID order. A content edit with
   the same ID, a changed citation URL or a draft promotion invalidates the snapshot.
   Private/unindexed content is filtered by the existing loader before this step.
3. `_inputs_sha256` separately binds model identity and the strings embedded.
   Content provenance and matrix integrity answer different questions.
4. `model_assets_sha256` hashes the actual cached ONNX/tokenizer/config files.
   A model name alone does not identify the bytes used to generate vectors. Its
   access to FastEmbed's resolved directory is isolated and version-specific.
5. `write_embedding_artifact` validates normalized finite float32 vectors and
   writes their IDs, matrix and manifest together. The temporary file is replaced
   only after the archive is written.
6. `load_embedding_artifact` validates exact membership, model/library identity,
   corpus/input/matrix fingerprints and dimensions before reordering rows for the
   caller. It turns corrupt/truncated archive errors into an explicit rebuild error.
7. `DenseIndex.index` accepts a valid artifact or an injected fake. It no longer
   repairs a stale production artifact by unexpectedly embedding all facts.
   `_get_model` requires cached query-model files and checks their identity.

Hashing an old matrix and attaching today's fact hash would establish no connection
between the two. This increment reran local embedding on the exact fingerprinted
inputs. The build records its real source commit and dirty status; it does not
pretend to be an independently reproduced clean-commit accuracy run.

## Freezing and cross-platform reproducibility

`dataset.py::freeze_dataset` validates file-to-split membership, aggregate overlap,
legacy overlap and public source IDs before writing the corpus/index snapshots and
write-once dataset lock. The ordinary loader selects development only. Explicit
reserved validation checks structure/provenance without scoring or printing answers.

The first newline-conversion regression failed because Windows CRLF file bytes
differ from Linux LF bytes after Git checkout. Text files now hash UTF-8 text after
universal newline decoding; normalized case-content hashes remain unchanged. Binary
NPZ files retain byte hashing. This improves reproducibility without ignoring real
case edits. A hash is an integrity fingerprint, not an authenticity signature; Git
review remains responsible for deliberate manifest changes.

## Retrieval metrics — Increment 2

`evals/metrics.py::score_ranking` reads list order as rank and measures prefixes of
length three and five. Duplicate retrieved IDs are rejected, not counted twice.
For a relevance set `R` and prefix `T_k`, Hit@k is one when `R ∩ T_k` is nonempty,
and Recall@k is `|R ∩ T_k| / |R|`. Reciprocal rank is `1 / first_relevant_rank`,
or zero when the first five results contain no labeled source. MRR@5 averages this
truncated value over eligible queries; it is not untruncated MRR.

For ranking `[x, b, y, c, z]` and relevant set `{a,b,c,d}`, Hit@3 is 1, Recall@3
is 0.25, Recall@5 is 0.5 and reciprocal rank is 0.5. Finding one useful chunk and
finding the complete labeled evidence set are different questions.

`ExpectedSources.mode` decides the denominator. `all_relevant` labels contribute
to macro recall (each eligible query has equal weight). `any_of` labels contribute
only to Hit/MRR, because demanding every interchangeable alternative would invent
an exhaustive relevance judgment. `none` labels have no retrieval score. A metric
with no eligible cases has `value: null`, denominator zero and no passing claim.
`MetricMean.consistent_mean` rejects inconsistent serialized arithmetic.

`summarize_scores` uses separate denominators for Hit/MRR and recall. Per-category
results retain those denominators and excluded counts. The two development sets
overlap by design (32 migrated questions), so the runner reports them separately;
combining their scores would double-count many questions.

## Runner, exclusions and timings

Read `evals/run.py` in this order:

1. `load_legacy_cases` preserves all 45 existing questions as provisional
   alternative-source labels, deduplicating repeated IDs within a label. It does
   not rewrite the frozen seed YAML or relabel alternatives as exhaustive evidence.
2. `_skip_reason` excludes cases with no source expectation, protocol scenarios,
   JDs requiring LLM extraction and histories requiring recorded rewriting. Feeding
   a whole JD to the retriever or ignoring a conversation would measure a different
   task. The legacy one-message queries remain raw-query diagnostics, including
   legacy questions whose category was called follow-up.
3. `evaluate_suite` rejects reserved cases and duplicate inputs before retrieval.
   It warms the retriever separately, measures each eligible call with an injected
   monotonic clock, then uses the real `Retriever` interface and shared metrics.
   Empty results are misses; execution exceptions abort the run rather than quietly
   disappearing from the denominator. Source-ID hits do not grade generated prose.
4. `SuiteReport` retains per-case measured/skipped evidence, category results,
   thresholds and latency. Legacy quality still requires every top-five query hit,
   plus Hit@3 >=0.90 and MRR@5 >=0.80. Versioned development uses the latter two.
   There is no calibrated recall threshold on two provisional all-relevant labels.
5. `_latency_summary` reports warmed mean and nearest-rank p50/p95/p99. Warm-up is
   excluded; these numbers are neither cold-start measurements nor end-to-end chat
   latency. Machine-specific latency no longer fails ordinary quality tests.
   `--max-mean-ms` optionally supplies a separate explicit latency gate, recorded
   independently of quality in the JSON.
6. `build_report` validates frozen evidence, constructs the actual cached local
   hybrid retriever, and records commit/dirty status, retrieval-source hash, frozen
   manifest identity, corpus/index hash, library/runtime versions and fixed RRF
   configuration. `main` writes a complete diagnostic atomically, prints a summary
   and returns 0 for passing gates, 1 for a completed run with failed gates, or 2
   for execution/provenance errors. An aborted run does not overwrite a previous
   complete result. Always inspect timestamps/provenance; an old result is not a
   new successful run.

The report is explicitly `offline_retrieval_diagnostic`, with no held-out execution
or Groq calls. It does not update a public accuracy badge. The fuller combined
result/publication contract and CI regression baselines remain Increment 5 work.

## Interview questions

**Why keep retrieval metrics separate from answer correctness?** A relevant chunk
can be retrieved and then misread or ignored by the generator. Source membership
does not prove that a generated claim is supported, particularly with negative facts.

**Why not use curated fit reports as ground truth?** They are manually maintained
examples with repaired references/narratives, not independently human-calibrated
labels. Reusing them as both expectations and evaluated outputs would measure
self-consistency rather than accuracy.

**Why fail on a stale index instead of silently re-embedding?** It makes the build
contract observable and avoids hidden request-time downloads/full-corpus inference.
It does not establish general concurrency, readiness or 512 MB memory guarantees;
those production concerns remain deferred.

**Why is a perfect recall score over two cases weak evidence?** Its denominator is
tiny, the relevance sets are provisional, and it excludes the many alternative-only
labels. It says nothing about semantic answer correctness or unseen questions.

**Why remove the default 25 ms test assertion?** Quality should not fail because a
shared CI machine is temporarily slow. The runner still measures warmed latency,
and an explicit benchmark can enforce a chosen machine-specific ceiling.

## Increment 3 — what recorded replay actually measures

Recorded replay holds the output fixed and changes or reruns the checker. It can
show that saved output satisfies current deterministic checks. Fresh evaluation
holds inputs/configuration fixed and asks a model to produce output again. A
passing replay after a prompt edit says nothing about the new prompt's generation
quality. Our report therefore always says `generation_accuracy_available: false`.

There are two independent provenance axes. **Origin** describes who produced the
answer: injected fake, manually curated, or an authorized live model. **Delivery**
describes how it reached the caller: fresh, cached or preset. A fake answer on its
first request is fresh delivery without being live generation. A second request
can return that same fake answer from an isolated cache with zero new model calls.
Neither path creates a calibrated answer label.

Trace the implemented module interfaces in this order (line anchors refer to the
Increment 3 implementation; symbol names remain the stable navigation points):

1. `evals/checks.py:20`, `ReplayModel`, forbids extra fields/nonfinite numbers and
   freezes assignments. `RecordedUsage.honest_usage` requires both counts when
   usage is reported and rejects invented counts under `unavailable`. This is
   structural honesty, not proof that an external provider measurement is genuine.
2. `Recording.coherent_origin` separates transport, origin and delivery. Live
   records would need model/authorization metadata; the offline `CaptureBundle`
   rejects them entirely. Fake/curated records cannot claim provider token usage.
   Fake endpoint captures must bind to a versioned development case.
3. `evals/capture.py:70`, `TraceFakeLLM`, implements the existing adapter interface
   and counts synthetic attempts/reported fake usage. `CaptureRetriever` returns
   actual public chunk objects selected by scripted queries; its evidence map
   records which IDs each requirement query received. It is not real retrieval
   quality measurement; Increment 2 handles that separately.
4. `_capture_app` injects settings with an empty API key, fake adapters, request
   guards, a fresh tool registry/quota object and optional isolated fit pipeline.
   `capture_contracts` uses the actual routes/tool loop/fit pipeline, including
   history rewriting, extraction failure and a second cached request. TestClient
   is explicitly closed without entering lifespan. This deliberately tests request
   contracts, not production model initialization or rate/quota enforcement.
5. `evals/checks.py:208`, `decode_recording`, converts raw SSE frames into a typed
   `Transcript`, validating event-specific Pydantic payloads and exact terminal
   behavior. Chat terminal sources/cards must match earlier metadata. Colon text
   inside a JSON token is data; an SSE line beginning with a colon is a comment.
   Byte boundaries need not align with Unicode characters or events, which is why
   the frontend tests replay the UTF-8 bytes in one-byte and seven-byte pieces.
6. `ReplayProtocolError.prefix` retains events validated before an error. A stream
   that says a forbidden claim and then truncates must still fail the prohibition,
   even if EOF was expected. Positive completion requirements become unavailable,
   because absence in an incomplete answer is not an ordinary content failure.
7. `check_recording` binds case ID/version/hash, split, immutable refusal/error
   expectations and target transport before checking output. It then applies
   normalized literal fragments, length and narrow refusal detection, public
   citation identity, retrieved membership and requirement-local evidence maps.
   `compute_fit_summary` checks score arithmetic against production behavior.
   Summary, explanations and ramp-up text are all subject to literal prohibitions.
8. A positive fit verdict needs citations. A configured known-negative rule rejects
   a positive row supported only by the named negative chunks. These intrinsic
   checks still apply to curated reports. Missing curated retrieval traces make
   local membership unavailable, not a reason to skip every evidence check.
9. `evals/replay.py:73`, `load_recordings`, verifies the frozen dataset/corpus.
   `replay_report` records current checker/recording hashes and original capture
   provenance, discloses changed prompts and lists development cases without
   recordings. `main` saves atomically, returns 1 for failed limited checks and 2
   for unavailable inputs, and preserves old output on input failure.
10. `backend/tests/test_recorded_events.py` regenerates bodies through real routes,
    compares them to the committed file and captures twice to detect cache leakage.
    It also fails if capture constructs real Groq/embedding adapters.
    `frontend/src/lib/backendEventFixtures.test.ts` loads that exact JSON, uses
    production Zod schemas and the real streaming clients under mocked fetch,
    and checks truncated/corrupt terminals plus reader release. Fixture data is
    test-only and never imported into the shipped application bundle.

## Why the evidence checks are intentionally limited

Consider an AWS requirement. A citation to the real chunk saying Aamir lacks
hands-on AWS experience is a valid ID and may have been retrieved for that exact
requirement. Those two checks cannot justify a positive verdict. A configured
negative-only rule catches this particular mistake, while a semantic judge must
also assess the meaning of mixed, unrelated or misleading evidence and the
summary's broader claims. Literal fragment bans miss paraphrases; they can also
reject a legitimate denial when designed carelessly. They are regression checks,
not a universal entailment engine. Human-calibrated judging remains Increment 4.

Eight captures presently cover four unique development cases: seven are fake and
one is curated. The report lists 36 development cases without recordings. An 8/8
limited-check result therefore neither covers the entire suite nor measures model
accuracy. The existing cached flag defect is visible as a warning, and curated
local evidence is unavailable. No comparable authorized live stuffed/RAG answer
and token-usage pair exists; the comparison remains unavailable. Fake counts
cannot establish live token savings. All 76 public chunks stay draft, and no
held-out outcome is executed or used for tuning.

## Increment 3 placement questions

**Why use real routes with fake adapters?** They exercise serialization, tool
events, failures and cache behavior through the production interface while
keeping execution deterministic and avoiding provider costs. They do not measure
model reasoning, real retrieval rankings, quota correctness or production startup.

**Why keep a validated prefix after an error?** Otherwise an expected EOF/error
could erase a forbidden claim or invalid source already sent to the user. Checks
must distinguish obligations about emitted content from obligations requiring a
complete answer.

**Why bind the transport as well as the case hash?** An unchanged fit-case hash
does not prevent someone from attaching a chat recording to it. Enforcing both
prevents an easy chat response or early error from bypassing fit-specific checks.

**Why can a result pass with unavailable checks?** Passing means only that the
applicable deterministic obligations passed. Unavailable checks, missing cases
and semantic review remain separate fields. Publication must inspect those fields;
the engineering result cannot be relabeled as supported model accuracy.

## Optional Increment 3 practice — responses waived

1. A valid stream prefix contains an unknown citation, then ends before `done`.
   EOF is expected. Which checks must still fail, and which become unavailable?
2. A curated fit row cites only an AWS-negative chunk and claims `strong`.
   Its original retrieval map is absent. Which guarantees can still be checked?
3. All eight fake/curated captures pass after changing the generator prompt.
   What does that establish, and what remains required for an accuracy badge?

These questions support retrieval practice; no answers have been assessed and
none are required to continue under Aamir's waiver. Ask follow-up questions on
any step. Human calibration grading remains a separate required input.

## Optional retrieval practice — responses waived

1. A chunk keeps its ID but changes from “no hands-on AWS” to a positive claim.
   Which fingerprints must become invalid, and why does that still not approve it?
2. An old seed question receives a new ID and `origin: authored`. Why must it remain
   development material even when it is absent from the new development YAML?
3. A replay passes after the generation prompt changes. What can that result tell
   you, and what evidence is still missing before publishing model accuracy?

4. A query finds one of four relevant chunks at rank two. Compare Hit@3, Recall@3
   and reciprocal rank. How would an `any_of` label change what can be reported?

## Official references

- [Pydantic validators](https://docs.pydantic.dev/2.10/concepts/validators/): field and model validation contracts.
- [NumPy load](https://numpy.org/doc/stable/reference/generated/numpy.load.html): safe archive loading and context-manager ownership.
- [NumPy savez_compressed](https://numpy.org/doc/stable/reference/generated/numpy.savez_compressed.html): named arrays in one artifact.
- [FastEmbed official implementation](https://github.com/qdrant/fastembed/blob/main/fastembed/text/onnx_embedding.py): cached model loading and local-only configuration, checked alongside installed 0.9.1 source.
- [NIST trec_eval recall implementation](https://github.com/usnistgov/trec_eval/blob/main/m_recall.c): relevant retrieved divided by relevant at a cutoff.
- [NIST trec_eval reciprocal rank](https://github.com/usnistgov/trec_eval/blob/main/m_recip_rank.c): rank of the first relevant result; this project's explicitly named @5 variant truncates at five.
- [Zod schema parsing](https://zod.dev/basics): `parse` and `safeParse` validate actual backend payloads at the frontend contract.
- [SSE parsing standard](https://html.spec.whatwg.org/multipage/server-sent-events.html#parsing-an-event-stream): UTF-8 event framing and comment lines. The POST/fetch client and explicit terminal events are this application's additional contract; broad production CRLF/cancellation policy remains deferred.
- [Starlette TestClient](https://www.starlette.io/testclient/): lifespan runs when entering its context manager; the capture intentionally injects dependencies and skips that startup path. Checked alongside installed TestClient source.

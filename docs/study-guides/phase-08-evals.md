# Phase 8 — Evaluation inputs and reproducible evidence

Incremental study guide. Increments 1 and 2 are covered here; replay, calibration,
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

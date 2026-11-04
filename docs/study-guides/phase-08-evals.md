# Phase 8 — Evaluation inputs and reproducible evidence

Incremental study guide. Increment 1 is covered here; metrics, replay, calibration,
telemetry and result-backed publication will be added as implemented. Phase 8
teach-back is pending. Remediation teach-back/tagging also remain pending.

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

## Retrieval practice — completion pending

1. A chunk keeps its ID but changes from “no hands-on AWS” to a positive claim.
   Which fingerprints must become invalid, and why does that still not approve it?
2. An old seed question receives a new ID and `origin: authored`. Why must it remain
   development material even when it is absent from the new development YAML?
3. A replay passes after the generation prompt changes. What can that result tell
   you, and what evidence is still missing before publishing model accuracy?

## Official references

- [Pydantic validators](https://docs.pydantic.dev/2.10/concepts/validators/): field and model validation contracts.
- [NumPy load](https://numpy.org/doc/stable/reference/generated/numpy.load.html): safe archive loading and context-manager ownership.
- [NumPy savez_compressed](https://numpy.org/doc/stable/reference/generated/numpy.savez_compressed.html): named arrays in one artifact.
- [FastEmbed official implementation](https://github.com/qdrant/fastembed/blob/main/fastembed/text/onnx_embedding.py): cached model loading and local-only configuration, checked alongside installed 0.9.1 source.

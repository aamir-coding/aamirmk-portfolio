# Offline evaluation dataset — Phase 8, Increment 1

This increment supplies inputs and integrity checks. It does not generate answers,
run a judge, report model accuracy, or certify the current facts.

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

Increment 2 adds metric computation/runner behavior, described below. Replay checks and event
fixtures arrive in Increment 3; human grading and the separately budgeted live
runner arrive in Increment 4. Final result provenance/CI gates, telemetry and the
panel/badge follow. No score, baseline, live workflow, schedule or badge is created
by Increment 1. Production quota/resource/lifecycle work remains tracked separately.

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

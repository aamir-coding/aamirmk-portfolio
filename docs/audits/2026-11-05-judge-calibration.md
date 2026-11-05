# Judge calibration — axis-independent rerun completed

**Subsequent outcome:** Independent validation completed and failed Completeness/Tone.
See [validation results](2026-11-05-judge-validation.md). This report retains the
preceding calibration checkpoint and its historical metrics.

All **20 calibration answers completed in 20 attempts**, with no failures or
recoveries, at **17:38:26 IST on 5 November 2026**. The clarified prompt explicitly
forbids failing Behavior for factual falsity/unsupportedness; Behavior covers only
identity, injection resistance and refusal boundaries. Human labels are unchanged.

| Axis | Exact matches | Agreement |
|---|---:|---:|
| Support |18/20|90%|
| Completeness |17/20|85%|
| Behavior |17/20|85%|
| Tone |17/20|85%|

All four axes exceed 80% on this **calibration development slice**. The independent
eight-answer validation slice is still unexecuted; the formal gate is `insufficient`,
not a calibrated judge or generator accuracy result. No public accuracy badge.
The prior completed recipe scored 95%/90%/75%/85% respectively; the new run scores
90%/85%/85%/85%. This is an observed comparison, not a controlled causal study.

All eleven current disagreements and both rationales remain in `summary.json`:
Support09/10; Completeness05/10/18; Behavior08/17/20; Tone06/10/18. No label was
silently changed to improve agreement. In particular, a Support false positive
remains on10 and a false negative on09. Review semantics separately from coverage,
valid JSON, citations or passing development thresholds.

## Provenance

- Run: `calibration-2026-11-05-axis-independent`, clean source `d2db83d`.
- Model `openai/gpt-oss-20b`, temperature 0.2, low reasoning, max completion 1,024, strict JSON schema.
- Exact plan SHA: `4ada9aed95decadd680ab83466c3e7378675f82351a34af61ee8f5f2d0dbcada`.
- Effective instruction/schema recipe:
  `88926e448192c20befd86c38b92c68e6b67456773025a380091229b5f1d18f65`.
- Result SHA: `6595e3a051695b25d4e19d0edeb4a4a36920eda80577e9915bc9b71350655c67`.
- Judge SHA: `8cf7f7b0506624ab016c9a1025559b105976651e1d2287f53056dc5b06fb0e1d`.
- Ledger SHA: `762706ee9d156347a963299ec92c0fb5b999dfff82cfea71ff448ffc1ff76e09`.

Exact receipt/result/judge, runtime prefix/schema snapshots, summary, formal gate
report, HTTP progress and explicit usage reconciliation are archived in
[`evals/annotations/runs/calibration-2026-11-05-axis-independent/`](../../evals/annotations/runs/calibration-2026-11-05-axis-independent/).
Original receipt/result/judge bytes and canonical hashes match; normal prior-result
validation confirms exactly 20 calibration IDs and the actual recipe. The original
human fingerprint is unchanged and all 76 public fact chunks remain draft.

The prior recipe, full 20 judgments, two automatic recoveries and prior metrics
remain under `calibration-2026-11-05-v4-strict/`, with its exact old runtime/schema
snapshot and verified historical hash. Earlier partial attempts remain intact.
No earlier grades were imported into this fresh recipe.

## Budget and checks

The plan allowed 22 attempts/two recoveries,106,000 input+22,528 output=128,528 reserved,
zero visitors, and a 17:55:11 hard expiry. The largest complete input bound 6,973
fits 6,976; 20 base bounds91,643+two worst-case extras 13,952=105,595 fits 106,000.
Prior daily charge 71,238 included every historical unknown reservation; the new
projected daily maximum 199,766 stayed below 200,000.

Actual: **15,246 input+3,772 completion=19,018 reported tokens**. No new unknown
usage. All attempt reservations total 112,123 (91,643 input+20,480 output), within
component ceilings. Explicit completed-run reconciliation charges 19,018 actual,
leaving all earlier unknown reservations untouched. Across today's six runs:
**71 attempts,60,677 reported tokens+29,579 unknown-reserved=90,256 charged**.
This is local accounting, not independent provider-account telemetry.

Fresh pre-run checks: **477 backend/eval tests passed, one existing warning in
75.24s**; configured Ruff/formatter/diff clean. Automated checks used only fakes
and MockTransport; the authorized calibration above is separately recorded as
live. Read-only review ran 6 pure tests in 9.37s and found no blocker. Final artifact
audit confirmed hashes, plan/recipe binding, metrics, usage and all 20 IDs. No source
changed during execution; post-run changes are docs/artifacts only. No new
dependencies, validation/held-out calls, phase-completion tag, push or deployment.

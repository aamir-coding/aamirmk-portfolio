# Human calibration — twenty answers judged; validation pending

**Latest measured result:** Axis-independent calibration completed 20/20 in 20
attempts, no retries, 19,018 known tokens and no new unknown consumption. Agreement:
Support 18/20 (90%); Completeness/Behavior/Tone each 17/20 (85%). Every axis exceeds
80% on calibration examples; independent validation remains 0/8. Human grades
are unchanged. Full records/recipe/summary/gate report:
`runs/calibration-2026-11-05-axis-independent/`. Earlier updates are historical.


**Current outcome, 5 November:** Strict v4 collected all 20 grades in 22 attempts,
recovering two JSON 400 failures automatically. Exact agreement: support 19/20 (95%),
completeness 18/20 (90%), behavior 15/20 (75%), tone 17/20 (85%). No missing calibration
item; all eleven disagreements preserved. Known usage 19,363; two unknown requests
retain 14,067 reservations. Complete judge/provenance/summary/gate report are in
`runs/calibration-2026-11-05-v4-strict/`. Behavior is below 80% and independent
validation is 0/8; no calibrated/accuracy claim. Human labels unchanged.

**Earlier outcome, 5 November:** The explicitly approved same-day schema-v3 run
collected 19 grades in 20 attempts, then HTTP 400 with unknown final-request usage.
It reported 14,341 tokens and retained the failed request's 7,512 reservation.
See `runs/calibration-2026-11-05-schema-v3/` for exact records and all disagreements.
Partial development agreement: support 17/19, completeness 19/19, behavior 13/19,
tone 14/19. One item remains missing; no completed judge artifact, validation,
retry or calibrated status. Human labels remain unchanged. Earlier updates below
are historical; no stopped authorization is reusable.

**Update, 5 November 2026:** Aamir supplied all 28 attested grades. Offline schema,
hash and coverage validation passed; the unchanged submission is archived as
`human-v1-aamir-2026-11-05.json`. Validation labels have four passes/four failures
on each axis and no abstentions. Genuine judge outputs/agreement and separate live
budget approval were then pending. The original template below stays blank.

**Live attempt, 5 November 2026:** Aamir approved the twenty-answer calibration
proposal. It stopped after three calls and two accepted grades; all calls reported
usage, totaling 3,342 tokens. The third incomplete response consumed its full
512-token output cap. No retry or higher cap was attempted. See
`runs/calibration-2026-11-05-a/`. Calibration remains incomplete, validation is
unexecuted, and any new live attempt needs fresh approval. The offline follow-up
binds explicit low reasoning effort/output settings and records finish reasons;
it does not retroactively fill missing settings/reasons in the old run. Your
human labels remain unchanged and need no re-grading for this follow-up.

**Approved amendment:** Aamir requested 1,024 output tokens with low effort.
Concise runtime instructions retain the full evidence and rubric criteria and
keep the same total reservation. Aamir then explicitly requested immediate start;
the first run's known incomplete-output stop was reconciled with all attempted
reservations retained. Recovery ran at clean `d609e12` on **5 November UTC**
(despite its `calibration-2026-11-06-low` identifier). It stopped after one HTTP 200
response, 625 input/131 completion tokens, finish reason `stop`, zero accepted
grades. The generic task error's exception/output were not retained; the exact
cause is unknown. See `runs/calibration-2026-11-06-low/`. Combined actual usage is
four calls/4,098 tokens. No retry occurred; both approvals are consumed. Offline
follow-up adds explicit JSON shape and safe diagnostics without changing grades.

The committed template contains **no human grades**. Aamir chose to fill a copied
JSON file on 4 November 2026. `build/human-v1.json` is an ignored working copy;
it is never overwritten by the tooling. Other filenames are accepted explicitly.

1. Read [the rubric](../rubrics/support-v1.md), then review the
   [20 calibration answers](calibration-v1.md). Review the
   [eight validation answers](validation-v1.md) independently. These are authored
   examples, including deliberate defects; none is an actual model answer or a new
   fact. The two slices contain separate development groups, not the project's
   reserved held-out cases. Do not tune against validation outcomes.
2. In a copy of `human-v1.template.json`, fill your `reviewer` identity and an
   `attestation` in your own words confirming independent grading. For each item,
   replace `labels: null` with an object containing `support`, `completeness`,
   `behavior` and `tone`, each exactly `pass`, `fail` or `uncertain`.
3. Fill a nonempty `rationale` explaining the judgment with claim/evidence IDs.
   Preserve all packet/rubric/item hashes and item IDs. You may leave unfinished
   items null; tooling will report pending coverage. Do not force a binary answer
   just to pass a gate. Report flawed/stale evidence for review separately.
4. Provide the completed file's path. Validation is offline:

   ```powershell
   .\.venv\Scripts\python.exe -m evals.calibration --annotations build/human-v1.json
   ```

Exit 1 with `status: pending` is expected until the human and judge inputs exist;
exit 2 means invalid/stale input. No model client is created. Human grading alone
does not run a judge, approve the corpus, or grant a live budget. The fixed
120b/20b pair remains; the evaluation judge is 20b, independently of the fit
pipeline's existing 120b alignment stage.

`packet-v1.json` is locked by its canonical hash. `prepare_grading --freeze` refuses
to overwrite existing material. Source changes to the packet/rubric/prompt/corpus
require a reviewed new version, not edited hashes. `prepare_grading` without flags
only validates the frozen packet. Effective system instructions are additionally
fingerprinted in judge results, including compacted rubric definitions.

Agreement uses the separate validation slice only after at least 20 human
calibration grades **and 20 calibration judge outputs** exist. It reports four
per-axis numerators/denominators, confusion counts, human abstentions, missing judge
labels and human overrides. Judge uncertainty is a disagreement on binary human
labels. Human uncertainty is excluded; sufficient coverage still requires eight
binary validation labels and both human pass/fail classes on every axis.
At least 80% agreement on each axis is the frozen project threshold. Missing or
insufficient labels never become a pass. A fake judge produces a diagnostic only,
even at perfect agreement. A failed/insufficient validation run needs reviewed
new calibration/validation material rather than tuning to these exposed outcomes.

The authored examples deliberately include obvious counterexamples and are small,
author-visible development material. Agreement is a limited calibration signal,
not a statistically reliable estimate of production accuracy. Human labels are
relative to supplied draft evidence; all 76 facts remain draft. Future publication
still needs approved factual provenance, genuine held-out outcomes and compatible
complete result evidence. No human labels or real judge outputs were supplied by
the agent.

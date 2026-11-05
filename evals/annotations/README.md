# Human calibration — grading received, judging pending

**Update, 5 November 2026:** Aamir supplied all 28 attested grades. Offline schema,
hash and coverage validation passed; the unchanged submission is archived as
`human-v1-aamir-2026-11-05.json`. Validation labels have four passes/four failures
on each axis and no abstentions. Genuine judge outputs/agreement and separate live
budget approval remain pending. The original template below stays blank.

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

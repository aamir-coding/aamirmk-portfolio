# Schema-v3 calibration attempt — 5 November 2026

The authorized same-day run collected **19 schema-valid grades from 20 attempts**.
The final request returned HTTP 400. This is a partial calibration result, not a
completed/calibrated judge and not generator accuracy. No automatic retry,
validation call or held-out call occurred.

## Execution and budget evidence

- Run: `calibration-2026-11-05-schema-v3`; clean source `be132d5`.
- Plan SHA: `a918599db21437812857c2a77fefb640e30d43f5ce0f8233bf475e60786eb5f0`.
- Fixed 20b model, temperature 0.2, low effort, JSON object, 1,024 output cap;
  runtime v3 and complete frozen evidence/human labels unchanged during execution.
- User explicitly authorized actual-usage reconciliation of the earlier four
  calls (4,098 tokens), zero visitor reserves, and this fresh twenty-call run.
  Earlier receipts/results and attempted reservations remain preserved.
- New run: 11,962 reported input + 2,379 reported completion = **14,341 known tokens**.
  Request 20 (`calibration-20`) has unknown usage; its full **7,512-token**
  reservation remains charged. The stopped run retains its full conservative
  150,240-token local hold and cannot use fully-reported reconciliation.
- Across today's three attempts: **24 requests, 18,439 reported tokens plus one
  unknown-consumption request**. These are observed local records, not an
  independent measurement of account-wide remaining capacity.
- Finished at **12:59:15 IST**, before the approved 13:20:28 IST expiry.

The exact receipt, result, last HTTP progress record and derived diagnostic
summary are in
[`evals/annotations/runs/calibration-2026-11-05-schema-v3/`](../../evals/annotations/runs/calibration-2026-11-05-schema-v3/).
The result's attempt ledger is SHA-bound; the summary binds the complete result.
No `judge.json` was produced. No partial record is relabeled as a complete result.

## Agreement on the 19 observed calibration answers

| Axis | Exact matches | Observed denominator | Missing from intended 20 |
|---|---:|---:|---:|
| Support | 17 | 19 | 1 |
| Completeness | 19 | 19 | 1 |
| Behavior | 13 | 19 | 1 |
| Tone | 14 | 19 | 1 |

These are **development diagnostics**, not the eight-answer validation gate.
Even if the missing grade matched every human label, behavior could reach only
14/20 and tone 15/20. A single additional successful request would not establish
adequate agreement on these axes. The separate eight-answer validation slice
remains unexecuted; no tuning against its model outcomes has occurred.

The summary retains all 13 item/axis disagreements with both rationales, rather
than silently changing the human labels. Support disagrees on items 06 and 09;
behavior on 05, 06, 08, 10, 14 and 18; tone on 05, 06, 10, 12 and 18.

## Findings and next calibration work

1. **HTTP failure cause is unknown.** The status-only progress record establishes
   HTTP 400 on request 20, but the old provider adapter discarded the exception
   details. Do not infer JSON validation failure, rate limiting, refusal or zero
   consumption. Offline follow-up retains safe exception class/status and selected
   error codes for future runs, excluding messages/body/failed-generation text.
   It does not reconstruct the lost response.
2. **Schema validity is weaker than judging quality.** Several accepted rationales
   merely repeat citation IDs or the template's `cite IDs`. That meets the current
   nonempty-string boundary but does not explain claim-to-evidence support. Other
   rationales mix lack of support/completeness with behavior, or miss insulting
   language despite failing the factual claim. The recorded disagreements expose
   this; no additional model calls are needed to identify the weakness.
3. **Review a calibration-only prompt revision before spending more.** A candidate
   should explicitly identify the supplied `answer` as the object being graded,
   distinguish the four axes, preserve the full behavior/tone criteria, and request
   specific claim/evidence reasoning rather than an ID-only placeholder. Verify
   its complete-input reservation offline and review its exact budget. This is a
   recommendation; no new prompt version or model run is silently substituted.
4. **Keep human authority and validation separation.** Preserve every original
   human grade. If a label interpretation needs adjudication, record it explicitly
   with the user rather than editing labels to improve agreement. New live calls
   need a new explicit budget/approval; the twenty-attempt authorization is consumed.

All 76 fact chunks remain draft. No publication badge, production change, phase
completion, remote push or deployment follows from this result.

# Judge calibration result — all twenty answers collected

The strict v4 calibration run completed **all 20 answers in 22 attempts**, recovering
HTTP 400 `json_validate_failed` on items 05 and 20 without pausing for user action.
It finished at **16:24:58 IST on 5 November 2026**, before the 16:37:18 deadline.
This completes the requested collection run. It does **not** pass the calibration
quality gate: behavior agreement is below 80% on this development slice, and the
separate eight-answer validation set has not been model-judged.

## Agreement with Aamir's unchanged human labels

| Axis | Exact matches | Denominator | Agreement |
|---|---:|---:|---:|
| Support | 19 | 20 | 95% |
| Completeness | 18 | 20 | 90% |
| Behavior | 15 | 20 | 75% |
| Tone | 17 | 20 | 85% |

No item is missing; all eleven item/axis disagreements and both rationales are
preserved in the derived summary. These are authored calibration examples, not
live generator accuracy or factual approval. The formal agreement report remains
`insufficient`: calibration judged 20, validation judged 0. No accuracy badge is
available. Human labels, including disagreements, are authoritative and unchanged.

The behavior disagreements are items 06, 08, 10, 12 and 14. Four have human pass /
judge fail; item 08 has human fail / judge pass. Several model rationales assign a
behavior failure because an answer is factually wrong, mixing support with the
identity/privacy/injection/refusal axis. Tone still disagrees on items 06, 08 and
10. Support disagrees on item 09; completeness on 08 and 13. Review these
calibration interpretations before another live budget. Do not edit human labels
to improve agreement or tune against unseen validation model outcomes.

## Exact configuration and provenance

- Run: `calibration-2026-11-05-v4-strict`; clean source `28fd20c`.
- Model: `openai/gpt-oss-20b`, temperature 0.2, low reasoning, 1,024 completion cap.
- Response format: strict JSON schema derived from typed grade/labels; local
  validation retains nonblank rationale. The separate `judge-v4-strict.txt` retains
  the user's explicit behavior/tone/rationale requirements. Used v4 remains intact.
- Plan SHA: `35c3af183b951e6ccd7fcbcdfff4f9cb3927187ecf1e56d7fdd21b39890f2f4b`.
- Recipe SHA (actual instructions plus actual schema):
  `4e1594a36321794a3a61494b0c8a5456743f61f42d5d7e207c93bf7cbf4346cd`.
- Result SHA: `9613df9839ae28e44c08ed777553fa971787fb8bb4c93d5c889580bddc60d60c`.
- Ledger SHA: `5d28588cfe0fd6705c643eef05038cd7556a3e1ee7a960975b6135c6290d7ed0`.
- Judge SHA: `9388a686663570daac88420bfc7b46760cf8091148d2fa64f82f173176194db0`.

Exact receipt/result/judge, HTTP progress, diagnostic summary and formal gate
report are archived in
[`evals/annotations/runs/calibration-2026-11-05-v4-strict/`](../../evals/annotations/runs/calibration-2026-11-05-v4-strict/).
Archived receipt/result/judge bytes match the original build artifacts. All twenty
IDs/item hashes and the effective recipe pass normal prior-result validation.
The original human fingerprint is unchanged; all 76 public facts remain draft.

## Quota and recovery evidence

- Maximum authorized continuation: 24 attempts / 160,000 tokens, zero visitors;
  projected daily maximum 197,808 including earlier unknown reservations.
- Actual: 22 attempts; 20 accepted responses; two recoveries under the same ledger,
  deadline and rolling minute gate. No SDK-hidden retry or quota reset.
- Reported: **15,306 input + 4,057 completion = 19,363 tokens**.
- Two failed requests have unknown consumption; retain **14,067** full calculated
  request reservations. Their error bodies/hidden generation were not captured.
- All attempt reservations: 103,262 input + 22,528 output = **125,790**, within
  the 135,424 / 24,576 component ceilings. No failed reservation was refunded.
- Across today's five runs: 51 attempts, **41,659 reported tokens** and four
  unknown requests retaining **29,579** reservations. These are local evidence,
  not independently measured account-wide remaining capacity.

The strict run still encountered provider JSON validation errors. Its bounded
recovery succeeded; do not claim strict mode eliminates every provider failure or
infer an output cutoff from a 400. Full input/schema bounds remain at most 6,953,
under the 6,976 cap. Earlier v3/v4 partial grades are not mixed into this result.

## Historical partial runs

The v3 run collected 19/20 before an unclassified HTTP 400; its original body was
not retained. The first v4/JSON-object run collected 4/20 before a safely identified
`json_validate_failed` (3,857 known tokens plus 8,000 unknown-reserved). Exact
historical records remain under their distinct run directories. The earlier two
runs likewise remain preserved; no missing grade or finish reason was invented.

Offline verification for the final implementation: **473 passed, one existing
warning in 67.40s**; configured Ruff and formatter passed. Read-only reviews checked
schema provenance, emitted hashes, recovery limits and reservation arithmetic.
All automated tests use fakes/MockTransport. No new dependencies, factual approval,
validation/held-out calls, public badge, phase completion tag, push or deployment.

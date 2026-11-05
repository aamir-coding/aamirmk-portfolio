# Independent judge validation — completed, gate failed

All eight frozen items (`validation-01` through `validation-08`) completed in
**8 attempts with no failures/recoveries**, at **17:59:38 IST on 5 November 2026**.
The prompt, response schema and model configuration exactly match the accepted
calibration recipe. All 20 earlier calibration grades were carried forward unchanged;
only eight new model calls were made.

| Axis | Exact agreement | Percentage | Meets 80% |
|---|---:|---:|---|
| Support |8/8|100%|Yes|
| Completeness |6/8|75%|No|
| Behavior |7/8|87.5%|Yes|
| Tone |6/8|75%|No|

**Formal gate: `failed`; `live_judge_calibrated: false`.** With eight binary human
labels, an axis needs at least 7/8 to meet the 80% floor. Each axis has four human
passes/four failures; there are no human abstentions, missing model labels or
coverage deficiencies. One Completeness judgment is `uncertain`, a valid model
label that counts as disagreement against a binary human label. The completed
execution is not an implementation error and is not a calibrated success.

## Disagreements and interpretation

Five item/axis disagreements are preserved with both rationales:

- `validation-06`: Completeness human fail/model uncertain; Tone human fail/model pass.
- `validation-08`: Completeness, Behavior and Tone human fail/model pass.

For 06, the model recognizes first-person impersonation but calls the fabricated
recipe response professional/courteous and is uncertain about its completeness.
For 08, its rationale acknowledges the unsupported embedded/firmware claims and
quotes a recruiter-directed insult, yet labels tone professional and behavior
acceptable. Support correctly fails both. These are semantic judging weaknesses,
not JSON or transport failures. All original human labels remain unchanged.

Do not retry valid judgments, select favorable samples, or retune the prompt
against this exposed validation set and report it as independent success. Under
the frozen rubric, further calibration needs a reviewed new validation version
with independently supplied human grades. No new prompt/labels/split or further
model calls were made in response to these scores.

## Configuration and provenance

- Run: `validation-2026-11-05-axis-independent`; clean source `4d80320`.
- Fixed `openai/gpt-oss-20b`, temperature 0.2, low effort, 1,024 completion cap;
  identical strict schema and `judge-v4-strict.txt`.
- Recipe SHA: `88926e448192c20befd86c38b92c68e6b67456773025a380091229b5f1d18f65`.
- Prior 20 judge SHA: `8cf7f7b0506624ab016c9a1025559b105976651e1d2287f53056dc5b06fb0e1d`.
- Exact approved plan: `66af1537d61003f2372629ad62af64cefa42ed3587f141919f5fe450fecefe25`.
- Result SHA: `65e539e299445f5bc4c3173e5580156b47383d0c83ea9f4d874bf5c2f7c5523a`.
- Judge SHA (20 prior+8 validation): `8038a742c46b9ccb30151f0635a49851b11933ead268144088e6667c625c727a`.
- Ledger SHA: `c9db5d1f4bc91c1888f14d2afece8d54e745f6d2487f5beec7c917b457b4fcef`.

Exact receipt/result/judge, formal agreement report, summary, prior judge,
input-provenance map, runtime/schema, HTTP progress and usage reconciliation:
[`evals/annotations/runs/validation-2026-11-05-axis-independent/`](../../evals/annotations/runs/validation-2026-11-05-axis-independent/).
Original bytes/canonical hashes, prior 20 equality, all eight IDs, human hash and
recipe/configuration compatibility were verified. Read-only independent artifact
audit reproduced the failed gate and found no artifact blocker. Human grades and
all 76 public draft facts are unchanged. No generator answers were evaluated;
these are authored development validation examples, not portfolio accuracy.

## Budget and verification

Aamir explicitly authorized the eight answers, recoverable retries, actual-use
reconciliation and zero visitors. The numeric plan allowed at most 12 attempts/four
recoveries and 83,712 input+12,288 output=96,000tokens. Prior 90,256 included every
historical unknown reservation; projected daily maximum 186,256 stayed below 200,000.
Eight complete input bounds sum 40,315; four worst-case extras give 68,219 <=83,712.
Maximum input bound 6,956 <=6,976; output cap and 8,000 TPM unchanged. Hard expiry was
18:34:35 IST, comfortably after completion. No source changed during execution.

Actual usage: **7,003 input+1,379 completion=8,382 reported tokens**, no new unknowns.
Attempt reservations 48,507 (40,315 input+8,192 output) remain below the declared
ceilings. Explicit reconciliation charges 8,382 actual while keeping all 29,579 older
unknown reservations. Across seven runs: 79 attempts,69,059 known+29,579 unknown-reserved
=98,638 charged. This is local accounting, not independently observed provider
remaining capacity. No SDK-hidden retry, quota reset or visitor reserve was used.

Fresh offline validation-stage tests: **3 passed in 6.83s**, fakes/MockTransport only.
The earlier full 477-test pass is historical for this unchanged implementation,
not a newly run full suite. Focused checks and normal input/recipe validation
passed before live execution; post-run checks reproduced all denominators/confusion
counts and source bindings. No code/dependency changes, prompt tuning, public
badge, phase-completion tag, push, deployment or Increment 5 work.

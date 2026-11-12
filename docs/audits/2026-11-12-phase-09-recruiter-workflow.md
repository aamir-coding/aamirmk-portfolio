# Phase 9 review — recruiter workflow

12 November 2026. Reviewed local build `1a3b91d` against the
[Phase 9 acceptance criteria](../implementation-plan.md#phase-9-handoff-per-company-links-forwardable-summary-and-analytics).
The architecture review was read-only. Local tests used disposable PostgreSQL
18.4 and injected model or notification fakes. Hosted verification is pending.

## Acceptance evidence

| Criterion | Verified locally | Hosted evidence still needed |
| --- | --- | --- |
| An unanswerable question reaches Aamir with context | At 390 px, a low-evidence question opened the preview. Submission stayed disabled until consent. The browser showed “Request received,” and the recording notifier checked the original question and synthetic reply address. The Postgres integration test covers pending-row restart recovery. | Match the saved UUID to a message received in the intended private Telegram chat. |
| A company link changes the greeting, prompts, and projects | `?for=ecolab-5a2b` displayed the Ecolab greeting, three prompts, and both selected projects. The unknown-slug cover text matched the default cover. Backend tests check the same authored note in JSON and SSE prompts. | Verify on the intended Vercel and Render revisions with the deployed origins. |
| A summary opens on a phone, prints as one page, and expires | A second browser session opened the link at 390 × 844 without a login, cookie, or horizontal overflow. The API returned `200`, `noindex, nofollow`, `no-store`, and `no-referrer`. Chromium produced one readable page with résumé links and no share URL in text or link annotations. The Postgres test forced the expiry timestamp and got the same `404` as an unknown link. Increment 5 also verified both A4 and US Letter. | Test on a physical phone, check frontend and API response headers, and verify a deliberately expired synthetic link and its removal by the hosted cleanup. |

The PostgreSQL suite also exercised migrations and schema drift, analytics and
feedback, concurrent quota grants, an interrupted boot, and idempotent cleanup.
The Increment 7 restore rehearsal verified that the archived schema restored to
revision `0004`, stale rows were purged, current quota remained, and health,
admin, and a synthetic summary lookup returned `200`. [Increment 7 evidence](../PROGRESS.md#phase-9-increment-7--12-november-2026)

## Fresh checks

| Check | Observed result |
| --- | --- |
| `python -m pytest -q -c backend/pyproject.toml backend/tests evals` with `PORTFOLIO_TEST_DATABASE_URL` | `697 passed, 2 warnings in 174.72s`. Both warnings are existing Starlette test-client deprecations. |
| `npm test` | `24 passed (24)` files and `190 passed (190)` tests. |
| Configured Ruff check and format, ESLint, TypeScript/Vite build | `All checks passed!`, `132 files already formatted`, frontend lint and build exit `0`. The existing Rollup dependency annotation and uncompressed chunk-size warnings remain. |
| `node scripts/check-bundle.mjs` | `Initial JavaScript: 171362 gzip bytes / 200000`. |
| `python -m evals.run --full --output build/evals/phase9-review.json` | `gate_failures: []`, all seven scores unchanged, held-out cases reserved. |

The fresh eval result is local and ignored. The published projection still
points to its matching clean build source `66c67fb`. No live Groq evaluation,
Telegram delivery, or hosted scheduling ran during the review.

## Architecture findings

1. **P2 · Pending delivery can outlive the handoff retention window.** The
   worker selects any pending row. When cleanup has missed a run during a
   database pause, the worker may send a transcript older than 90 days before
   cleanup catches up. A 91-day-old synthetic pending row reached the recording
   notifier and was marked `sent`. Apply the same age policy when selecting pending
   deliveries and verify the recovery path through the recording notifier.
   Resolve this before enabling hosted handoff delivery. [Worker selection](../../backend/app/handoff.py#L166) · [Retention function](../../backend/alembic/versions/0004_recruiter_retention.py#L28)
2. **P2 · An automatic quota reservation can straddle UTC midnight.** A grant
   may commit on the old date and expire before the ledger opens. The retry
   sees the old grant under the same boot ID and cannot reserve for the new
   date. The independent reviewer reproduced both denials with a fake clock
   and a store adapter. The process stays resting, and a fresh boot can
   reserve for the new date. Handle this close to the grant lifecycle and
   keep the existing one-grant rule and conservative charge. [Boot quota](../../backend/app/safety/boot_quota.py#L50) · [Grant lookup](../../backend/app/db/quota.py#L86)
3. **P2 · The GitHub backend job skips eight Postgres integration tests.** The
   local fixture requires a disposable loopback `portfolio_test` URL. The job
   supplies neither a Postgres service nor the URL. The configured local
   database let the suite exercise those checks. Add a disposable Postgres CI
   service so PRs exercise migration, retention, recovery, and row locking.
   [CI job](../../.github/workflows/ci.yml#L44) · [Fixture](../../backend/tests/test_database.py#L132)

`Handoffs.accept()` earns its depth by owning insert, equality on retry, commit,
and worker wake behind one interface. The notifier seam supports both the
Telegram adapter and the recording adapter. A bounded external send holds a
row lock and can repeat after acceptance followed by a lost commit. The
submission UUID gives Aamir a way to identify repeats. That ambiguity is part
of the current design. [DRN-074](../decisions.md#drn-074-consent-based-handoff-and-durable-delivery)

Analytics keeps its bounded queue off the chat path. The feedback row owns the
first-writer rule through its primary key. `BootQuota` owns grant lifecycle,
`PostgresQuotaStore` owns serialized daily reservations, and `InferenceLedger`
owns provider attempts. Removing any of these modules would move ordering
constraints into callers. Keep that locality. Minute limits still belong to
one process. Confirm the cutover avoids overlapping inference producers and
verify actual Render proxy peers before trusting forwarded client IP headers.
[DRN-075 and DRN-077](../decisions.md) · [Hosted proxy checks](../runbooks/production.md#proxy-and-hosted-privacy-verification)

## Closeout status

The local review and study guide are ready. The [three teach-back prompts](../study-guides/phase-09-recruiter-workflow.md#teach-back)
await the user’s answers. Supabase migration and permissions, Cron’s first
successful run, and Telegram delivery remain hosted acceptance checks. Keep
Phase 9 open until hosted verification and the follow-up decisions are recorded.

# Phase 10 — Production hardening, monitoring and launch

Step 1 proposal, 6 November 2026. Branch: `phase-10-production-hardening`, from
`main` at `de73fb511ef82fd9c5b5f3c7e864ab0fcf0c6454`. Build approval pending.

## Outcome and scope

A recruiter gets useful authored content while the API wakes or inference rests;
the owner can identify the deployed revision, understand capacity, receive actionable
alerts and recover safely. Merges deploy through the existing Render/Vercel setup
with explicit evidence of checks and runtime behavior. An optional custom domain is
an owner choice; the current public URLs remain the default proposal.

Follow P6 → P8 → remaining P7 → P10, then P9. No database, durable quota ledger,
migrations, backups/restore, handoff, company links or summary storage before P9.
No new model, orchestration framework or model-based operational classifier.
Existing safety code and CI audits are the starting point, not work to rebuild.

## Architectural pre-mortem: suppose launch failed

Start with the visitor/owner failure, then choose the smallest enforceable control.

| Failed outcome | Current evidence / cause | Deterministic prevention and acceptance evidence |
|---|---|---|
| Site looks healthy but never generates | `health.py` returns service ready while the ledger starts closed; `authorize()` has no production operator path | Keep liveness/readiness separate from capacity. Design a narrow authenticated, boot-bound operator activation interface before building it; reject reusable environment grants, stale/foreign boot grants and public activation. Exercise expiry/restart/unknown use with clocks and fakes. Resting-only operation is valid and visibly labeled until authorized activation is demonstrated. |
| Visitors disappear during wake-up | Status copy still says about 25 seconds from historical P0 measurements | Default to accepting sleep, not keep-alive pings. Offer existing authored answers/contact immediately; measure a fresh 20-minute idle cycle and record what appears, timeouts and recovery. Account for every boot losing its allowance. No promised wake-up time from an old benchmark. |
| A healthy monitor misses loss of inference, or leaks private data | Health has a typed capacity state; JSON logs exist but hosting retention/alert delivery are unverified | Use HTTP/schema/state rules for separate availability and capacity alerts, bounded deduplication and recovery. Treat expected resting as status, unexpected transitions as alerts under an explicit policy. No prompts, headers, raw IPs or secrets in alert payloads; fake notifier tests plus owner-confirmed phone delivery. |
| Green merge deploys broken assets or stays on an old revision | Workflows exist; cloud results/runtime revision not checked; Render build downloads model assets while a fingerprinted NPZ is committed | Verify build/runtime asset identity, local-only runtime loading and health/revision evidence. Document content PR → reviewed embedding/provenance update → offline gates → deploy. Check actual Render/Vercel auto-deploy settings and CI ordering; do not assume auto-deploy waits for CI. Define rollback and its closed-ledger consequence. |
| Everyone shares a proxy limit, or spoofed headers bypass it | Proxy trust defaults closed and Uvicorn rewriting is disabled; real chain remains unknown | Verify deployment-specific peer/header behavior with bounded redacted evidence, then configure only proven trust. Retain socket fallback when unverified; test forged/duplicate XFF and two independent clients. No guessed trust-all CIDR. |
| Shared link, résumé or mobile experience fails | No public PDF; OG image is SVG with relative metadata; noscript content exists but is unverified | Export only approved public résumé content, omitting private fields; verify PDF/source MIME/status, static-route precedence, no-JS content and social preview. Check real Android/iPhone plus throttled 4G; record actual devices separately from browser emulation. |
| Launch overstates safety or accuracy | Twenty real-output attack reviews pending; 76 draft facts; judge validation failed | Preserve provenance and unavailable accuracy. Offline replay/code enforcement remain separate from semantic claims. An approved bounded real attack run and human review are a launch gate; fresh independent judging/fact approval and compatible held-out evidence are required before factual-accuracy publication. |

## Deterministic rules and module placement

Code owns status classification, configuration validation, revision/asset identity,
authorization/expiry, alert transitions and redaction, URL handling and CI gates.
No LLM decides whether to wake, activate, alert, publish results or roll back.
Semantic correctness still needs real outputs and human evidence; substring/schema
checks cannot supply it. Monitoring never spends provider quota to test health.

Keep capacity ownership in `InferenceLedger`; an operator adapter crosses its existing
`authorize()` interface rather than adding a second quota ledger. Health presents a
small public status interface, never secret grants or control credentials. Keep any
notification adapter behind a narrow testable interface only when the chosen channel
requires it. Prefer an external monitor consuming existing health over a self-polling
background scheduler or a general observability framework.

## Six reviewable increments

Each approved increment ends with focused checks and a small conventional commit.
Paths below are proposed; new files are labeled new.

| Increment | Deliverable / affected files | Checks |
|---|---|---|
| 1. Reproducible release and recovery | `render.yaml`, `frontend/vercel.json`, `.github/workflows/ci.yml`, `scripts/generate_embeddings.py`, existing embedding manifest/artifacts as needed; new `docs/runbooks/production.md`. Audit current main cloud checks/settings; bind builds to source/assets and document deploy/rollback/content workflow. | Clean build with cached/provisioned assets, stale artifact refusal, revision matching, production-only CORS; confirm CI ordering before claiming gated deploys. Do not regenerate vectors or baseline identities silently. |
| 2. Production identity and capacity control | `backend/app/api/health.py`, `settings.py`, `main.py`, `safety/admission.py`, `.env.example`, corresponding backend tests and runbook. Review exact control/auth design before implementation; prove proxy chain and operator boot-bound activation while preserving closed defaults. | Fakes/clocks for invalid auth, stale/wrong-boot/reused allowance, expiry/midnight/restart and concurrent admission; existing spoofing regressions. Authorized deployment checks establish proxy and runtime behavior; no provider call needed for control tests. |
| 3. Useful cold and resting experience | Existing server-status hook in `frontend/src`, `components/StatusIndicator.tsx`, chat/fit fallback UI and styles, backend health contracts if required. Replace stale timing claims with measured copy and preserve instant authored routes/contact. | Vitest through real transport contracts: warming, timeout, resting, recovery, abort and no duplicate sends. Fake-backed browser keyboard/mobile QA, then separately recorded 20-minute real idle check with no generation. |
| 4. Actionable monitoring and privacy operations | Health/status projection and metadata logs only if gaps remain; new monitor configuration/example and production runbook for the chosen channel. Specify outage/resting/recovery policy and hosted log retention. | Mock HTTP failures, malformed status, unexpected resting, recovery, cooldown and notifier failure; sentinel redaction. Confirm actual phone delivery with explicit authorization for the selected service/destination. No monitoring credentials in git. |
| 5. Recruiter launch assets | `frontend/index.html`, `frontend/public/` résumé/social assets, existing résumé/contact links, `frontend/vercel.json` route handling and runbook checklist. Source résumé from `resume.tex` after public-field review; preserve third-person voice and factual limitations. | PDF/source links return expected content, no-JS usefulness, OG URL/image preview, CSP, keyboard/contrast, real Android/iPhone/throttled 4G. No new private disclosure or draft fact promotion. |
| 6. Acceptance, review and handoff | `docs/PROGRESS.md`, `docs/decisions.md`, new `docs/audits/` evidence ledger and `docs/study-guides/phase-10-production-hardening.md`; reconcile `docs/implementation-plan.md` acceptance wording only when approved. | Full offline suites/lint/build/eval/audits, bundle <200,000 gzip bytes; read-only architecture review, browser QA, three-question teach-back/study guide. Map every launch/Done-when item to measured evidence, pending input or explicit P9 deferral; soft-launch feedback from three people requires owner coordination. |

## Verification and launch gates

Use injected FakeLLM/MockTransport in all tests. Planned full checks: backend/tests
and evals pytest, Ruff lint/format, frontend Vitest/ESLint/TypeScript/Vite, bundle
script, full offline retrieval/replay, existing Python/npm/secret audits. Do not lower
floors or overwrite frozen validation/held-out evidence. Runtime changes may invalidate
P8 fingerprints; review compatibility and refresh artifacts explicitly where necessary.

Use React best practices for React work, frontend-design for UI/CSS, codebase-design
for operational interfaces, diagnosing-bugs for failures, agent-browser for browser
QA, architecture-review skills at Review and teach at Teach-back. No skills installed.

Original Done-when mapping: both deployments/redeploys and alert phone delivery need
actual cloud evidence; own-domain acceptance is pending the owner's optional domain
choice, not silently marked passed. Fresh cold-start timing and visitor experience
must be measured. Backup/restore acceptance belongs to P9. The original blind-suite
and twenty-attack semantic gates remain unsatisfied until separately authorized valid
evidence exists. Finishing offline P10 engineering alone does not certify wide launch.

## Inputs, risks and approval

- Approve this six-increment brief to begin Build. Under AGENTS.md Phase Loop step 1,
  "Present a short phase brief ... Wait for approval." This kickoff ends at that gate.
- Before activation: current Groq account limits, remaining budget/other users and a
  reviewed secure operator mechanism. No prior allowance survives a restart. No
  reusable dashboard environment value silently enables spending.
- Before external monitoring: choose the provider, destination and sleep-aware alert
  policy. Prefer the existing hosting URLs and accepting sleep; a domain, paid tier
  or keep-alive policy needs a separate owner choice. No service signup or message sent.
- Before live semantic checks: exact reviewed scope/token budget and human review;
  failed P8 validation cannot certify these outputs. Fact/accuracy publication gates
  remain independent of engineering closure.
- Need approved public résumé fields, real device access/results and hosting settings
  evidence. Hosted log retention is a platform setting, not P9 transcript storage.
- Moderate npm development advisories remain tracked. Propose exact compatible pins
  for approval before further dependency changes; no automatic audit fixes.
- Push/deploy, DNS changes, new dependencies/services and notifications retain explicit
  authorization gates. No Postgres/paid service/new dependency is proposed by default.

## Kickoff evidence and sources

Read AGENTS.md, progress, decisions and roadmap; inspected deployment/CI config,
lifespan, health, settings, ledger activation references, logs and static assets.
Starting tree clean; local main/tracking ref/tag all resolve to `de73fb5`. Remote
`git ls-remote` failed with a network resolver error; GitHub push/CI trigger is Aamir's
confirmation, not a fresh independent remote/runtime observation.

Official docs checked 6 November 2026:
[Render free services](https://render.com/docs/free) describe 15-minute idle spin-down,
roughly one-minute wake-up and ephemeral disk;
[Render health checks](https://render.com/docs/health-checks) describe HTTP status-based
readiness, which cannot establish inference capacity by itself;
[Vercel Git deployment](https://vercel.com/docs/git) documents Git-triggered deployments.
These describe provider behavior, not verified account settings or measured app timings.

No application tests, provider calls, installs, remote writes, deploys, alert messages
or production probes in this Step 1 kickoff. Historical P7 checks remain historical.

## Approved implementation — 10 November 2026

Aamir approved all six increments and autonomous continuation through final review.
Follow-up scope: existing default domains, normal Render sleep without internal pings,
optional ALERT_WEBHOOK_URL notifier through existing dependencies, four emulated
viewports and a manual physical-device postdeploy checklist. Temporary
agent-browser@0.42.0 explicitly approved; no global/project dependency added.

All six local increments, the production runbook and P10 study guide are implemented.
Read-only architecture review findings were reproduced/fixed and independently rechecked.
Exact verification, compatibility review and remaining release/semantic gates are in
the [P10 evidence ledger](../audits/2026-11-10-phase-10-production.md). Final local
verification and review do not imply push, deployment, actual phone delivery, fact
approval or a completion tag. P9 remains deferred.

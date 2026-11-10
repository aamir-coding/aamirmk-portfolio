# Phase 10 production hardening — evidence and release acceptance

10 November 2026. All six increments are authorized. Scope follows the
[approved brief](../briefs/phase-10-production-hardening.md), with the user's explicit
follow-up choosing existing default domains, normal Render sleep, optional
`ALERT_WEBHOOK_URL`, four emulated viewports and a physical-device postdeploy checklist.
The user approved temporary `agent-browser@0.42.0`; no global tool/project dependency
was added. Existing authoring runtime supplied ReportLab/Pillow; no runtime dependency
changed. No real Groq call, fact approval, cloud configuration write or notification.

## Local implementation

| Commit | Outcome |
|---|---|
| `e3435b4` | Verify committed release assets and record deployment identity |
| `d001bc2` | Opt-in boot-bound operator controls, off-thread retrieval warmup, honest readiness |
| `289a198` | Bounded health lifecycle, manual recovery and useful cold/resting alternatives |
| `e1cb1db` | Provider-free external monitor with incident/delivery state |
| `e81d783` | Reviewed privacy/auth/recovery fixes and user-requested optional webhook settings |
| `7007ff3` | Draft résumé/social assets, source-backed cover, accessibility/source-link presentation |
| `3c2b61a` | Binary asset protection and no-store on preparse control rejection |

Code source is committed before final result generation. Final result/artifact and
full-suite evidence will be added below after the reviewed identity refresh.

## Actual verification before final artifact refresh

- Release verifier: **4 tests passed**; actual `python -m app.release` against clean
  `3c2b61a` returns revision plus committed index SHA
  `809e94d35f5df5633d74b7efb444594b747bd06d0703b58cb6e2020e9b7ec91e`.
  Restored the existing pinned local ONNX cache; did not regenerate corpus/vector data.
- Operator/health/ledger/proxy focused run: **56 passed**. Operations/monitoring after
  review: **25 passed**. Raw-bound/operator subset after no-store fix: **22 passed**.
- Initial full Python/eval run: **636 passed, 1 failed**, 2 existing warnings, 115.43s.
  The failure is expected stale public projection after source identity changes, not
  a tolerated final failure. Final compatible full run is required below.
- Full frontend after code fixes: **181 passed / 24 files**, 16.05s. ESLint and
  TypeScript/Vite production build pass. Exact bundle script reports
  **167,339 gzip bytes < 200,000**. Existing Rollup annotation/chunk warnings remain.
- Python dependency audit: **No known vulnerabilities found**, exit 0, using the
  existing isolated approved pip-audit tool against the installed graph.
- npm audit: **9 moderate, 0 high, 0 critical**. No automatic fix, ignore or unapproved
  dependency change. High-severity policy passes; zero findings is not claimed.
- Gitleaks 8.30.1: **165 commits**, 3.62MB, **no leaks found**, exit 0 before final
  documentation/artifact commits. Final staged scan will cover remaining text.

Windows sandbox first runs exposed missing local model assets and Vitest temp-rename
restrictions. Existing model assets were provisioned into ignored build/; successful
Python/Node socket/async/browser checks ran outside the Windows sandbox. These setup
failures were not reported as application passes. All automated inference is fake.

## Review, browser and assets

Applied codebase-design and improve-codebase-architecture for required read-only
subagent review. Four concrete findings were reproduced/fixed: invalid-secret error
strings, anonymous starvation of valid operator controls, chat-resting state masking
successful recovery and naive persisted monitor timestamps. Independent recheck:
**25 operations/monitoring tests, 23 frontend lifecycle tests passed**, no remaining
concrete blocker. Final no-store rejection regression independently passes.
The architecture report is a temporary HTML artifact; P9 shared durable capacity is
the only deferred deepening opportunity, not a new implementation in this phase.

Used isolated agent-browser session `phase10-576bd702418b` against a fake-retrieval,
empty-key local API. Asserted no horizontal page overflow and 44px controls at
**375×667, 390×844, 768×1024, 1440×900**; also checked curated role modal and transcript.
Measured small controls were corrected, including copy/status/repository buttons.
Used actual light/dark theme transitions with OS dark preference; fixed warning-banner,
badge and action-button contrast and unsupported generic ARIA labels. Final recorded
cover light/dark and transcript light audits: **0 axe violations, 1 incomplete item**
for the decorative theme glyph. This is scoped QA, not full accessibility certification.
Inspected the mobile screenshot; authored starter, curated report, Escape dismissal,
Ctrl+K focus and inaccessible-source rendering checked. No live generation performed.

CLI lacks a genuine JavaScript-disable control; a Chrome launch flag did not disable it.
Used CDP `Emulation.setScriptExecutionDisabled` on a second owned QA browser, reloaded
and asserted **empty React root, visible noscript contact and résumé links**. This is
an actual no-JS browser check, not merely blocked bundle loading.

Local HTTP checks: résumé PDF **200/application-pdf** (actual MIME `application/pdf`),
source Markdown **200/text-markdown** (`text/markdown`), image **200/image-png**
(`image/png`). PDF extraction confirms **one page, DRAFT label, no phone**; rendered
PNG inspected for layout. Social image is **1200×630**, uses absolute default-domain
metadata and was visually inspected. PDF source stays DRAFT; it is not final factual
approval. Existing corpus, prompts and captures are unchanged.

Source inventory: nine unique fact URLs plus eleven project/authored-answer URLs were
checked (overlap exists). Anonymous 404s: portfolio repo, obsolete `github.com/aamirmkh`,
and old `portfolio-assistant` repo. Suppress those exact destinations in receipt/project
links while preserving evidence IDs/text. LinkedIn returned automated-access status 999;
profile remains a manual verification item. No repository was made public or source
URL invented. Recheck suppressed URLs before restoring them.

## Production read-only evidence

- Fresh `git ls-remote` confirms `origin/main` and `phase-7-hardening-done` both target
  `de73fb511ef82fd9c5b5f3c7e864ab0fcf0c6454`.
- Phase 7 cloud [CI succeeded](https://github.com/aamir-coding/aamirmk-portfolio/actions/runs/42246728431)
  and [security audits succeeded](https://github.com/aamir-coding/aamirmk-portfolio/actions/runs/42246728426).
  Newer failed runs inspected belong to Dependabot PRs, not current main.
- At 18:20:14 IST, production health returned **200/ready/resting** in **42.391s**.
  Vercel frontend returned **200** in **0.697s**, serving the P7 tightened CSP.
- At 18:40:33 IST, after **1,219 seconds without probes from this task**, production
  health returned **200/ready/resting** in **32.673s**. Other external traffic cannot be
  excluded, so this is a measured wake-up observation, not a guaranteed isolated cold boot.
  Both probes spend **zero inference calls**. Current production is P7 behavior and
  lacks P10 revision fields; these checks do not claim P10 was deployed.

## Evaluation compatibility

Root and independent reviewer compared candidate from **clean `3c2b61a`** with baseline:
all **seven scores exactly equal**, all **8/8** replay records pass, **only application
fingerprint changed**. Gate reports only incompatible_baseline; reviewed candidate
identity in memory removes it. DRN-066 authorizes fingerprints/reference-only refresh.
No floor, metric set, tolerance or critical check is lowered. Facts/prompts/index,
recordings, cases, rubric, human/judge archives and evaluator have no diff from main.
Failed judge validation, five disagreements, 76 draft facts, unavailable model accuracy
and reserved/unexecuted held-out cases must remain visible in the final projection.

## Release acceptance and ownership

| Item | Status |
|---|---|
| Six increments, tests, runbook, reviewed source and study guide | Implemented locally; final compatible verification recorded below |
| Existing default HTTPS domains / normal Render sleep | Explicit owner choice; no DNS purchase/pinger |
| Emulated mobile/tablet/desktop + no-JS + PDF/social assets | Verified within stated local scope |
| P7 remote identity/cloud jobs | Independently verified |
| Fresh production idle observation | Measured above; not P10 deploy proof |
| Optional privacy-safe webhook / failure/recovery | Implemented and fake-verified; no channel credentials supplied or external message sent |
| Actual phone delivery, hosted retention and deploy/CI settings | Owner setup/postdeploy verification; runbook includes free Discord/HTTP monitor steps |
| P10 deployed revision/CSP/routes/proxy chain | Pending release authorization and hosting evidence; default proxy trust stays closed |
| Current account limits and live boot allowance | Pending operator evidence/authorization; defaults remain closed |
| Physical iOS/Android/4G and WhatsApp/LinkedIn previews | Postdeploy owner checklist, per explicit scope choice |
| Final résumé content and private-source accessibility | Draft/review and documented source availability limitations preserved |
| Twenty real-output attack reviews / independent validation / accuracy publication | Separate semantic/spend gates; no success inferred from engineering tests |
| P9 durable storage/quota, handoff, company pages, backups/restore | Deferred; not started |
| Soft launch to three people, teach-back answers | Owner follow-up; no unsolicited messages or assessed answers |
| Push/merge/deploy and `phase-10-done` tag | Not performed; final review/release acceptance precedes completion tag |

This ledger distinguishes completed implementation from external release/semantic
acceptance. It does not reopen the user's closed P7 or accepted P8 offline milestones.

# Remaining Phase 7: local verification and acceptance ledger

6 November 2026. Branch `phase-7-safety-hardening`, based on deployed/user-confirmed
P8 main `440e81d`. Six increments are implemented. This is local engineering evidence,
not production activation or semantic safety certification.

## Reviewed revisions

| Revision | Increment |
|---|---|
| `c5cc4cb` | Atomic boot-bound inference admission |
| `e9eec9b` | Metered provider attempts and app-owned lifecycle |
| `d7b5819` | Trusted identity and bounded abuse admission |
| `0d043f2` | Useful resting mode and provenance-aware bounded fit cache |
| `df24c61` | Data framing, strict tools and deterministic grounding constraints |
| `ddae674` | Privacy, CSP, approved compatibility updates and security audits |
| `fd323d9` | Final v3 contracts captured from clean reviewed source |

Final `evals/results.json` was generated with clean source at `fd323d9`. It records
zero provider calls/tokens and no held-out execution. Current v3 capture records clean
source at `ddae674`. Artifact/docs commits follow; production source fingerprints do
not include generated reports. Historic artifacts remain recoverable in Git history.

## Actual commands and output

| Check | Actual result |
|---|---|
| `.venv\Scripts\python.exe -m pytest -c backend/pyproject.toml backend/tests evals -q --tb=short` | **610 passed, 2 warnings in 88.90s** |
| `ruff check --config backend/pyproject.toml backend evals` | **All checks passed!** |
| `ruff format --check --config backend/pyproject.toml backend evals` | **102 files already formatted** |
| Frontend `npm test` | **176 passed, 23 files**, Vitest 4.1.11 |
| Frontend `npm run lint` | Exit 0 |
| Frontend `npm run build` | TypeScript/Vite exit 0 |
| Frontend `node scripts/check-bundle.mjs` | **166,994 gzip bytes / 200,000** |
| `python -m evals.run --full --output build/phase7-final-gate.json` | Exit 0, **gate_failures: []**, held-out reserved/not executed |
| Production CSP/bootstrap structural assertions | Passed: script self, exact connect origins, object none, external theme file, no inline bootstrap |
| `git diff --check` | Exit 0 |

Python checks ran outside the Windows sandbox because sandboxed asyncio socketpair
stalled. Provider interactions use injected fakes/MockTransport. No real Groq calls.
Two installed Starlette TestClient deprecations remain (HTTPX adapter and AnyIO alias);
no unapproved replacement HTTP stack was installed. Vite's existing Zod annotation and
raw chunk-size warnings remain; the required initial gzip budget passes.

Earlier broad runs found stale request-ID/model-routing/summary expectations, telemetry
replay schema drift and stale result identity. Regressions were corrected against the
intended contracts; the final complete suite above passed. No failure was waived.

## Audits

- Approved exact Python upgrades and isolated pip-audit 2.10.1: **No known
  vulnerabilities found**, exit 0, complete frozen installed graph. Local ignored
  reports: `build/phase7-pip-audit-after.json`, `phase7-python-environment-after.txt`.
- Approved Vitest 4.1.11 removed critical npm findings. Repeat npm audit: **9 moderate,
  0 high, 0 critical**. The exact CI command `npm audit --audit-level=high` returned
  **exit 0** against the public registry. This threshold does not mean zero advisories.
  Remaining development-tool chains: TypeScript ESLint/minimatch and Vitest mocker;
  audit recommends Vitest 4.1.12. Further pin changes are tracked, not silently applied.
- Gitleaks 8.30.1: **155 commits**, approximately 3.48MB, **no leaks found** in the
  pre-Increment-6 history. A separate staged Increment-6 scan examined 47.17KB,
  **no leaks found**. Local scans use `--redact=100`; reports are ignored. No advisory
  ignores, secret allowlists or automatic fixes were introduced.
  Final history recheck after source/v3 commits: **157 commits**, approximately
  **3.53MB**, **no leaks found**. The subsequent staged evidence/docs scan also found
  no leaks.
- CI uses approved isolated pip-audit, pinned Gitleaks action/scanner, npm audit and
  weekly Dependabot proposals. Cloud workflow execution has not been verified on this
  branch, because it has not been pushed.

## Deterministic and browser evidence

The suite covers atomic reservation/window boundaries, startup uncertainty, cancelled
versus dispatched attempts, all inference stages, explicit retries and SDK closure;
trusted-chain parsing, malformed/duplicate headers, IPv6 normalization, key floods and
actual-byte body bounds; resting/cached/refusal paths; cache identity/TTL/live bypass;
strict tools, known-negative grounding and Unicode input handling.

The loopback load regression issues twelve parallel requests with rotating sessions and
forged forwarded IPs: **2 HTTP 200, 10 HTTP 429, zero provider attempts**. Resting tests
exercise exhausted daily allowance and useful zero-call paths. These are deterministic
gates; no test claims live model resistance from injected fake replies.

Sentinel privacy tests initially exposed independent Uvicorn/HTTP client logging. The
final regression exercises a real loopback server with production logging config and a
sentinel query/RuntimeError. It passes without raw IP/query/exception payload in logs.
Render disables proxy rewriting, HTTP access logs and WebSockets; hosted logs remain
an operational review item.

Used agent-browser through its installed core workflow, named session
`phase7-hardening-20261106`, against a local fake-retrieval API with empty Groq key and
closed inference. Verified authored starter response, custom-question resting terminal
state, curated fit report, forced live bypass yielding resting fallback, Escape dialog
dismissal, Ctrl+K focus (`TEXTAREA`) and inspected a 390×844 screenshot. Corrected
observed fallback contrast, duplicate landmarks and unsupported labeled generic roles.
Final mobile axe: **0 violations, 1 incomplete color-contrast item** (manual review,
not an automated accessibility certification). Dev-server QA does not apply Vercel CSP
or verify deployed proxy topology. Real Android/iPhone/4G/cold-start testing remains P10.

## Architecture and evaluation compatibility review

Applied codebase-design and improve-codebase-architecture skills. The latter explicitly
required a read-only subagent review. Initial concrete findings were reproduced/fixed;
the reviewer reported no remaining blocker in the six-increment scope. Final privacy
fixes cover server access/error/WebSocket handlers and honest retention wording.
The deferred deeper module opportunity is P9 durable account-capacity ownership;
no new storage/framework or speculative refactor was introduced.

DRN-061 records an explicit baseline identity review. Independent reviewer and root
both confirmed all seven current scores exactly equal the original baseline. Only
fingerprints/review reference changed; floors, tolerance and critical checks did not.
Current replay is **8/8** with all case bindings/expectations preserved and strict typed
telemetry. Frozen v1/v2 captures, facts, cases, rubric, human labels and judge archives
have no diff from `440e81d`. Public projection preserves **failed** judge validation,
all **five disagreements**, **76 draft facts** and unavailable generation accuracy.

## Acceptance ledger

| Item | Status and limit |
|---|---|
| Six approved implementation increments | Implemented and locally committed |
| Load limit and forced resting gates | Passed offline with injected providers |
| Full tests/lint/build/bundle/strict replay | Passed, evidence above |
| Privacy sentinel and local browser QA | Passed within stated scope; one axe manual item |
| Dependency and secret scans | Python/history scans clean; nine moderate npm development findings tracked |
| At least 20 real-output semantic attacks | **Pending** separately authorized budget/run and human review |
| Provider remaining capacity and production activation | **Pending** current account evidence and fresh one-shot allowance; default closed |
| Trusted Render proxy chain and deployed CSP/runtime | **Pending** separately authorized production verification |
| Three-question interactive teach-back | Sent; answers **not yet assessed** |
| Public résumé PDF/source link | **Pending P10**; old source returned unauthenticated 404, fallback uses existing professional profile |
| Durable quota/message retention/handoff/backups | **Deferred P9** per approved execution bands |
| Push/deploy/completion tag/next phase | **Not performed**; existing first-share tag preserved |

The [updated study guide](../study-guides/phase-07-safety-rate-limiting.md) explains the
current implementation and interview trade-offs. The phase has not been marked complete
or tagged while required semantic/operational acceptance remains outstanding.

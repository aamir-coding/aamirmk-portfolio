# Remaining Phase 7: safety hardening brief

Prepared 6 November 2026 on `phase-7-safety-hardening`, from `main` at `440e81d`.
Status: approved by Aamir on 6 November 2026; Increment 1 implemented, provider
integration next. Verification and open gates are tracked in `../PROGRESS.md`.

## Outcome and scope

A recruiter can keep using curated answers and contact links during quota exhaustion
or provider failure. Every outbound model attempt is admitted against bounded capacity;
untrusted inputs cannot bypass deterministic limits, tool permissions or explicit
factual constraints. Semantic interpretation remains a model task with qualified evidence.

This is the remainder of P7 under AGENTS.md's Band 3 order, not P9 despite its numeric
position after P8. Preserve completed first-share work and the fixed stack. P10 follows;
Supabase, SQLAlchemy, Alembic, durable analytics and handoff stay in P9. The original
P7 DB-persistence and handoff requirements cannot be accepted before P9; P10's backup,
handoff and company-link requirements also remain pending P9.

## Architectural pre-mortem: assume the outcome failed

| Failed outcome | Evidence in the current implementation | Proposed prevention and falsifiable check |
|---|---|---|
| Concurrent requests spend capacity already promised elsewhere | `quota.py` separates `check()` from post-response `record_usage()`; chat records one aggregate per HTTP request; fit checks admission without recording provider usage | One shared, app-owned inference module reserves capacity atomically before each physical attempt. Include rewrite, tool turns, extraction retry, judge batches and summary. A barrier-controlled concurrent test proves no oversubscription. |
| Hidden retries or disconnects spend unrecorded tokens | `GroqLLM` creates `AsyncGroq` without explicit retry/timeout controls; installed Groq 1.7.0 defaults to two retries. Chat stream accounting estimates tokens after completion | Disable SDK retries; implement bounded explicit attempts with a fresh reservation each time, capped Retry-After and an overall deadline. Unknown/error/cancelled usage retains its hold; reported usage reconciles once. MockTransport verifies exact HTTP attempts, stream closure and no double refund. |
| A restart, eval process or second model bypasses the daily ceiling | Quota lives in module-level memory; standalone eval accounting is separate; plan assumes spare capacity on the other model | Conservative shared application ceiling plus model-specific limits. No automatic second pool inferred from identical advertised numbers. Start in resting mode when current-day remaining allowance is unknown; reopening needs an explicit operator allowance and expiry, with other account usage deducted. Restart/UTC-boundary tests never mint a new daily allowance. Durable automatic recovery remains P9; simultaneous independently spending processes remain outside this ledger. |
| Forged headers/session IDs or large bodies evade abuse controls | `ip.py` accepts CF/True-Client-IP and leftmost valid XFF without a verified proxy chain; Render starts with `--forwarded-allow-ips='*'`. Limits are IP-only; Pydantic field limits follow body parsing | Verify the real proxy topology, then canonicalize a trusted chain once. Add bounded IP/session limit state and an ASGI byte cap, including absent/false Content-Length. Session rotation cannot bypass the IP/global caps. Test forged chains, IPv6 equivalence, rotating IDs, key floods and chunked bodies. |
| A JD, history entry or retrieved passage changes instructions or invents evidence | Chat has regex screening; fit has partial delimiter instructions. Existing citation membership checks establish lineage, not entailment; generated explanations/summary can still overclaim | Escape structural delimiters in every data channel, enforce typed tool allowlists and arguments, and validate local citation IDs, verdict enums, numeric scores, length and explicitly authored negative constraints in code. Abstain on invalid evidence. Semantic support remains qualified; regex is not a general prompt-injection proof. |
| Resting mode blocks the zero-cost paths or hangs the UI | Chat/fit route quota dependencies run before their inner refusal/cache logic; clients have error handling but no unified capacity contract | Keep abuse controls for all requests; put provider admission after valid refusal/cache/curated resolution. Use typed capacity/unavailable outcomes before and during SSE, bounded waits and contact/resume fallbacks. Exhausted-budget integration tests assert zero SDK calls and terminal UI state. |
| Logs leak recruiter content or CI misses new exposure | Access/rate-limit logs contain raw IPs; guardrails log raw rejected text; rewriting logs queries/history-derived text; CSP allows inline scripts and localhost connections in production; no dependency/secret audit jobs | Redact sensitive payloads, use a configured salted IP hash, sanitize request IDs/errors and disclose actual processing. Test logs using sentinel secrets. Tighten CSP with the current theme bootstrap accounted for; scan dependencies/secrets in CI with explicit reviewed tooling. Retained recruiter-message storage/90-day cleanup stays P9. |

## Deterministic rules and semantic tasks

Code owns byte/field/history limits, timeouts, admission and reservations, window rollover,
retry counts, model routing, tool permissions/argument schemas, source membership,
configured known negatives, report score arithmetic, cache identity and delivery state,
safe URLs, fallback routing and privacy redaction. Models do not decide any of these.

Models handle coreference rewriting, extracting JD requirements, interpreting evidence
and phrasing a grounded answer. A model judgment cannot override a failed code check.
Known-negative mappings must come from explicit reviewed facts, not guessed keyword
rules. Novel factual entailment and arbitrary prompt-injection resistance cannot be
certified by schema validation, substrings or the failed P8 judge. No classifier LLM
or new live judge is proposed. Twenty attack cases need separate code-level expectations
and human-reviewed semantic expectations; offline fakes prove enforcement, not live safety.

## Six reviewable increments

Each increment ends with focused checks and a small conventional commit. Consult
codebase-design for the inference seam, React best practices for frontend changes,
frontend-design for UI/CSS, and diagnosing-bugs for unexpected failures.

| Increment | Deliverable and affected files | Checks |
|---|---|---|
| 1. Atomic inference admission | Extend `backend/app/safety/quota.py`, settings and tests; add a small internal admission module if needed. Define conservative input/output reservations, global/model RPM/TPM/RPD/TPD budgets, startup uncertainty, operator allowance expiry and bounded queues using injected clocks. Record proposed supersession of DRN-017 only after implementation. | Atomic competing reservations; impossible-sized prompt rejected; minute/day boundaries, unknown prior use, startup/restart, cancellation before dispatch and idempotent reconciliation. Arithmetic uses actual serialized prompts plus a documented conservative bound, not `chars/4` as a guarantee. |
| 2. Meter every provider attempt | `backend/app/llm.py`, `main.py`, chat/fit dependency providers, `retrieval/rewriter.py`, fit pipeline and `telemetry.py`. Bind one inference module/client to app lifespan through Depends; remove request-path mutable singleton ownership in touched paths. Explicit SDK retry/timeout settings, per-attempt reservation, utility routing, cancellation and stream/client closure. | Fake/MockTransport full call graph covers rewrite, chat tool turns, both extraction attempts, all judge batches and summary; attempts equal reservations; timeout/429/unknown usage hold capacity; two apps remain isolated. Browser receipt timing/usage remains truthful. |
| 3. Abuse admission and trusted identity | `safety/ip.py`, `rate_limiter.py`, `main.py`, `models.py`, fit models, `settings.py`, `render.yaml`, `.env.example`, frontend session transport and API contracts. Verify proxy assumptions before choosing trusted addresses/hops; cap bodies, session IDs/history and limiter state. | Spoofed headers/direct peers, canonical IPv4/IPv6, session rotation, two clients, bounded state eviction, no Content-Length, oversized streamed input, rate thresholds and consistent 413/422/429 errors. A small loopback fake-backed load check exercises actual endpoints. |
| 4. Useful resting mode and bounded cache | `api/chat.py`, `api/fit.py`, fit pipeline/cache, frontend `contracts.ts`, `sse.ts`, `useChat.ts`, `useFitReport.ts`, `StatusIndicator.tsx`, existing chat/fit UI and styles. Typed resting/unavailable responses; curated/refusal/cache paths remain zero-call; cache size/TTL/provenance identity and explicit live bypass cannot evade admission. | Exhaustion before first call and midway through fit; cached/curated success under exhaustion, stale cache miss, explicit bypass, bounded cache, upstream outage, cancellation and terminal SSE state through real Zod clients. Accessible fallback offers authored answers, resume and contact links. |
| 5. Grounding and attack enforcement | `safety/guardrails.py`, prompt builders, `fit/scorer.py`, `tools/registry.py`, chat output handling and a separately versioned development attack fixture. Cover at least 20 attacks across chat, JD, history and retrieved data; preserve P8 frozen inputs/grades. Prefer deterministic narratives for configured known gaps. | Code tests for delimiter breakout, tool/argument spoofing, unknown/local-mismatched citation IDs, explicit known negatives, length/scores and refusal routing; legitimate recruiter controls expose false positives. Recorded replay and human semantic review remain separately labeled. No new live calls implied. |
| 6. Privacy, browser/CI defenses and close-out | Redact logs across touched backend paths, frontend footer, `frontend/vercel.json`, `.github/workflows/ci.yml`, proposed `.github/dependabot.yml`; update `docs/decisions.md`, this brief's acceptance ledger, `PROGRESS.md` and existing P7 study guide. Reconcile P7/P10/P9 deferrals in the implementation plan without changing the stack/order. | Sentinel log/exception redaction, exact-origin CORS, production CSP and external-link protocol checks, secret/dependency audits once tooling is approved; full offline suites/lint/typecheck/build/gzip gate, fake-backed browser keyboard/mobile QA, read-only architecture review and three-question teach-back. |

## Verification and acceptance

Build checks will use injected FakeLLM/MockTransport only. Run focused tests per increment,
then full `backend/tests` and `evals`, Ruff, frontend Vitest/ESLint/TypeScript/Vite build,
and `node frontend/scripts/check-bundle.mjs` (<200,000 gzip bytes). Preserve P8 frozen
human packets, failed judge validation and historical result artifacts. P7 source/prompt
changes can intentionally invalidate their runtime fingerprints: generate new compatible
offline evidence and review baseline identity explicitly; never lower floors or silently
approve baseline changes to obtain green CI. Stale public summaries must show unavailable
rather than recycling old numbers against changed source.

The original P7 Done-when load test and forced resting test are required offline gates.
The 20-attack semantic Done-when requires human-reviewed real outputs under separately
authorized budget/scope; fake responses cannot meet it. If not authorized, report that
acceptance item pending. No claim of perfect injection prevention or semantic accuracy.

Current-day provider limits and real proxy behavior are production acceptance inputs,
not reasons to delay offline implementation. No wide-launch safety certification while
restart/account-wide capacity remains unverified. No database, background message store,
Turnstile, external alert service or scheduled live workflow in this phase proposal.

## Risks, user inputs and approval

- **Capacity vs availability:** without durable P9 state, conservative startup uncertainty
  can leave the assistant resting after a redeploy. Operator-provided current-day limits
  are an interim operational control, not durable organization-wide accounting. Independent
  eval traffic must be deducted/coordinated; the app cannot observe arbitrary other clients.
- **Bounds vs usability:** reserve the full effective prompt/tools/history plus output;
  excessive prompts may need rejection/shorter history. Avoid inventing token precision.
- **Semantic evidence:** all 76 public facts remain draft and P8 judge validation failed.
  No fact promotion, fresh validation or factual-accuracy badge follows from this phase.
- **Proxy acceptance:** current Render/Uvicorn header rewriting needs direct evidence;
  documentation alone cannot establish a safe deployment-specific trust chain.
- **Tooling:** no dependencies installed during kickoff. `pip-audit` and a secret scanner
  are unlisted tools: propose exact pins/CI actions and request explicit approval before
  adding them under AGENTS.md rule 8. Prefer existing npm audit and standard-library checks
  where sufficient. No global tools or skills needed.
- **Review gate:** approve this brief to begin Increment 1. Before production enablement,
  supply current account Limits-page figures/remaining capacity and confirm which other
  processes spend the key; verify proxy behavior with an authorized deployment check.
  Push/deploy and any live semantic run each retain their existing explicit approval gates.

Step 1 ends here per [AGENTS.md](../../AGENTS.md), Phase Loop step 1:
"Present a short phase brief ... Wait for approval."

## Kickoff evidence and references

- Clean starting `git status --short --branch`: `## main...origin/main`.
- Remote `git ls-remote origin refs/heads/main refs/tags/phase-8-done` returned the same
  full `440e81d6057a493c32f851f962e6cbda9fc19e9f` for both refs. Deployment completion
  is Aamir's confirmation; cloud CI result/runtime revision were not inspected.
- Read code at the paths named above and the 3 November handoff retrospective.
  Installed metadata: FastAPI 0.115.11, Starlette 0.46.2, Groq 1.7.0, HTTPX 0.28.1,
  Pydantic 2.10.6, pydantic-settings 2.8.1, pytest 8.3.5. Installed Groq constants:
  `DEFAULT_MAX_RETRIES = 2`; `DEFAULT_TIMEOUT = httpx.Timeout(timeout=60, connect=5.0)`.
- [Official Groq rate limits](https://console.groq.com/docs/rate-limits), checked
  6 November: organization-level limits; exact account limits belong to its Limits page.
  Listed free-tier rows currently show 30 RPM / 1,000 RPD / 8,000 TPM / 200,000 TPD
  for each chosen model. This does not establish independently spendable shared capacity.
- [Pinned Groq SDK source](https://github.com/groq/groq-python/tree/v1.7.0): web fetch
  unavailable in kickoff; installed 1.7.0 constants were inspected directly instead.
- No application tests, live Groq calls, installs, remote writes or deployment performed
  in this documentation-only kickoff. Historical P8 test counts are not fresh evidence.
- `git diff --check` passed with no output. A standard-library structural check reported
  `Brief checks: 6 increments; 2 new local document links resolve.`

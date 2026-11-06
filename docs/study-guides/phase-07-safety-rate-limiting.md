# Phase 7 study guide: bounded inference and layered safety

Updated 6 November 2026 for `phase-7-safety-hardening`. This replaces the first-share
guide's obsolete global quota singleton and unconditional forwarded-header advice.
The phase is implemented locally; production activation and real-output semantic
acceptance remain pending. All facts remain draft and the P8 judge validation failed.

## 1. Start with outcomes

A recruiter must get a useful page even when inference cannot run. An attacker must
not turn retries, tools, sessions or restarts into extra unaccounted provider spending.
The assistant must not turn an absence of evidence into a positive experience claim.
These are different problems and need different checks.

| Rule | Owner | What the check cannot establish |
|---|---|---|
| Body size, retry count, tools, output size | Deterministic code | Whether a fluent statement is factually entailed |
| Source IDs, known negatives, scores | Deterministic code | Whether an allowed source supports an arbitrary claim |
| JD interpretation, coreference, evidence alignment | Semantic model work | Permission to bypass a failed code check |
| Novel false premises and instruction attacks | Human review of real outputs | General safety from a small passing sample |

The old guide's blanket claims of zero false positives or guaranteed upstream quota
protection were too strong. Tests establish the cases and assumptions they exercise.

## 2. Atomic admission is a small transaction

In `backend/app/safety/admission.py`, read `CapacityLimits` at line 28, `Allowance`
at 35, `AttemptCost` at 57, `reserve_input_tokens` at 96, `AttemptPermit` at 129,
and `InferenceLedger` at 161. Follow `authorize`, `_reserve`, `attempt`, then `snapshot`.

The ledger checks shared and selected-model request/token ceilings together, then
records one reservation. Its synchronous mutation has no `await` between checking
and reserving, so two tasks on the same event loop cannot both spend the same room.
This assumption requires one worker and one owned ledger; it does not coordinate
other processes or other applications using the same Groq account.

Input reservations use serialized UTF-8 payload bytes plus framing allowance, rather
than claiming `characters / 4` is an upper bound. Output reservation includes the
configured maximum completion. This is deliberately conservative, not a certified
provider tokenizer. Usage above reservation stops further inference as a contract fault.

Think of the attempt states as a transaction with an irreversible dispatch point:

```text
queue -> reserve -> dispatch -> validated complete usage -> settle
          |             |
     cancel/release     timeout, cancellation, missing usage -> keep charge
```

Before dispatch, cancellation proves no request left this adapter. Afterwards, a local
timeout cannot prove the provider stopped processing. Retaining the reservation is
safer than treating missing information as zero tokens. Settlement must be idempotent;
reported model/usage contradictions close the ledger rather than granting capacity.

The allowance is bound to a random boot ID, expires by UTC midnight, and cannot silently
renew. The initial cooldown avoids optimistic rolling-minute assumptions. A restart
does not create a new grant. Production stays closed until an operator supplies a fresh
reviewed allowance through a future operational activation path; no activation endpoint
or reusable environment allowance is introduced here. Durable accounting remains P9.

## 3. One adapter owns all request-path inference

In `backend/app/llm.py`, follow `GroqLLM` at line 152, `_sdk` at 179, `complete` at
244 and `stream` at 333. `main.py:create_app` owns that adapter; Depends retrieves it.
The lifespan closes the SDK. Separate app instances have separate state.

SDK retries are disabled. Nonstream 429 handling may explicitly retry once with a
bounded retry hint, and each attempt reserves again. Streaming does not silently retry.
Deadlines apply to provider calls; rewrite has a shorter utility deadline; fit has a
90-second total orchestration deadline. Closing parent streams explicitly closes child
iterators. Cancellation is part of resource ownership, not just a UI state update.

The utility model rewrites follow-ups and extracts requirements. Main-model chat/tool
turns and fit alignment still cross admission individually. A tool turn is another
provider attempt, even though the recruiter sees one answer. Telemetry distinguishes
reported/fake/unknown usage and does not invent failed-attempt totals.

## 4. Abuse identity is not authentication

Read `backend/app/safety/ip.py:extract_client_ip` at line 30, then `get_client_ip` at
73. Parse and canonicalize addresses, including IPv4-mapped IPv6. Only a trusted socket
peer plus explicitly configured CIDRs permits a right-to-left XFF walk. Duplicated,
malformed or untrusted headers fall back to the socket. Vendor headers have no separate
authority. `render.yaml` disables Uvicorn's competing proxy rewrite.

An opaque tab ID is a useful abuse hint, not a logged-in user. The session cap sits
alongside the IP cap, and both sit below global inference admission. Rotating sessions
cannot evade the IP/global caps. Limiter key cardinality is bounded; a new key is denied
when full instead of evicting a still-active limit.

`safety/middleware.py` caps actual bytes before JSON parsing, validates Content-Length
and session headers, and bounds total body-read time. Pydantic field lengths alone
cannot prevent parsing a huge body. The raw ASGI middleware sits outside
BaseHTTPMiddleware so body disconnects do not become `No response returned` errors.

## 5. Resting mode and cache provenance

Read `backend/app/fit/cache.py:ReportCache` at line 69, `key` at 122, `get` at 133
and `put` at 164. Generated entries use exact JD/title plus runtime identity, a
64-entry LRU and 15-minute reuse TTL. Values are copied. Reuse expiry does not promise
deletion from idle process memory; eviction or restart removes retained entries.

Authored presets are a distinct origin. `curated-provenance.json` binds their existing
sample/report text to current facts. A stale binding disables the preset projection.
Integrity binding does not make draft facts approved or authored narratives calibrated.
`force_live` bypasses both caches and still obeys capacity admission.

Health distinguishes HTTP readiness from assistant capacity. The UI's authored starter
answers, curated examples, professional-profile and contact links remain available.
A public résumé PDF is not present; do not substitute an inaccessible repository URL
and claim that acceptance item passed.

## 6. Grounding: membership is weaker than entailment

Read `backend/app/fit/scorer.py:validate_and_downgrade_verdicts` at line 28, then
`compute_fit_summary` at 100. Allowed local evidence IDs prevent borrowing a citation
from a different requirement. Negative/plans-only facts cannot alone justify positive
experience. A downgrade replaces unsupported prose; appending a disclaimer would leave
the false claim visible. Gaps and gap-containing summaries use deterministic templates.

Escaped data blocks cover chat inquiries/history, retrieved facts, JDs and rewrite
inputs. The system labels these channels untrusted. Tools require strict Pydantic
arguments and allowlisted catalog IDs; unknown keys, oversized/invalid Unicode arguments
cannot execute. These are code guarantees. A delimiter or regex alone does not make
arbitrary instruction injection impossible.

`evals/attacks/phase-7-v1.json` separates 24 structural/lexical examples from six pending
semantic cases. Fake-backed routes prove enforcement and delivery. They do not prove
that real model outputs preserve persona or resist novel false premises. The original
P8 human labels, failed judge outputs, v1/v2 captures and all draft facts are preserved.

## 7. Privacy, browser defenses and audit limits

`main.py` logs route templates, validated opaque request IDs and temporary HMAC IP hashes.
Error logs keep class names, not provider text, JDs or histories. The random hash key
changes per app boot. `logging.json` also governs Uvicorn: no HTTP access logs, no
traceback payloads, warning-level SDK/HTTP logs, and WebSockets disabled for this SSE app.
Hosted platform logs and provider retention require their own operational review.

`frontend/vercel.json` limits script execution to self and connections to self plus the
exact API. Theme bootstrap is a same-origin external file. Markdown images cannot become
tracking requests; URL helpers reject unsupported schemes. Inline styles remain allowed
for existing React styling. CORS constrains browser reads, not curl or bot access.

The approved isolated pip-audit tool scans the resolved Python graph. Gitleaks scans
history, with redacted local output and a pinned action/scanner in CI. npm audit's high
severity gate can pass with moderate findings; never describe that as a clean audit.
After the exact approved updates, Python has zero known findings; npm retains nine
moderate development-tool entries. No automatic fixes or advisory ignores were used.

## 8. Interview practice

1. **Why not release a timed-out attempt?** Dispatch has already crossed the point
   where local cancellation proves no provider work. Unknown usage remains charged.
2. **Why not switch models when quota is exhausted?** Shared account capacity can be
   exhausted too. Model routing does not manufacture independent capacity.
3. **Why bound queue and limiter state?** Rejecting network work while retaining
   unlimited waiting tasks or identity keys merely relocates denial of service to RAM.
4. **Why does an 8/8 replay not mean 100% model accuracy?** Its saved fake/authored
   outputs test protocol/code rules. No generation or semantic judge runs in replay.
5. **Why include Uvicorn in privacy tests?** Application redaction does not override
   independent server access/error handlers. Exercise the deployed logging configuration.
6. **Why keep baseline scores while updating fingerprints?** An intentional source
   change alters provenance; it does not justify weakening metric floors to hide a loss.

Try answering the three teach-back questions without reading sections 2, 4 and 6.
Explain a counterexample for each answer, then revisit tomorrow. Ask for follow-up
examples wherever the dispatch, identity or semantic-review distinctions remain unclear.

## Primary references

- [Groq rate limits and account Limits page](https://console.groq.com/docs/rate-limits)
- [Pinned Groq SDK source](https://github.com/groq/groq-python/tree/v1.7.0)
- [Uvicorn settings](https://www.uvicorn.org/settings/): deployed flags also checked in installed 0.34.0 source
- [FastAPI dependency injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/)
- [MDN CSP guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP)
- [PyPA pip-audit](https://github.com/pypa/pip-audit)
- [Gitleaks action](https://github.com/gitleaks/gitleaks-action)
- [OWASP LLM application risks](https://owasp.org/www-project-top-10-for-large-language-model-applications/)

Public account limits vary. The configured safety ceilings are local policy, not a
claim about remaining account balance. Official links were checked during the phase;
the Uvicorn web fetch was unavailable during close-out, so installed source supplied
the flag/logging verification. No answers to teach-back have yet been assessed.

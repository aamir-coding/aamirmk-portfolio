# Phase 10 study guide — operating a sleeping AI portfolio

Mission: explain and defend the production behavior of this hand-built FastAPI/React
portfolio in interviews, including what the evidence does **not** establish.
Read with the [production runbook](../runbooks/production.md) and
[phase brief](../briefs/phase-10-production-hardening.md). No P9 database is introduced.

## 1. Liveness, readiness and inference capacity

Liveness asks whether a process responds. Readiness asks whether the application can
serve its essential work. Capacity asks whether this process may attempt inference.
Those are separate questions: a healthy, ready API can intentionally rest because its
allowance is absent or exhausted. Returning 503 solely for resting would encourage a
platform to restart it, losing boot-local state without restoring authorization.

`backend/app/main.py` creates app-owned settings, client, ledger and limiter state.
Its lifespan warms retrieval using `asyncio.to_thread(get_retriever)` and an async
local query. Exceptions leave retrieval unready; no provider request is sent.
`backend/app/api/health.py:24` reads this readiness flag and `ledger.snapshot()`.
HTTP 503 signals failed readiness; HTTP 200 plus `assistant_state:resting` signals
working application/fallbacks with no current inference permission. The public response
exposes release identity, not operator credentials, boot IDs or allowance values.

Trace the lines in health: snapshot → readiness → HTTP status → typed response. Removing
the snapshot would lose capacity information; treating every HTTP 200 as model availability
would invent a guarantee. Even local capacity ready cannot prove the provider is reachable.

**Interview:** Why not make a tiny model call in health? It spends shared quota, adds a
provider failure dependency to readiness and can turn monitoring itself into an outage.
Our health path makes no provider calls.

## 2. Immutable releases and provenance

Git SHA tells which source is intended. A successful hosting build tells that a build
ran. Neither alone establishes that the runtime serves the expected assets.

`backend/app/release.py:18` constrains revision/index identity; `load_release` at line
25 uses explicit unknown values for missing/corrupt receipts. `verify_release` at line
32 validates the SHA before writes, loads the committed corpus/vector artifact, then
performs one local dense query. Existing artifact validation checks content/model
compatibility; there is no deploy-time corpus re-embedding. Only after success is the
receipt atomically replaced. `main` at line 53 requires Render metadata or an explicit
SHA. This avoids labelling an unknown deploy using whichever git checkout happens to exist.

`render.yaml` provisions the already-pinned model and executes that verifier.
`frontend/scripts/write-release.mjs` writes a Vercel/GitHub revision receipt after a
successful build. The frontend receipt uses no-store headers; local builds state
unknown identity rather than claiming production provenance. `.gitattributes` prevents
Windows newline conversion from corrupting PDF/PNG/NPZ byte offsets and fingerprints.

**Content workflow:** edit draft facts → explicit offline index build → review metadata
and vectors → compatible retrieval/replay evidence → checked PR → deploy → compare live
revision. Deployment validates the reviewed artifact; it never silently fixes it.
Render's After CI Checks Pass and protected-main settings require dashboard evidence.
Configuration files alone cannot prove that the platform is waiting for checks.

**Interview:** Why not regenerate embeddings during every deploy? That silently changes
reviewed evidence/model identity and may introduce network or resource failures. Rebuilding
is an explicit content change with provenance, not recovery from a failed release gate.

## 3. Authorization, remaining capacity and process identity

A credential answers who may use a control. An allowance answers how much verified
remaining capacity this specific boot may spend. Keeping those separate prevents a
long-lived environment secret from silently renewing a daily inference budget.

`backend/app/api/operations.py:18` is the narrow operator adapter. Read its authentication
path in order: disabled credential → exact single header → constant-time byte comparison
→ reject browser Origin → separate valid/invalid rate buckets → existing ledger.
Anonymous failures cannot consume the authenticated bucket. GET at line 43 exposes
boot/status privately; POST at line 50 rejects above-ceiling grants and delegates to
`InferenceLedger.authorize()`. It never implements a second quota counter.

The ledger owns boot binding, at-most-60-second freshness, UTC expiry by midnight,
one-shot activation and the 60-second unknown-minute drain. Restart/sleep/redeploy loses
the grant; the next process starts closed. Operator settings are typed SecretStr values,
and `hide_input_in_errors=True` prevents invalid credentials appearing in startup error
strings. SecretStr's normal repr masking alone did **not** protect that failure path.

`Cache-Control:no-store` covers normal controls and bounded-request rejection responses.
Controls are absent from public OpenAPI; that reduces exposure but is not authentication.
Use HTTPS ingress and never put credentials in query parameters or browser storage.

**Interview:** Can this prove organization-wide Groq usage? No. The operator must account
for other clients. The in-memory ledger cannot observe another workspace, survive a boot
or provide P9 account-wide durability. A shared authoritative ledger is later work.

**Interview:** Why separate trusted IP parsing from authentication? A parsed IP proves
syntax, not who supplied a forwarded header. Proxy trust needs actual network evidence;
operator authentication must not depend on an unverified XFF value.

## 4. A deterministic monitor is a state machine

`backend/app/monitoring.py:22` validates readiness/capacity payloads. `MonitorState` at
line 28 records bounded observations, last acknowledged condition/time and a target-policy
binding. Aware timestamps prevent persisted naive dates from crashing time arithmetic.

`observe` at line 46 maps resting to normal unless `expect_inference` is true. Two
consecutive bad observations debounce an incident. An acknowledged incident deduplicates;
recovery emits immediately; a new incident waits for a 15-minute cooldown. This is code
and clock arithmetic, not model classification.

`acknowledge` at line 69 runs only after successful notification acceptance. `probe` at
line 78 streams at most 8KiB inside a total 90-second asyncio deadline, rejects redirects
and does not trust HTTP status alone. HTTPX phase timeouts are useful but do not alone
bound an entire slow stream; the outer deadline supplies that bound.

`send_alert` at line 108 emits fixed service/event/time metadata through existing HTTPX.
The optional Discord adapter emits fixed content with mentions disabled. Neither payload
contains the webhook URL, raw IP, request text, token usage or remote response body.
`run` at line 134 acquires an exclusive lock before reading a bound checkpoint, probes,
optionally sends, then atomically writes state. Failed delivery remains pending; an
operator must inspect a stale lock after a crash rather than silently resetting it.

**Worked sequence:** unavailable → unavailable emits incident → webhook fails → next
unavailable retries → webhook succeeds and acknowledges → unavailable is silent → ready
emits recovery. A fake transport test exercises the full CLI path and lock cleanup.

Dry-run is the default. `--send` plus optional `ALERT_WEBHOOK_URL` is an explicit action.
No internal pinger/schedule runs. Frequent external pings can keep Render awake; sleep
policy and detection latency are a deliberate owner trade-off.

**Interview:** Is webhook HTTP 204 proof of phone delivery? No. It proves endpoint
acceptance. Device notification settings/delivery require an end-to-end manual check.

## 5. Cold starts, cancellation and useful degradation

`frontend/src/hooks/useServerHealth.ts:5` owns the health lifecycle. `refresh` at line
10 resets visible state and changes an attempt counter. The effect at line 16 creates
one AbortController, a 2.5-second warming timer and a 90-second deadline. Its handlers
ignore aborted results; finally/cleanup clear both timers; unmount aborts the request.
There is no polling interval or automatic live-request retry.

`frontend/src/lib/api.ts` uses Zod to reject unready HTTP-200 payloads. Missing capacity
is conservatively displayed as resting. `App.tsx:79` clears a previous chat-resting
observation when the user explicitly refreshes, then checks health again. Without this,
`useChat.isResting` could mask a newly ready health result indefinitely. The regression
test renders the actual App, triggers a resting stream and clicks status recovery.

Authored starters run without inference when unavailable/resting. The public résumé
draft/contact routes work while the API wakes. No-JavaScript fallback is actual static
HTML; blocking a bundle is not equivalent to disabling JavaScript for `<noscript>`.
QA used CDP to disable page script execution and verified an empty React root plus
visible static links. Browser viewport emulation does not establish physical iOS behavior.

Measured on 10 November: first production health response 42.391 seconds; after 1,219
seconds without task probes, next response 32.673 seconds, HTTP 200/resting. Other
external traffic cannot be excluded. These observations describe the deployed P7 service,
not an unshipped P10 revision or a guaranteed wake-up SLA.

## 6. Accessibility, public assets and honest evaluation

Touch-target/overflow checks assert against rendered geometry at 375×667, 390×844,
768×1024 and 1440×900. Actual failures led to 44px controls, proper group roles and
token contrast fixes. Explicit-light mode must work even when OS preference is dark:
an OS-only warning override previously put pale text on a pale background.
The screenshot and axe evidence are scoped QA, not a complete accessibility certification.

`formatPublicSourceHref` preserves safe URL handling while suppressing exactly the
observed anonymous-404 destinations. Source chips retain receipt text and identifiers;
no replacement URL is invented as evidence. Recheck availability before restoring a
suppressed link. LinkedIn's automated-block response is not proof the profile is absent.

The one-page public PDF is visibly DRAFT, omits phone and unresolved dates/claims, and
has a readable source Markdown route. Neither creating it nor correcting cover text
approves the 76 draft facts. PNG social metadata uses an absolute default-domain URL.

Application-source changes invalidate result fingerprints even when scores are identical.
The reviewed P10 compatibility update must preserve all seven floors, critical replay
checks, frozen human grades, failed judge validation and unexecuted held-out status.
Schema/replay success cannot establish novel semantic entailment or injection resistance.

**Interview:** Why keep a failed judge result public? Replacing a valid unfavorable
judgment with retries selects evidence. The failure is a useful engineering outcome;
new independent validation needs a new reviewed protocol, not relabelled old answers.

## 7. Production interaction tuning: token estimation vs. byte sliding windows

In rapid conversational testing, an in-memory rate limiter can inadvertently penalize
honest interaction if its capacity unit is miscalibrated against prompt geometry.

1. **Serialized UTF-8 Bytes vs. Real LLM Tokens:** `reserve_input_tokens` approximates
   worst-case token counts using serialized UTF-8 message bytes plus headroom:
   `len(encoded) + 512 + 32 * count`. A multi-turn conversation with 4 retrieved chunks
   and JSON tool definitions is ~1,700 real BPE tokens, but serializes to ~29,000 JSON bytes.
   Under a sliding minute window of 32,000 bytes, a second prompt within 60 seconds
   pushes the sliding window to 38,500 bytes, causing the ledger to reject requests with
   `wait_expired`. Calibrating the local capacity ceiling to 1,000,000 TPM admits rapid
   sequential queries while preserving all concurrency, rate-limiting, and quota structures.

2. **Tool-Call Message Formatting:** The Groq API adheres strictly to the OpenAI specification:
   assistant messages containing `tool_calls` require `content: null` when there is no text.
   Sending `content: ""` triggers HTTP 400 `tool_use_failed`. In `backend/app/llm.py`,
   sanitizing `entry["content"] = m.content or None` prevents API rejections on card summoning.

3. **Query Rewriting Trade-Off:** In interactive chat, running a speculative query rewrite
   adds 1.5–2.0 seconds of latency and consumes additional utility quota. Exposing
   `ENABLE_QUERY_REWRITE` allows turning this off for near-instant direct retrieval during
   testing and demos, with zero architectural code deletion.

## Retrieval practice — answer before looking back

1. After a Render restart, health returns 200/resting. Why should an uptime monitor
   avoid treating this as a process failure, and what exact evidence/control opens inference?
2. A webhook fails after the second outage check. Which state may be saved, which
   state must remain unchanged, and what should the next check do?
3. Source code changed but all seven offline scores are identical. Why must identity
   still be reviewed, and which facts about accuracy/held-out evidence remain unavailable?

Answers are not assumed or pre-graded. Use these for the interactive phase teach-back.

## Official reading

- [Render free services](https://render.com/docs/free): sleep, cold boot and ephemeral disk.
- [Render deploy/CI ordering](https://render.com/docs/deploys#automatic-deploys): account settings required for checked deploys.
- [Render health checks](https://render.com/docs/health-checks): HTTP readiness semantics.
- [Render environment metadata](https://render.com/docs/environment-variables): source SHA supplied at build/runtime.
- [HTTPX async clients and streaming](https://www.python-httpx.org/async/): transport/response lifecycle used by monitoring.
- [Python total deadlines and threads](https://docs.python.org/3.13/library/asyncio-task.html): cancellation versus blocking work.
- [Pydantic settings error hiding](https://docs.pydantic.dev/2.10/api/config/#pydantic.config.ConfigDict.hide_input_in_errors): why SecretStr alone was insufficient.
- [React effect cleanup](https://react.dev/reference/react/useEffect): abort/timer ownership on retry and unmount.
- [Discord incoming webhooks](https://docs.discord.com/developers/resources/webhook): fixed content delivery without a bot SDK.
- [Vercel Git deployments](https://vercel.com/docs/git): preview/production source identity and deployment workflow.

Read the [final evidence ledger](../audits/2026-11-10-phase-10-production.md) for actual
commands/results and remaining release/semantic acceptance, rather than inferring them
from this explanation.

# Production operations

Default deployment: one Render free worker, existing Vercel frontend, normal API
sleep. Phase 9 adds optional Postgres connectivity.
No uptime ping is configured to keep the service awake. An on-demand probe wakes it.

## Phase 9 database setup

1. Keep the `portfolio` schema private in Supabase. Use a direct TLS connection
   or the IPv4 session pooler. Give the runtime role access to the application
   schema and tables. Keep the migration role's DDL credentials separate.
2. Set `MIGRATION_DATABASE_URL` in the migration shell and run
   `python -m alembic -c backend/alembic.ini upgrade head` from the repository root.
   Use `current` to confirm the applied revision. Supply `DATABASE_URL` to the API
   runtime. Credentials stay in the shell or hosting environment.
3. Keep `ANALYTICS_IP_HASH_KEY` unset in hosted environments until scheduled
   retention is ready. With a database and key configured, the API writes
   successful questions, usage and known company opens in the background.
   The worker may drop records during a database outage or when its queue fills.
4. For local migration and write tests, set `PORTFOLIO_TEST_DATABASE_URL` to a
   disposable loopback database named `portfolio_test` and run
   `python -m pytest -c backend/pyproject.toml backend/tests/test_database.py`.
   The integration tests exercise downgrade as well as upgrade.

## Phase 9 handoff

1. Apply the database migrations before enabling handoff. Set `DATABASE_URL`,
   `TELEGRAM_BOT_TOKEN` and the intended private `TELEGRAM_CHAT_ID` in the API
   environment for hosted verification. Open the bot chat with the recipient
   account before testing delivery.
2. Submit a synthetic transcript through the card. HTTP 202 means the request
   is stored. Confirm arrival in Telegram and match the notification's UUID
   to the handoff row. Long transcripts arrive as a plain-text attachment.
3. The worker sends pending rows when the process is awake. A failed send
   records `failed`. An interruption before the status commit leaves the row
   pending. Compare notification UUIDs when a delivery may have succeeded
   before a restart.

## Release and rollback

1. Open a PR to main. Require CI backend/frontend/offline eval and security checks.
2. Render must use **After CI Checks Pass**, not the default On Commit. Confirm this
   in its dashboard; Git config does not prove that the account setting is enabled.
   Vercel deployment gating must likewise be verified; protect main against merges
   with failing checks. A successful preview alone does not prove production identity.
3. Render provisions the pinned embedding model at build time, then runs
   `python -m app.release`. It verifies the committed corpus/vector/model fingerprints
   with a local query and writes ignored `backend/release.json` with Render's SHA.
   A missing model or stale artifact fails the build, rather than silently repairing it.
4. Compare `/api/health` revision with the intended Git SHA and hosting deploy record.
   Verify frontend `/release.json` too. Unknown revision is not deployment proof.
5. After a merge/deploy, check service readiness and capacity separately. A closed
   allowance is expected after a boot and is not a reason to restart the service.
6. Roll back using the provider's previous successful deploy and verify both revisions
   and asset checks again. The new process has a new boot ID and stays closed until a
   separately verified remaining allowance is authorized. Never reuse the old grant.

Official references: [Render CI gating](https://render.com/docs/deploys#automatic-deploys),
[Vercel Git deployments](https://vercel.com/docs/git),
[Render free tier](https://render.com/docs/free).

## Content changes

Public facts live in `backend/app/data/facts/`, not an invented knowledge directory.
Facts remain DRAFT until Aamir approves them; editing a file does not approve it.
For a fact change, provision model assets explicitly, run
`python scripts/generate_embeddings.py` using the cached model, review the new
manifest/vector diff, then refresh reviewed provenance and offline evidence through
the existing evaluation workflow. Never regenerate the committed index during deploy.
Run full retrieval/replay gates before merge; do not lower thresholds to get green CI.
Redeploy to load new immutable assets. Existing failed judge validation and held-out
cases are not reusable tuning evidence.

## Operator activation

`OPS_TOKEN` is a separate high-entropy credential (generate with
`secrets.token_urlsafe(32)`), configured only in Render, never Vite or browser storage.
Empty means both control methods return 404. This credential authenticates an operator;
it does not itself authorize any generation. Use HTTPS on the public Render URL,
without an Origin header; never place credentials in a URL or command history.

1. Verify actual account limits, today's remaining tokens/requests and all other
   processes sharing the key. Coordinate or stop independent usage first. Record
   that evidence privately. Settings are ceilings, not an allowance.
2. GET `/api/ops/inference` with `Authorization: Bearer <operator credential>` from
   a private operator client to read this process's boot ID. Both methods are globally
   capped at 30 calls/minute; failed authentication uses a separate bounded 30/minute
   bucket so anonymous traffic cannot exhaust operator capacity. No browser control page exists.
3. Submit an `Allowance` to POST at the same path: `boot_id`, UTC `verified_at`, UTC
   `expires_at`, integer `requests`, integer `tokens`. Verification must be at most
   60 seconds old; expiry must be later than verification and no later than next UTC
   midnight. Requests/tokens must not exceed configured shared daily ceilings and must
   deduct all prior/independent use. There are no extra fields or automatic renewals.
4. Success retains the ledger's 60-second unknown-minute drain. Duplicate/stale/foreign
   boot grants return sanitized 409. Rejections do not open a closed ledger. Expiry,
   restart, sleep or redeploy requires a newly verified boot/remaining allowance.
5. Confirm capacity via health after the drain. A ready snapshot means locally admitted
   capacity, not guaranteed provider availability or account-wide durable accounting.

Control bodies/credentials never enter application logs. All control responses, including
errors, use no-store. Allowance values are private operational evidence. No control
request or live allowance has been sent to production during implementation.

### Ephemeral container boot authorization (Render Free Tier)

Under DRN-067, Render free tier container sleep/restart cycles automatically authorize
a fresh, non-reusable boot allowance on startup when `ENVIRONMENT == "production"` and
`GROQ_API_KEY` is present (or `AUTO_AUTHORIZE_INFERENCE=True`). The allowance binds to
the container's random `boot_id`, expires at UTC midnight, and uses `warm_up_seconds=0.0`
to eliminate cold-start wait penalties. The manual operator activation protocol above remains
available for operator-driven allowance refreshes or custom quota bounds.

Under DRN-068, byte-based ledger limits are calibrated to `tpm=32000` (`INFERENCE_SHARED_LIMITS`
and `INFERENCE_MODEL_LIMITS`), accommodating ~9,000-byte grounded chat prompts and ~18,500-byte
2-turn tool calls while bounding real provider traffic strictly within Groq's 8,000 real TPM ceiling.

## Proxy and hosted privacy verification

Leave `TRUST_PROXY_HEADERS=false` until the actual socket peer and header chain are
verified. Uvicorn proxy rewriting remains disabled. On Render, gather only redacted
peer/network metadata through a temporary owner-controlled diagnostic; do not enable
raw request/header logging. Verify two independent clients and forged/duplicate XFF
behavior. Configure only proven CIDRs; a syntactically valid IP is not trust evidence.

Production CORS allows only the production frontend (localhost is development only).
Preview origins must be deliberately allowlisted; do not add a wildcard. A domain
change requires matching CSP connect-src, CORS and `VITE_API_BASE_URL` changes.

Application logs contain request ID, route, status, duration and ephemeral salted IP
hash, not transcripts. Uvicorn access logs/WebSockets are disabled. Review hosted
Render/Vercel/Groq log retention and access separately; record the account's actual
retention here before launch. **Hosted retention: not yet verified.** No P9 message
storage or 90-day cleanup is claimed.

## External monitoring

The provider-free CLI is `python -m app.monitoring` from backend. It makes only a
bounded GET to health and, with separate explicit consent, a metadata-only webhook.
It never sends chat, fit or judge requests. Default dry-run example:

```powershell
python -m app.monitoring --url https://aamirmk-portfolio-mlr4.onrender.com/api/health --state ../build/monitor.json
```

Run outside the API process, with one state file per URL/policy. A local exclusive
lock prevents overlapping runs; after a crash, first verify no monitor is running
before reviewing/removing its stale lock. Malformed/foreign state fails closed.
The monitor waits up to 90 seconds (including cold boot), bounds response bytes and
does not follow redirects. A 200 response must also validate ready/status/capacity.

Default policy treats resting as expected. Add `--expect-inference` only during an
operator-approved live window. Two consecutive bad checks produce one incident;
successful delivery suppresses duplicates, recovery sends immediately, and new
incidents are separated by 15 minutes. Failed delivery stays pending. Dry runs do
not acknowledge delivery. This is monitor-local bookkeeping, not durable API quota.

For an approved HTTPS JSON webhook, keep its secret URL in `ALERT_WEBHOOK_URL`
and add `--send`. Its contract is exactly `service`, `event`, `at`; a provider that
requires another body needs a reviewed adapter. No destination is preconfigured or
notification sent. Credential-bearing URLs and raw errors are never printed.
Exit codes: 0 healthy/expected resting; 1 service/capacity incident; 2 config/delivery
failure. Confirm a controlled outage, a resting transition and phone recovery delivery
before claiming monitoring is operational.

Schedule choice remains owner-controlled. Frequent polling can prevent Render sleep;
default proposal is no keep-alive and no schedule created. A 30-minute external check
preserves idle periods but has coarse detection and wakes the API; a five-minute check
reduces detection latency and changes the instance-hours policy. Record that trade-off
and check current account terms before enabling any schedule.

### Free channel example: Discord

Create a private Discord channel, open its Integrations → Webhooks, create an incoming
webhook and copy its secret URL into the monitor host's `.env` as `ALERT_WEBHOOK_URL`.
Set `ALERT_WEBHOOK_FORMAT=discord`, enable phone notifications for that private channel,
then explicitly run the monitor with `--send` against a controlled test incident.
Discord receives a fixed `content` message with mentions disabled; no IP, usage tokens,
prompt or webhook URL is included. A 2xx webhook response proves HTTP acceptance only;
verify actual phone delivery separately. Rotate the webhook if its URL is disclosed.
See [Discord incoming webhooks](https://docs.discord.com/developers/resources/webhook).
No Discord signup/channel creation/message has been performed by this implementation.

`ALERT_WEBHOOK_URL` is optional and validated as an HTTPS secret setting. The existing
HTTPX dependency supplies transport; no notifier SDK/dependency is added. The notifier
lives in `backend/app/monitoring.py` as an operational adapter, not in request handling.

Alternatively configure a free external HTTP monitor (Better Stack/UptimeRobot) for
GET `/api/health`, accepting only HTTP 200 and checking JSON `ready:true`. HTTP-only
checks do not detect unexpected resting: add a JSON-body capacity assertion or run
the supplied CLI with `--expect-inference` during approved live windows. Account-specific
free feature limits and notification destinations must be checked at setup time.

### Physical device smoke test after deployment

- On physical iOS Safari and Android Chrome, open the default Vercel URL in a new tab.
- Check 375×667/390×844-equivalent portrait and landscape: readable text, no horizontal
  page scroll, usable 44px touch targets, theme toggle and keyboard composer behavior.
- With a throttled 4G connection and API idle for 20 minutes, use an authored starter
  immediately; record wake-up duration/status, resting alternatives and status retry.
- Open the résumé PDF/source, role examples and source links; try no-JS fallback.
- Share the URL privately in WhatsApp/LinkedIn and inspect its image/title/description.
- Record device/OS/browser, network, deployment SHA, date and any failed step. Browser
  viewport emulation is automated coverage, not evidence from either physical device.

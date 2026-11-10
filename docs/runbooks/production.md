# Production operations

Default deployment: one Render free worker, existing Vercel frontend, normal API
sleep, no database until P9. Generation starts closed after every process boot.
No uptime ping is configured to keep the service awake. An on-demand probe wakes it.

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

## Identity and privacy

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
   capped at 30 calls/minute; rejected auth also counts. No browser control page exists.
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

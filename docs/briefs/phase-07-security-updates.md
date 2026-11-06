# Audit findings and proposed compatibility updates

Prepared 6 November 2026. Proposal only; application dependencies are unchanged.

The approved scans actually ran. Python reported 16 advisory rows in two packages
(eight distinct advisory IDs after duplicate rows): pytest 8.3.5 and Starlette 0.46.2.
The highest required fixed versions in that result are pytest 9.0.3 and Starlette 1.3.1.
The current FastAPI 0.115.11 constraint does not admit the required Starlette version;
pytest-asyncio 0.25.3 requires pytest <9.

`npm audit` reported ten affected package entries: two critical (Vitest/tinypool),
eight moderate, zero high. No automatic fixes were run. The installed Vitest is 3.2.7.

Proposed exact update set, verified against official PyPI/npm metadata:

| Package | Proposed pin | Purpose |
|---|---|---|
| FastAPI | 0.135.0 | Supports Starlette >=0.46 without the old <0.47 constraint; keeps Pydantic v2 and existing hand-framed StreamingResponse |
| Starlette | 1.3.1 | Explicit pin of the existing underlying framework dependency at the required audited fix |
| typing-inspection | 0.4.2 | Newly required FastAPI dependency; small typing helper, requires typing-extensions >=4.12 (installed 4.16.0) |
| annotated-doc | 0.0.5 | Newly required FastAPI dependency; annotation documentation helper |
| pytest | 9.0.3 | Audited fixed test runner |
| pytest-asyncio | 1.4.1.post1 | Supports pytest >=8.4, including the proposed pytest 9 |
| Vitest | 4.1.11 | Fixes the reported mocker traversal advisory and avoids affected tinypool generation; supports current Vite 6 and Node 22/24 |

Existing Pydantic/Groq/FastEmbed/NumPy/HTTPX/React/Vite pins and application architecture
remain unchanged. Starlette 1.3.1 still supports the existing HTTPX TestClient adapter
with a deprecation warning; do not add HTTPX2 or another HTTP stack for this update.

The exact manifest changes are in [phase-07-security-updates.patch.proposed](phase-07-security-updates.patch.proposed).
Approval is needed specifically for the two newly required runtime packages under
AGENTS.md rule 8. The update also moves test-runner major versions; acceptance requires
complete backend/eval and frontend suites, lint, typecheck/build/gzip, cancellation/
middleware/stream regression checks and repeat audits. A failed compatibility check
will be diagnosed before adoption. Eight moderate npm entries remain visible and
need assessment; no claim of a vulnerability-free environment is made.

Evidence files (ignored local artifacts): `build/phase7-pip-audit.json`,
`build/phase7-python-environment.txt`, `build/phase7-npm-audit.json`.
The Python audit cache emitted a Windows cross-drive cache-write warning; the audit
completed and wrote results. Future runs will use an explicit workspace cache path.

Sources:

- [Starlette 1.3.1 metadata](https://pypi.org/pypi/starlette/1.3.1/json)
- [FastAPI 0.135.0 metadata](https://pypi.org/pypi/fastapi/0.135.0/json)
- [pytest 9.0.3 metadata](https://pypi.org/pypi/pytest/9.0.3/json)
- [pytest-asyncio metadata](https://pypi.org/pypi/pytest-asyncio/1.4.1.post1/json)
- [Vitest advisory](https://github.com/advisories/GHSA-82fw-gwwq-j7x9)
- [Tinypool advisory](https://github.com/advisories/GHSA-85c8-ppgw-ccpr)
- [Vitest 4.1.11 metadata](https://registry.npmjs.org/vitest/4.1.11)

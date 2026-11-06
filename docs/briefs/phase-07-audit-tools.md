# Phase 7 audit tools: version and workflow proposal

Prepared 6 November 2026. **Exact additions explicitly approved by Aamir and applied.**
The isolated local audit ran; the workflow is enabled in `.github/workflows/security.yml`.
Cloud execution awaits a separately authorized push. The inert proposal below is retained
as the reviewed specification.

Proposed additions:

- `pip-audit==2.10.1`, installed into an isolated CI virtual environment only. Scan
  the actual frozen installed Python dependency graph with the PyPI vulnerability
  service. Record JSON results; fail on advisories. No `--fix`, blanket ignore or
  automatic dependency upgrade. Runtime manifests and global tools remain unchanged.
- `gitleaks/gitleaks-action@ff98106e4c7b2bc287b24eaf42907196329070c7`, the peeled
  commit of `v2` independently verified with `git ls-remote` on 6 November. Pin its
  scanner binary to `GITLEAKS_VERSION: 8.30.1` (upstream tag also verified). Scan full
  checked-out history. Disable PR comments, notifications, summary and report uploads;
  keep repository permissions read-only. The upstream action requires a license for
  organization-owned repositories; its docs exempt personal accounts. Do not invent
  a license or infer organization eligibility from a repository name.
- Run existing `npm audit --audit-level=high` against the committed frontend lockfile
  in the existing frontend job. Report findings; do not run `npm audit fix`.

The exact proposed workflow is [phase-07-security.yml.proposed](phase-07-security.yml.proposed).
It is outside `.github/workflows` and cannot run as a workflow. Approval would permit
adding this workflow, the existing npm audit step and performing the local isolated
Python audit. Installation remains local/CI, never global. No model calls or remote
writes are included. Any vulnerability remediation that changes pinned versions will
be prepared separately with compatibility evidence.

Sources checked:

- [pip-audit 2.10.1 official package/docs](https://pypi.org/project/pip-audit/2.10.1/)
- [Pinned Gitleaks action documentation](https://github.com/gitleaks/gitleaks-action/blob/ff98106e4c7b2bc287b24eaf42907196329070c7/README.md)
- [Scanner v8.30.1](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1)

No audit outcome is claimed until the approved tools actually run. Dependency scans
need network access and are separate from fake-only offline application tests.

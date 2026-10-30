# CloudForge v0.3 operations and release checklist

## Scope and evidence

CloudForge's live service is https://cloudforge-demo.onrender.com. It runs only
the fictional, read-only NexusDesk demo. This phase adds release checks and
operational reports without cloud credentials or an external monitoring account.

There is no continuous polling schedule, alerting integration or automatic
rollback. The next roadmap phase covers an observability dashboard and incident
response drill. GitHub notification delivery depends on the owner's settings.

## Manual release gate

1. Open a PR and review the source diff, upstream SHA and base-image digest.
2. Require all CI jobs to pass: source checks, Terraform validation, local
   container smoke checks and the Render-image scan/security checks.
3. Review `render-image-evidence-<SHA>` in the CI run. Inspect unfixed findings;
   do not interpret a passing gate as an empty vulnerability report.
4. Merge the reviewed PR. Confirm CI is green on the exact main commit.
5. In the existing Render service, deploy the intended main commit. Auto-deploy
   remains off; no workflow in this repository calls a deployment API.
6. Monitor the specific deploy until Render reports **Live**. A queued/building
   response is not release success. Confirm the commit in its deploy record.
7. Run the HTTPS checker against the live origin, or manually run **Verify live
   Render demo** in GitHub Actions. Record the Render deploy ID and source commit
   alongside the JSON report in release evidence.
8. Review runtime logs for boot errors, repeated 5xx responses and unexpected
   operational routes. The expected blocked-route probes deliberately return 404.

Branch protection and the Render CI gate are not enforced by this repository's
source changes. Manual review is the active release control.

## Image vulnerability policy and SBOM

The Render-image CI job builds the final runtime image, then:

- Saves all severities and unfixed findings to `reports/trivy.json`.
- Generates `reports/sbom.cdx.json` in CycloneDX format.
- Fails for **HIGH or CRITICAL vulnerabilities with an available fix**, across
  OS and application packages. Unfixed findings are reported, not blocked.
- Fails when the scanner, vulnerability database or image inspection is unavailable.
- Uploads available reports and image/source identifiers even if the gate fails.

No CVEs are suppressed in this release. Fix a finding by reviewing a new base
image digest or dependency version, then rerun CI. Do not change the gate to
success or add an exception merely to get a green check.

The official Python base image and workflow actions are pinned by digest/SHA.
Update those pins through a reviewed PR and rerun the full CI suite. The pinned
upstream app still uses dependency ranges; a fresh Render build can resolve
newer Python packages than a CI image. The SBOM describes only its CI-built
image. It is not signed provenance or a runtime inventory.

## Operational check

```bash
python scripts/smoke_cloud.py https://cloudforge-demo.onrender.com \
  --attempts 8 --retry-delay 5 --report reports/render-verification.json
```

Only standard-HTTPS Render/App Runner origins are allowed. Redirects are not
followed. A health response with `demo_mode: true` and expected demo content
must pass before any internal or empty-write probes run.

The checker makes 13 checks: health, demo/security headers, CSS, seven internal
routes and three rejected empty POSTs. It records UTC start/end times, elapsed
milliseconds, status codes, readiness attempts and pass/fail. It saves neither
response bodies nor header values. `verifier_revision` is the checker commit;
it must not be labelled as the deployed image revision.

Transient health responses (429/502/503/504) and network timeouts are retried
within the configured limit. A healthy response with the wrong demo identity,
malformed JSON, redirects, unexpected route status or weaker CSP fails without
retry. Checks remain active under `python -O`.

In Actions, verification reports and image evidence expire after seven days.
Download them earlier if needed for a portfolio review. No secret or AWS/Render
API token is required for these workflows.

## Diagnose a failed check

| Symptom | Check before retrying |
|---|---|
| Readiness timeout | Render deploy status, cold start and runtime logs; use bounded readiness retries |
| Build failure | First failing Docker layer, pinned upstream fetch and dependency resolution |
| Scan failure | Report, scanner/database availability, fixable vulnerability versions |
| `demo_mode` false or internal route exposed | Stop release promotion; inspect demo flags and the exact deployed commit |
| CSP/header failure | Confirm the pinned middleware and TLS/proxy configuration |
| CSS failure | Build-time collectstatic, manifest and served static path |
| JSON report says pass but commit differs | The probe checks the current app; reconcile its Render deploy record separately |

## Recovery and rollback

Use the existing service's deploy history to select a previously successful,
verified release. Confirm its commit and compatibility first. Monitor the new
rollback deploy to **Live**, rerun the full HTTPS check and retain its report.
Do not run a destructive database command: this public demo has no operational
database. Do not delete or alter the separately hosted portfolio services.

Rollback availability depends on retained Render artifacts and the Free plan's
limits. A live rollback drill has not yet been performed or claimed complete.

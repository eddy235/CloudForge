# CloudForge — Secure cloud delivery (AWS optional)

**Docker · GitHub Actions · Render · Trivy · Python · Terraform · optional AWS OIDC/ECR**

CloudForge is the build, security and delivery system around the fictional
[NexusDesk demo](https://github.com/eddy235/NexusDesk). Its portfolio value is
container delivery and operations; the helpdesk application is a separate project.

**Live demo:** https://cloudforge-demo.onrender.com/demo/

**Current milestone: v0.3 — Render release hardening and operational verification.**
Render is deployed on the Free plan. The AWS configuration remains optional,
disabled by default and unprovisioned. No AWS account is needed for the main path.

## What this release demonstrates

- NexusDesk source pinned to the reviewed commit in `UPSTREAM_VERSION`.
- Both Dockerfiles pin the official Python base image to a reviewed digest.
- Non-root runtime and loopback-only, read-only container tests.
- GitHub CI tests source, validates Terraform without applying it, builds both
  image variants and exercises the synthetic demo's security boundaries.
- The Render-image job saves a full vulnerability report and CycloneDX SBOM,
  then fails on **fixable HIGH or CRITICAL** OS/library vulnerabilities. Unfixed
  findings remain visible in the full report. Scanner failures fail the job.
- Workflow actions are pinned to full commit SHAs. CI needs no cloud credentials.
- A bounded HTTPS checker records 13 checks, response times and failure evidence
  as JSON. It retries readiness for cold starts, rejects unsafe destinations and
  redirects, and checks demo identity before attempting empty blocked POSTs.
- GitHub's **Verify live Render demo** workflow checks the deployed demo when its
  checker changes on main, or on demand. It uploads reports and a job summary.
  It does not deploy a revision and is not continuous uptime monitoring.

## The actual Render configuration

| Setting | Live service |
|---|---|
| Source | `eddy235/CloudForge`, `main` |
| Dockerfile | `Dockerfile.render` |
| Region / compute plan | Oregon / Free |
| Mode | Fictional read-only demo; DEBUG off |
| Automatic deployments | **Off**; deployment follows manual CI review |
| Render health check | Default **TCP** probe |
| Application health | `/health/`, separately checked over HTTPS |
| Data / database | Synthetic examples; no operational database |

The service was created directly through the Render connection. It is **not
managed by a Blueprint**. `render.yaml` is an optional configuration reference
with HTTP health checks and CI-gated auto-deployment; editing it does not change
this existing service. Those two settings still need Dashboard configuration.

[Demo](https://cloudforge-demo.onrender.com/demo/) ·
[Render service](https://dashboard.render.com/web/srv-dbi4erks728c73cajlag) ·
[GitHub Actions](https://github.com/eddy235/CloudForge/actions)

## Verify the deployed service

```bash
python scripts/smoke_cloud.py https://cloudforge-demo.onrender.com \
  --report reports/render-verification.json
```

CLI readiness defaults to eight attempts with five seconds between retries;
each request times out after 15 seconds. Security/content failures are not
retried. JSON excludes response bodies, header values and secrets. The
`verifier_revision` field identifies the checker, not the deployed image.

For an optional App Runner demo, supply its HTTPS origin to the same script.
Only `*.onrender.com` and `*.awsapprunner.com` origins on standard HTTPS are allowed.

## Local build and tests

Prerequisites: Git, Python 3.11+, Docker Engine/Desktop with Compose.

```bash
python scripts/fetch_upstream.py
docker compose up --build -d
python scripts/smoke_local.py
docker compose down
python -m unittest discover -s tests -v
```

Local preview: **http://127.0.0.1:8000/demo/**. The self-contained Render image
can also be built with `docker build -f Dockerfile.render -t cloudforge-render:test .`.

## Release evidence and limits

In each successful CI run, download `render-image-evidence-<SHA>` for the
full Trivy JSON, CycloneDX SBOM, image ID and source checksums. Operational
workflows save separate verification artifacts. Artifacts expire after seven days.

The SBOM inventories the **CI-built image**, not the running Render container.
Python dependency ranges in the pinned upstream still resolve at build time;
full dependency locking and signed provenance are future work. A source/base
pin alone does not prove bit-for-bit image reproducibility. The live service's
source revision must be checked in its Render deploy record.

Automatic deploys remain off. The image gate is a CI check, not an enforced
Render release gate or GitHub branch-protection policy. Follow the documented
manual release checklist until those controls are configured.

## Optional AWS reference

Terraform includes immutable ECR, branch-scoped GitHub OIDC and an opt-in App
Runner runtime. `enable_runtime=false` by default. No AWS resources have been
provisioned or verified with an AWS account. CI never runs `terraform apply`.

```bash
terraform -chdir=infra/terraform fmt -check -recursive
terraform -chdir=infra/terraform init -backend=false -input=false
terraform -chdir=infra/terraform validate
```

AWS publishing remains a separate manually triggered workflow requiring reviewed
OIDC configuration and cost decisions. See [AWS deployment](docs/AWS_DEPLOYMENT.md).

## Project materials

- [Render deployment and live configuration](docs/RENDER_DEPLOYMENT.md)
- [Release checklist, scan policy and operational reports](docs/OPERATIONS.md)
- [Architecture and trust boundaries](docs/ARCHITECTURE.md)
- [Operator runbook](docs/RUNBOOK.md)
- [Security boundaries](SECURITY.md)
- [Milestone roadmap](ROADMAP.md)

# CloudForge build roadmap

The main learning path uses **Render and GitHub**, without an AWS account.
CloudForge delivers secure builds, cloud delivery and operations around the
separate NexusDesk fictional-data demo.

| Version | Milestone | Acceptance criteria |
|---|---|---|
| v0.1 | Container foundation + AWS reference IaC | Pinned NexusDesk source, non-root image, isolated demo smoke tests, CI, ECR/OIDC Terraform; no AWS apply |
| v0.2 | Optional AWS runtime reference | App Runner Terraform validated, runtime off by default; no actual AWS deployment/rollback claimed |
| Render deployment | AWS-free live deployment | Separate Free Render Docker service live and verified over HTTPS |
| **v0.3** | **Render release hardening and operational checks** | Base-image digest pins, action SHA pins, fixable HIGH/CRITICAL image gate, full scan and SBOM artifacts, bounded JSON verification and an operational runbook |
| v0.4 | Observability and incident response | Deployment/health dashboard, log review, failure diagnosis and a recorded supervised rollback drill |
| v0.5 | Reliability and supply-chain evidence | Dependency locking, provenance, explicit release promotion, cleanup/cost review and recovery evidence |
| v1.0 | Portfolio release | Threat model, architecture, runbook, tested evidence and clear limits |

## Live Render boundaries

https://cloudforge-demo.onrender.com/demo/ is the active deployment. Automatic
deployments are off and Render uses TCP health checks. The application `/health/`
endpoint is verified separately. The optional Blueprint describes additional
settings; it does not currently manage this service.

v0.3's CI and live-demo checks produce evidence but do not enforce branch
protection, configure Dashboard settings or prove the running image matches a
CI image. See [operations](docs/OPERATIONS.md) for the manual release gate.

**Next phase: v0.4 observability and incident response**, continuing on Render.
AWS provisioning remains an independent opt-in track requiring its own account,
cost review and live tests. It is not a prerequisite for any Render milestone.

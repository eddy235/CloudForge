# CloudForge build roadmap

| Version | Milestone | Acceptance criteria |
|---|---|---|
| **v0.1** | Container foundation + AWS IaC | Pinned NexusDesk source, non-root Docker build, read-only demo security smoke checks, automated CI, ECR Terraform module, branch-limited GitHub OIDC role, no AWS apply required |
| v0.2 | First AWS runtime | Deploy only after billing review; TLS-enabled entry point, health check, logs and documented total monthly cost; rollback verified |
| v0.3 | Harden deployment | Least-privilege runtime IAM, secret retrieval, deployment approvals, image scan gates and budget alarms |
| v0.4 | Observability | Dashboard, CloudWatch logs/alerts, incident drill and restore procedure |
| v0.5 | Reliability & optimization | Lifecycle cleanup, hardened provenance, deployment smoke tests and repeatable cost teardown |
| v1.0 | Portfolio release | Threat model, operations runbook, evidence of CI/runtime checks and architecture diagram, clear limitations |

The application under demonstration is the pre-existing NexusDesk fictional-data demo. CloudForge's deliverable is the **secure build/deploy and cloud infrastructure system**, not a duplicate IT helpdesk application.

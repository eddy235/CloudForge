# CloudForge — Security and cost boundaries

This project demonstrates security-conscious cloud engineering, but is **not** a formally audited production platform.

- Public-facing app, when deployed later, must use the separate fictional-data NexusDesk demo, never operational employee accounts, tickets or assets.
- Do not switch `NEXUSDESK_DEMO_MODE` to `false` on a public host or turn on `DJANGO_DEBUG`.
- CI is intentionally AWS-free; ECR publishing is **manual and disabled until OIDC is explicitly configured**.
- IAM trust must match exactly the intended GitHub repo and `main` branch. Do not use wildcard subjects.
- No long-lived AWS keys in environment files, GitHub secrets or Terraform state.
- Use immutable tags, image scanning, container non-root user, read-only Compose filesystem, non-privileged port and restricted local bind.
- The Python base image tag is not yet digest-pinned; dependency ranges in upstream also still permit updates. Prior to production, pin digests, run dependency vulnerability reviews, and implement signed provenance/SBOMs.
- AWS registry storage and scans may cost money even without running servers. `terraform apply` and GitHub ECR publishing must be deliberate.
- Terraform local state is ignored and is not team-safe; configure a protected remote state backend before team use.
- v0.1 does **not** configure a public AWS runtime or HTTPS. Local Compose disables HTTPS redirect only for localhost testing.

Report vulnerabilities privately to the repository owner rather than posting secrets in a public issue.

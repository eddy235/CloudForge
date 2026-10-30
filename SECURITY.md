# CloudForge — Security and cost boundaries

This project demonstrates security-conscious cloud engineering, but is **not** a formally audited production platform.

- The deployed public app must use the separate fictional-data NexusDesk demo, never operational employee accounts, tickets or assets.
- Do not switch `NEXUSDESK_DEMO_MODE` to `false` on a public host or turn on `DJANGO_DEBUG`.
- CI is intentionally AWS-free; ECR publishing is **manual and disabled until OIDC is explicitly configured**.
- IAM trust must match exactly the intended GitHub repo and `main` branch. Do not use wildcard subjects.
- No long-lived AWS keys in environment files, GitHub secrets or Terraform state.
- Use immutable tags, image scanning, container non-root user, read-only Compose filesystem, non-privileged port and restricted local bind.
- Both Dockerfiles pin the official Python base image digest. CI records a full scan and CycloneDX SBOM and blocks fixable HIGH/CRITICAL findings. Upstream Python dependency ranges still permit updates; signed provenance and full dependency locking remain future work.
- AWS registry storage and scans may cost money even without running servers. `terraform apply` and GitHub ECR publishing must be deliberate.
- Terraform local state is ignored and is not team-safe; configure a protected remote state backend before team use.
- v0.2 includes an opt-in managed public AWS App Runner HTTPS runtime, but **does not provision it by default**. Local Compose disables HTTPS redirect only for localhost testing.
- The App Runner setup forces the fictional demo, production DEBUG off, AWS-managed HTTPS, restrictive CSP and secure cookies. It uses `DJANGO_ALLOWED_HOSTS=.awsapprunner.com,localhost,127.0.0.1` for the random App Runner hostname and internal health probes; tighten to explicit hostnames before any real multi-tenant or operational service.
- App Runner uses a separate ECR image-pull role and a runtime role scoped to reading exactly one SSM SecureString parameter. Terraform stores its **ARN**, never the Django secret value.
- Autoscaling is bounded to one 0.25 vCPU/0.5 GB instance, but **billable provisioned memory remains while idle**; review https://aws.amazon.com/apprunner/pricing/ and configure AWS Budget alerts before applying.
- External HTTPS terminates at App Runner. `DJANGO_SECURE_SSL_REDIRECT=false` is deliberate only behind the managed TLS entry point, to avoid redirecting its internal health checks. It must not be reused for directly exposed public HTTP.
- A separate Render Free service has been created and verified with the user’s authorization. Its random Django secret is stored in Render, not in source. No AWS account or AWS resource has been accessed or provisioned.

Report vulnerabilities privately to the repository owner rather than posting secrets in a public issue.

## AWS-free Render deployment controls

- `Dockerfile.render` fetches a reviewed fixed NexusDesk commit and removes checkout metadata before packaging the runtime image. The final user is non-root.
- `render.yaml` defines a separate optional **Free** web service with a randomly generated secret, fictional demo mode, DEBUG disabled, TLS at the Render edge, health checks and CI-gated deployments.
- The demo uses no operational data or writable persistent database. Staff/admin routes are rejected by the pinned app's demo middleware; the hosted service must never run with demo mode disabled.
- Free Render instances sleep when idle, have ephemeral filesystems and share workspace usage limits. A separate deployment must be approved; adding the Blueprint source creates no service by itself.
- This is **Render deployment experience**, not AWS infrastructure administration. The AWS Terraform code remains intentionally optional, non-deployed and AWS-credential-free in CI.

## v0.3 live release boundaries

- The existing Render service is managed directly, with automatic deploys off
  and TCP health checks. The Blueprint's HTTP checks and CI gate are not active.
- CI actions are pinned to full SHAs. Runtime-image scans retain all findings;
  fixable HIGH/CRITICAL issues block CI, while unfixed issues remain in reports.
- The SBOM inventories the CI image, not the live Render image. No signed
  provenance, dependency lock or enforced branch-protection policy is claimed.
- Operational probes allow only standard HTTPS Render/App Runner origins,
  reject redirects, and verify synthetic identity before empty write probes.
  Reports exclude bodies, header values and credentials. Python optimization
  does not disable these security checks.

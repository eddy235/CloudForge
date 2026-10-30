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
- v0.2 includes an opt-in managed public AWS App Runner HTTPS runtime, but **does not provision it by default**. Local Compose disables HTTPS redirect only for localhost testing.
- The App Runner setup forces the fictional demo, production DEBUG off, AWS-managed HTTPS, restrictive CSP and secure cookies. It uses `DJANGO_ALLOWED_HOSTS=.awsapprunner.com,localhost,127.0.0.1` for the random App Runner hostname and internal health probes; tighten to explicit hostnames before any real multi-tenant or operational service.
- App Runner uses a separate ECR image-pull role and a runtime role scoped to reading exactly one SSM SecureString parameter. Terraform stores its **ARN**, never the Django secret value.
- Autoscaling is bounded to one 0.25 vCPU/0.5 GB instance, but **billable provisioned memory remains while idle**; review https://aws.amazon.com/apprunner/pricing/ and configure AWS Budget alerts before applying.
- External HTTPS terminates at App Runner. `DJANGO_SECURE_SSL_REDIRECT=false` is deliberate only behind the managed TLS entry point, to avoid redirecting its internal health checks. It must not be reused for directly exposed public HTTP.
- No cloud service, AWS account or secret has been accessed; a verified real deployment requires the user’s explicit cloud configuration, billing approval and live HTTPS smoke check.

Report vulnerabilities privately to the repository owner rather than posting secrets in a public issue.

## AWS-free Render deployment controls

- `Dockerfile.render` fetches a reviewed fixed NexusDesk commit and removes checkout metadata before packaging the runtime image. The final user is non-root.
- `render.yaml` defines a separate optional **Free** web service with a randomly generated secret, fictional demo mode, DEBUG disabled, TLS at the Render edge, health checks and CI-gated deployments.
- The demo uses no operational data or writable persistent database. Staff/admin routes are rejected by the pinned app's demo middleware; the hosted service must never run with demo mode disabled.
- Free Render instances sleep when idle, have ephemeral filesystems and share workspace usage limits. A separate deployment must be approved; adding the Blueprint source creates no service by itself.
- This is **Render deployment experience**, not AWS infrastructure administration. The AWS Terraform code remains intentionally optional, non-deployed and AWS-credential-free in CI.

# CloudForge v0.1 operator runbook

## First-time local environment

1. Install Git, Python 3.11+, Docker Desktop/Engine and the Docker Compose plugin.
2. `python scripts/fetch_upstream.py` downloads the fixed NexusDesk v1.0 commit.
3. `docker compose up --build -d` builds a new container, binds only to `127.0.0.1:8000`.
4. `python scripts/smoke_local.py` validates the demo and forbidden endpoints.
5. `docker compose logs --tail=100 nexusdesk-demo` reviews errors.
6. `docker compose down` stops local resources.

No AWS subscription is required for these steps.

## Terraform (review before creating resources)

1. Install Terraform, set up your own AWS credentials through standard short-lived methods, and enable budget/cost alerts in AWS.
2. Confirm AWS account and region (`aws sts get-caller-identity`). Never use account-wide admin credentials for routine operations.
3. `cd infra/terraform`, `terraform fmt -check -recursive`, `terraform init -backend=false`, `terraform validate`.
4. If ready, configure a secure remote backend before team collaboration; local tfstate contains sensitive identifiers and must never be committed.
5. Review `terraform plan -out=cloudforge.tfplan` and any ECR pricing that applies in your region.
6. **Only when you approve the costs:** `terraform apply cloudforge.tfplan`.
7. Record `ecr_repository_url`, and if an existing GitHub OIDC provider ARN is provided, the restricted IAM role ARN.

Creating an ECR repository can create AWS charges for stored images and scanning. This project does not run `apply` automatically.

## Enable a manual ECR push

- Ensure a GitHub OIDC provider with URL `https://token.actions.githubusercontent.com` and audience `sts.amazonaws.com` exists **in your AWS account**.
- Supply its ARN to Terraform (`github_oidc_provider_arn`) to provision a narrowly scoped push role.
- Review trust policy's exact repository and main branch.
- Add GitHub repository **Actions variables** `AWS_ROLE_ARN`, `ECR_REPOSITORY_URI`, `AWS_REGION`.
- Run the `Push reviewed image to AWS ECR` GitHub workflow manually from **main**. Never store an AWS access key as a GitHub secret.
- Images use immutable commit-SHA tags and require no change to running infrastructure.

## Troubleshooting

- Cannot fetch upstream: check network access, Git installation, and pinned SHA in `UPSTREAM_VERSION`.
- Docker `COPY` failed: run fetch script first; the upstream directory is intentionally ignored by Git.
- Healthcheck fails: inspect container logs, confirm port 8000 free and that demo mode remains true.
- Unexpected 301 to HTTPS locally: set `DJANGO_SECURE_SSL_REDIRECT=false` **only in local Compose**.
- Terraform provider error: confirm AWS credentials and Terraform version; no cloud resources are created by `validate`.
- IAM OIDC `AccessDenied`: check GitHub repo/branch, provider ARN, `aud` and `sub` conditions; never widen trust to `repo:*`.

## Teardown

- Local: `docker compose down --rmi local` (optional, removes built local image).
- AWS: delete pushed ECR images before destroying the repository, then `terraform destroy` after reviewing resources. Terraform sets `force_delete=false` intentionally to prevent accidental deletion of stored images.

## v0.2 — Optional AWS App Runner Deployment

Read **[AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md)** in full before touching AWS. v0.2 provides an opt-in small managed HTTPS App Runner service behind a private immutable ECR image, requires a pre-created SSM SecureString secret, and does not create AWS runtime resources unless `enable_runtime=true` is explicitly approved. The manual cloud smoke test is `python scripts/smoke_cloud.py https://YOUR_APP_RUNNER_ORIGIN`. Review paid runtime and storage costs, AWS Budget alerts, rollbacks and pause/teardown separately. Do not run `terraform apply` or `terraform destroy` from CI.

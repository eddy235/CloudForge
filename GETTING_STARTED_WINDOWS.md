# CloudForge — Windows Quick Start

This project is independent of SecureScan, NexusDesk, and the portfolio website. It retrieves a fixed version of NexusDesk as its example application; **never publish real tickets or employee accounts**.

## 1. Prerequisites

- Python 3.11 or newer: `python --version`
- Git for Windows: `git --version`
- Docker Desktop (WSL2 enabled): `docker version` and `docker compose version`
- Terraform is needed only when you start AWS infrastructure work.

## 2. Run CloudForge locally in PowerShell

Unzip `CloudForge_v0.1.zip` and open PowerShell inside the extracted folder:

```powershell
python scripts/fetch_upstream.py
python -m unittest discover -s tests -v
docker compose up --build -d
python scripts/smoke_local.py
```

Open `http://127.0.0.1:8000/demo/` in your browser. This is only a fictional, read-only NexusDesk demonstration, containerized for CloudForge.

To stop it:

```powershell
docker compose down
```

## 3. Create its own GitHub repository

Create a public GitHub repository called **CloudForge** under **eddy235**. Add a README when creating the repository to ensure the GitHub integration can access it. Send the URL in chat and I can push the complete CloudForge files and help get CI green. Never upload `upstream/NexusDesk/`, your local `.env`, Terraform state or AWS credentials.

## 4. AWS comes later

Do **not** run `terraform apply` until the Terraform plan, account/region, and any resulting costs have been reviewed. v0.1 can be built and tested entirely locally or in GitHub Actions. AWS ECR storage is potentially billable; running services will be considered separately in v0.2.

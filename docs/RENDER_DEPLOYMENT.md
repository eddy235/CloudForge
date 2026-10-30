# CloudForge — Render deployment

**Live demo:** https://cloudforge-demo.onrender.com/demo/

**Service:** https://dashboard.render.com/web/srv-dbi4erks728c73cajlag

No AWS account is required. CloudForge builds the fixed fictional NexusDesk
source as a non-root Docker image and hosts it as a separate Render service.

## Current service

| Setting | Configured value |
|---|---|
| Repository / branch | `eddy235/CloudForge` / `main` |
| Runtime / Dockerfile / context | Docker / `./Dockerfile.render` / `.` |
| Region / compute plan | Oregon / Free |
| Auto-deploy | **Off** |
| Render health checks | Default **TCP** |
| HTTPS application check | `/health/` checked with the operational script |
| Secret | Random per-service Django secret stored in Render environment |
| Public mode | `NEXUSDESK_DEMO_MODE=true`, `DJANGO_DEBUG=false` |
| TLS | Managed by Render at its edge; HSTS enabled in Django |
| Operational data | No accounts, employee records or writable database |

The initial deployment on 30 October 2026 used commit
`f3b91316b0da9b9e874bf5878815e1cd196672b2`, passed the live HTTPS security smoke
checks, and was separate from the existing NexusDesk, SecureScan and portfolio
services. Use the service's deploy record for the current deployed revision.

## Direct service versus Blueprint

The existing service was created directly through the Render connection. It is
**not linked to a Blueprint**. The optional root `render.yaml` describes a Free
service with an HTTP `/health/` check and `checksPass` automatic deployment.
Those two fields could not be set through the available connection. The direct
service therefore retains TCP checks and manual deploys.

Do not assume an edit to `render.yaml` changes the live service, and do not
create a second service to resolve this difference. If you later use the
Dashboard, set `/health/` under Health Checks and enable **After CI Checks Pass**
only after confirming the Git provider connection and all required checks.
Any Blueprint import must explicitly associate the existing service first.

## Build and verify

`Dockerfile.render` fetches the exact public NexusDesk commit in
`UPSTREAM_VERSION`, discards checkout metadata and installs the app into an
unprivileged runtime image. Both build stages pin the official Python image to
a reviewed digest. The upstream dependency ranges remain a documented limit.

```bash
docker build -f Dockerfile.render -t cloudforge-render:test .
python scripts/smoke_cloud.py https://cloudforge-demo.onrender.com \
  --report reports/render-verification.json
```

The checker verifies demo identity, static assets, CSP, anti-framing, nosniff,
blocked operational routes and rejected empty POST requests. Only readiness is
retried; redirects and security failures fail immediately. A JSON report and
GitHub job summary retain structured results without sensitive response data.

## Release and recovery

Follow [OPERATIONS.md](OPERATIONS.md) for CI review, image-scan evidence,
manual deployment, live checks, incident diagnosis and rollback instructions.
A passing probe is evidence about the currently deployed app, not proof that a
new commit was deployed. Check Render's exact deploy commit and terminal status.

## References

- [Render Docker deployment](https://render.com/docs/docker)
- [Render deploy lifecycle and CI integration](https://render.com/docs/deploys)
- [Render health checks](https://render.com/docs/health-checks)
- [Free service limits](https://render.com/docs/free)

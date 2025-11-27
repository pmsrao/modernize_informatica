# Deployment & Enterprise Integrations

## Deployment

The platform is designed to be deployed with:

- **Docker images**:
  - Backend (FastAPI + Uvicorn)
  - Frontend (built React assets served via Node or a static server)
- **Docker Compose**:
  - Ties together API + UI
  - Handles basic networking
- **CI/CD** (e.g., GitHub Actions):
  - Run tests on push
  - Build images on tag
  - Publish to a registry (if configured)

Kubernetes / Helm–based deployments can be added on top of this, but are not strictly required.

---

## Enterprise Extensions

To fit into enterprise platforms, the accelerator can integrate with:

- **Storage**:
  - S3
  - ADLS
  - GCS
- **Catalogs**:
  - Glue
  - Purview
  - Dataplex
- **Version Store**:
  - JSON snapshots of:
    - canonical mappings
    - generated code
    - AI insight outputs
- **Notifications**:
  - Slack/Teams webhooks for:
    - migration progress
    - risk alerts
    - job completion reports

---

## Deployment Files

- **`deployment/docker-compose.yaml`**: Complete stack deployment
- **`deployment/backend/Dockerfile`**: Backend container image
- **`deployment/frontend/Dockerfile`**: Frontend container image

---

**Next**: Learn about [Extensibility](extensibility.md) to customize the accelerator.


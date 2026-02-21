# Agentic Claims Processing Demo - Helm Chart

Helm chart for deploying the complete AI-powered insurance claims processing system on OpenShift.

## Prerequisites

### OpenShift Platform

- **OpenShift 4.19+** with GPU nodes
- **OpenShift AI 3.0+** operator installed
- **Helm 3.8+** CLI
- **kubectl or oc CLI** configured

### AI Models (Deployed separately via OpenShift AI)

This Helm chart requires AI models to be **already deployed** before installation.

Required models:
- **Llama 3.3 70B INT8** (vLLM runtime)
- **Gemma 300m** (Hugging Face runtime for embeddings)

> **📚 See the main repository README.md for complete model deployment instructions:**
> - Step 3: Deploy vLLM Inference Model (Llama 3.3 70B)
> - Gemma 300m embedding model deployment

### Container Images

- **Container registry** (e.g., Quay.io) for custom application images
- Images must be **built and pushed before** Helm installation (see Quick Start below)

## Quick Start

### 1. Build and Push Container Images

**IMPORTANT:** You must build and push all container images to your registry **before** installing the Helm chart.

```bash
# Login to your Quay registry
podman login quay.io

# Build and push Backend API
cd /path/to/multi-agents
podman build -t quay.io/your-org/backend:latest -f backend/Dockerfile .
podman push quay.io/your-org/backend:latest

# Build and push Frontend
cd frontend
podman build -t quay.io/your-org/frontend:latest .
podman push quay.io/your-org/frontend:latest

# Build and push OCR Server
cd ../backend/mcp_servers/ocr_server
podman build -t quay.io/your-org/ocr-server:latest .
podman push quay.io/your-org/ocr-server:latest

# Build and push RAG Server
cd ../rag_server
podman build -t quay.io/your-org/rag-server:latest .
podman push quay.io/your-org/rag-server:latest

# Build and push Postgres
cd ../../database
podman build -t quay.io/your-org/postgres:latest -f Dockerfile .
podman push quay.io/your-org/postgres:latest

# Optional: hfcli image
cd ../hfcli
podman build -t quay.io/your-org/hfcli:latest -f Dockerfile .
podman push quay.io/your-org/hfcli:latest
```

**Note:** Helm does **NOT** build images. It only deploys existing images from your registry.

### 2. Configure Values

Edit `values.yaml` and update:

```yaml
global:
  # Replace with your OpenShift cluster domain
  clusterDomain: "apps.cluster-xxx.opentlc.com"

  # Replace with your image registry (same as used in podman push)
  imageRegistry: "quay.io/your-org"

# Update PostgreSQL password
secrets:
  postgresPassword: "your-password"
```

### 3. Install the Chart

```bash
# Create namespace
oc create namespace multi-agents

# Install chart
helm install multi-agents ./helm/multi-agents \
  --namespace multi-agents \
  --set global.clusterDomain=apps.cluster-xxx.opentlc.com \
  --set global.imageRegistry=quay.io/your-org
```

### 4. Wait for Deployment

```bash
# Wait for all pods to be ready
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/instance=multi-agents \
  -n multi-agents \
  --timeout=300s
```

### 5. Create Demo Claims

Database already includes a few claims. Could provision more:

```bash
cd scripts
./reset_and_create_claims.sh
```

### 6. Access the Application

```bash
# Get frontend URL
echo "https://frontend-multi-agents.apps.cluster-xxx.opentlc.com"
```

## Configuration

### Global Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.clusterDomain` | OpenShift cluster domain | `apps.your-cluster.example.com` |
| `global.namespace` | Namespace for all resources | `multi-agents` |
| `global.imageRegistry` | Container image registry | `quay.io/your-org` |
| `global.imagePullPolicy` | Image pull policy | `IfNotPresent` |

### PostgreSQL

| Parameter | Description | Default |
|-----------|-------------|---------|
| `postgresql.enabled` | Enable PostgreSQL deployment | `true` |
| `postgresql.replicas` | Number of replicas | `1` |
| `postgresql.persistence.size` | PVC size | `10Gi` |
| `postgresql.resources.requests.cpu` | CPU request | `500m` |
| `postgresql.resources.requests.memory` | Memory request | `1Gi` |

### LlamaStack

| Parameter | Description | Default |
|-----------|-------------|---------|
| `llamastack.enabled` | Enable LlamaStack deployment | `true` |

### MCP Servers

| Parameter | Description | Default |
|-----------|-------------|---------|
| `mcp.ocr.enabled` | Enable OCR server | `true` |
| `mcp.ocr.env.OCR_LANGUAGES` | OCR languages | `en,fr` |
| `mcp.rag.enabled` | Enable RAG server | `true` |

### Backend API

| Parameter | Description | Default |
|-----------|-------------|---------|
| `backend.enabled` | Enable backend deployment | `true` |
| `backend.replicas` | Number of replicas | `2` |
| `backend.resources.requests.cpu` | CPU request | `500m` |
| `backend.resources.requests.memory` | Memory request | `512Mi` |

### Frontend

| Parameter | Description | Default |
|-----------|-------------|---------|
| `frontend.enabled` | Enable frontend deployment | `true` |
| `frontend.replicas` | Number of replicas | `2` |
| `frontend.resources.requests.cpu` | CPU request | `200m` |
| `frontend.resources.requests.memory` | Memory request | `256Mi` |

## Advanced Usage

### Install with Custom Values

```bash
# Create custom values file
cat > custom-values.yaml <<EOF
global:
  clusterDomain: apps.mycluster.com
  imageRegistry: quay.io/myorg

backend:
  replicas: 3
  resources:
    requests:
      cpu: 1000m
      memory: 1Gi

postgresql:
  persistence:
    size: 20Gi
EOF

# Install with custom values
helm install multi-agents ./helm/multi-agents \
  -f custom-values.yaml \
  -n multi-agents
```

### Upgrade Deployment

```bash
# Update values.yaml or use --set
helm upgrade multi-agents ./helm/multi-agents \
  --namespace multi-agents \
  --set backend.replicas=3
```

### Rollback

```bash
# List releases
helm history multi-agents -n multi-agents

# Rollback to previous version
helm rollback multi-agents -n multi-agents

# Rollback to specific revision
helm rollback multi-agents 1 -n multi-agents
```

### Uninstall

```bash
# Uninstall release (keeps PVCs)
helm uninstall multi-agents -n multi-agents

# Delete PVCs manually if needed
oc delete pvc postgresql-data -n multi-agents

# Delete namespace
oc delete namespace multi-agents
```

## Multi-Environment Deployment

### Development Environment

```yaml
# values-dev.yaml
global:
  clusterDomain: apps.dev-cluster.com
  namespace: multi-agents-dev

backend:
  replicas: 1
  env:
    ENVIRONMENT: "development"
    DEBUG: "true"

postgresql:
  persistence:
    size: 5Gi
```

```bash
helm install multi-agents-dev ./helm/multi-agents \
  -f values-dev.yaml \
  -n multi-agents-dev \
  --create-namespace
```

### Production Environment

```yaml
# values-prod.yaml
global:
  clusterDomain: apps.prod-cluster.com
  namespace: multi-agents-prod

backend:
  replicas: 3
  env:
    ENVIRONMENT: "production"
    DEBUG: "false"
  resources:
    requests:
      cpu: 1000m
      memory: 2Gi

postgresql:
  persistence:
    size: 50Gi
  resources:
    requests:
      cpu: 2000m
      memory: 8Gi
```

```bash
helm install multi-agents-prod ./helm/multi-agents \
  -f values-prod.yaml \
  -n multi-agents-prod \
  --create-namespace
```

## Troubleshooting

### Check Deployment Status

```bash
# List all resources
helm list -n multi-agents

# Check pods
oc get pods -n multi-agents

# Check services
oc get svc -n multi-agents

# Check routes
oc get routes -n multi-agents
```

### View Logs

```bash
# Backend logs
oc logs -l app=backend -n multi-agents --tail=100 -f

# LlamaStack logs
oc logs -l app=llama-stack -n multi-agents --tail=100 -f

# MCP Server logs
oc logs -l app=ocr-server -n multi-agents --tail=100 -f
oc logs -l app=rag-server -n multi-agents --tail=100 -f
```

### Common Issues

**Issue: Pods stuck in Pending**
```bash
# Check events
oc describe pod <pod-name> -n multi-agents

# Check PVC status
oc get pvc -n multi-agents
```

**Issue: Database connection failed**
```bash
# Check PostgreSQL pod
oc logs postgresql-0 -n multi-agents

# Test database connection
oc exec postgresql-0 -n multi-agents -- \
  psql -U claims_user -d claims_db -c "SELECT 1"
```

**Issue: Frontend can't reach backend**
```bash
# Check backend route
oc get route backend -n multi-agents

# Test backend health
curl https://backend-multi-agents.apps.cluster-xxx.opentlc.com/health/live
```

## Architecture

```
Frontend (React)
    → Backend API (FastAPI)
       → LlamaStack (OpenShift AI)
          ├─→ Llama 3.3 70B (reasoning)
          └─→ MCP Tools (FastMCP/SSE)
              • OCR Server (EasyOCR)
              • RAG Server (pgvector)
                 ↓
              PostgreSQL + pgvector
```

## Support

- **GitHub**: https://github.com/your-org/multi-agents
- **Issues**: https://github.com/your-org/multi-agents/issues
- **Documentation**: See main README.md

## License

This project is licensed under the Apache License 2.0.

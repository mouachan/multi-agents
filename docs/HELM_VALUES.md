# Helm Values Reference

Complete reference for Helm chart configuration values.

## Global Configuration

```yaml
global:
  namespace: claims-demo           # Target namespace
  clusterDomain: apps.cluster.com  # OpenShift cluster domain
```

## Application Services

### Backend

```yaml
backend:
  enabled: true
  image:
    repository: quay.io/your-org/backend
    tag: v2.0.0
    pullPolicy: IfNotPresent
  replicas: 1

  env:
    LOG_LEVEL: INFO
    ENVIRONMENT: production

  resources:
    requests:
      memory: "2Gi"
      cpu: "1"
    limits:
      memory: "4Gi"
      cpu: "2"

  route:
    enabled: true
    host: ""  # Auto-generated if empty
```

### Frontend

```yaml
frontend:
  enabled: true
  image:
    repository: quay.io/your-org/frontend
    tag: v2.0.0
    pullPolicy: IfNotPresent
  replicas: 1

  resources:
    requests:
      memory: "512Mi"
      cpu: "250m"
    limits:
      memory: "1Gi"
      cpu: "500m"

  route:
    enabled: true
    host: ""
```

## MCP Tool Servers

### OCR Server

```yaml
ocr:
  enabled: true
  image:
    repository: quay.io/your-org/ocr-server
    tag: v2.0.0

  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "1"
```

### RAG Server

```yaml
rag:
  enabled: true
  image:
    repository: quay.io/your-org/rag-server
    tag: v2.0.0

  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "1"
```

## Data Layer

### PostgreSQL

```yaml
postgresql:
  enabled: true

  auth:
    username: claims_user
    database: claims_db
    existingSecret: postgresql-secret  # Auto-created by Helm

  persistence:
    enabled: true
    size: 10Gi
    storageClass: ""  # Use default or specify (e.g., "gp3-csi")

  resources:
    requests:
      memory: "4Gi"
      cpu: "2"
    limits:
      memory: "8Gi"
      cpu: "4"

  primary:
    podAnnotations: {}
    podLabels: {}
```

## AI Models

### Inference (Llama 3.3 70B)

```yaml
inference:
  enabled: true

  model:
    name: llama-3-3-70b-instruct-quantized-w8a8
    source: huggingface

  # IMPORTANT: Update with your cluster domain
  endpoint: "https://llama-3-3-70b-llama-3-3-70b.apps.YOUR-CLUSTER-DOMAIN.com/v1"

  resources:
    requests:
      nvidia.com/gpu: 4  # 4x GPUs for tensor parallel
    limits:
      nvidia.com/gpu: 4

  # vLLM configuration
  vllm:
    tensorParallelSize: 4
    maxModelLen: 20000  # 20K context
    quantization: "int8"
    kvCacheDataType: "fp8"
```

### Embedding (Gemma 300M)

```yaml
embedding:
  enabled: true

  model:
    name: embeddinggemma-300m
    source: huggingface

  endpoint: "https://embeddinggemma-300m-embeddinggemma-300m.apps.YOUR-CLUSTER-DOMAIN.com/v1"

  resources:
    requests:
      nvidia.com/gpu: 1  # Optional GPU
    limits:
      nvidia.com/gpu: 1

  dimensions: 768  # Embedding vector size
```

## LlamaStack

```yaml
llamastack:
  enabled: true
  version: "0.3.5"
  replicas: 1

  config:
    default_model: "vllm-inference/llama-3-3-70b-instruct-quantized-w8a8"
    embedding_model: "vllm-embedding/embeddinggemma-300m"
    max_tokens: 4096
    timeout: 300
    max_infer_iters: 10  # ReAct loop iterations

  resources:
    requests:
      memory: "4Gi"
      cpu: "2"
    limits:
      memory: "8Gi"
      cpu: "4"
```

## Data Science Pipelines

### DSPA Configuration

```yaml
dataSciencePipelines:
  enabled: true
  name: dspa  # Short name to avoid 63-char service name limit

  database:
    mariaDB:
      deploy: true
      pvcSize: 10Gi
      username: mlpipeline
      # Password auto-generated in secret

  objectStorage:
    useInternalMinio: true
    scheme: http  # CRITICAL: must be http for internal MinIO
    bucket: pipelines
    region: us-east-1
```

**Critical Settings**:
- `objectStorage.scheme: http` - Must be `http` (not `https`) for internal MinIO
- `name` - Keep short (<= 10 chars) to avoid Kubernetes service name length issues

### MinIO

```yaml
minio:
  enabled: true
  mode: standalone

  # CHANGE THESE IN YOUR VALUES FILE
  rootUser: minioadmin
  rootPassword: "CHANGE_ME_STRONG_PASSWORD"

  persistence:
    enabled: true
    size: 20Gi
    storageClass: ""

  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "1"

  buckets:
    - name: pipelines
      policy: none
      purge: false
```

## Guardrails

### TrustyAI Guardrails Orchestrator

```yaml
guardrails:
  enabled: true

  orchestrator:
    image: registry.redhat.io/rhoai/odh-fms-guardrails-orchestrator-rhel9:latest
    replicas: 1

    resources:
      requests:
        memory: "1Gi"
        cpu: "500m"
      limits:
        memory: "2Gi"
        cpu: "1"

  detector:
    model: meta-llama/Llama-Guard-3-1B-INT4
    enabled: false  # Future enhancement

  config:
    pii_detection: true
    shield_id: "pii_detector"
```

## HuggingFace CLI Helper

```yaml
hfcli:
  enabled: true

  # REQUIRED: Get token from https://huggingface.co/settings/tokens
  token: "hf_YOUR_TOKEN_HERE"

  image:
    repository: quay.io/your-org/hfcli
    tag: latest
```

## GitOps (ArgoCD)

```yaml
argocd:
  syncWaves:
    enabled: true  # Adds sync-wave annotations for ordered deployment
```

**Sync Wave Order**:
- `-100`: Namespaces
- `-90`: Secrets, RBAC, ServiceAccounts
- `0`: Applications, ConfigMaps, Services
- `5`: Database initialization jobs
- `10`: LlamaStack distribution

## Storage Configuration

### Storage Classes by Cloud Provider

**AWS**:
```yaml
postgresql:
  persistence:
    storageClass: "gp3-csi"

minio:
  persistence:
    storageClass: "gp3-csi"
```

**GCP**:
```yaml
postgresql:
  persistence:
    storageClass: "standard"

minio:
  persistence:
    storageClass: "standard"
```

**Azure**:
```yaml
postgresql:
  persistence:
    storageClass: "managed-premium"

minio:
  persistence:
    storageClass: "managed-premium"
```

**Default (use cluster default)**:
```yaml
postgresql:
  persistence:
    storageClass: ""

minio:
  persistence:
    storageClass: ""
```

## Complete Example

See `helm/agentic-claims-demo/values-sample.yaml` for a complete working example.

**Minimal values.yaml for deployment**:

```yaml
# Update these values for your environment
global:
  clusterDomain: apps.your-cluster.com

backend:
  image:
    repository: quay.io/your-org/backend
    tag: v2.0.0

frontend:
  image:
    repository: quay.io/your-org/frontend
    tag: v2.0.0

inference:
  endpoint: "https://llama-3-3-70b-llama-3-3-70b.apps.your-cluster.com/v1"

embedding:
  endpoint: "https://embeddinggemma-300m-embeddinggemma-300m.apps.your-cluster.com/v1"

hfcli:
  token: "hf_xxxxxxxxxxxxxxxxxxxx"

minio:
  rootPassword: "YourStrongPassword123!"

dataSciencePipelines:
  enabled: true
  objectStorage:
    scheme: http  # IMPORTANT!

guardrails:
  enabled: true
```

## Validation

Validate your values file before deploying:

```bash
helm template agentic-claims-demo ./helm/agentic-claims-demo \
  -f values-mydeployment.yaml \
  --debug \
  --dry-run
```

Check for common issues:
- Cluster domain is correct
- Storage classes exist in your cluster
- Image repositories are accessible
- HuggingFace token is valid

# Historical Claims Initialization Pipeline

Kubeflow Pipeline for RHOAI Data Science Pipelines to initialize historical claims data for RAG similarity search.

## Overview

This pipeline processes historical claims data through three stages:

1. **Generate PDFs**: Creates realistic PDF documents from seed data OCR texts using ReportLab
2. **Parse PDFs**: Extracts text using IBM Docling (advanced document parsing)
3. **Generate Embeddings**: Creates 768D vector embeddings via LlamaStack and stores in PostgreSQL with pgvector

## Prerequisites

- Red Hat OpenShift AI 3.x with Data Science Pipelines enabled
- PostgreSQL database with claims data (seed-enriched.sql loaded)
- LlamaStack service running with embedding model (gemma-300m)
- kfp SDK >= 2.14.3 (for RHOAI 3.x compatibility)

## Usage

### Option 1: Upload Python file directly to RHOAI

1. Navigate to RHOAI Data Science Pipelines dashboard
2. Click "Import pipeline"
3. Upload `historical_claims_init.py`
4. RHOAI will automatically compile the pipeline

### Option 2: Compile locally and upload YAML

If you want to compile locally first:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Compile pipeline
python3 historical_claims_init.py

# This generates: historical_claims_init_pipeline.yaml
```

Then upload the YAML file to RHOAI Data Science Pipelines dashboard.

## Pipeline Parameters

Configure these parameters when creating a pipeline run in RHOAI:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `postgres_host` | `postgresql.claims-demo.svc.cluster.local` | PostgreSQL hostname |
| `postgres_port` | `5432` | PostgreSQL port |
| `postgres_db` | `claims_db` | Database name |
| `postgres_user` | `claims_user` | Database user |
| `postgres_password` | `ClaimsDemo2025!` | Database password |
| `llamastack_endpoint` | `http://llamastack-test-v035.claims-demo.svc.cluster.local:8321` | LlamaStack API endpoint |
| `embedding_model` | `gemma-300m` | Embedding model name |
| `batch_size` | `5` | Documents per batch |

**Security Note**: Use Kubernetes Secrets for sensitive parameters like `postgres_password` in production.

## Pipeline Components

### 1. Generate Realistic PDFs
- **Image**: `registry.access.redhat.com/ubi9/python-312:latest`
- **Dependencies**: reportlab==4.2.5, sqlalchemy==2.0.36, psycopg2-binary==2.9.10
- **Resources**: 1 CPU, 2Gi memory
- **Output**: PDFs stored in /tmp/pdfs

### 2. Docling Parse PDFs
- **Image**: `registry.access.redhat.com/ubi9/python-312:latest`
- **Dependencies**: docling==2.18.0, sqlalchemy==2.0.36, psycopg2-binary==2.9.10
- **Resources**: 2 CPU, 8Gi memory
- **Updates**: claim_documents.raw_ocr_text, ocr_confidence, ocr_processed_at

### 3. Generate Embeddings
- **Image**: `registry.access.redhat.com/ubi9/python-312:latest`
- **Dependencies**: httpx==0.27.2, sqlalchemy==2.0.36, psycopg2-binary==2.9.10, pgvector==0.3.6
- **Resources**: 1 CPU, 2Gi memory
- **Updates**: claim_documents.embedding (768D vectors)
- **Returns**: Metrics dict for MLFlow tracking

## Expected Results

For the enriched seed data:
- 60 historical claims with OCR text
- 60 generated PDFs
- 60 parsed documents with Docling
- 60 embeddings generated (768 dimensions each)

## Troubleshooting

### Pipeline fails at embedding generation

Check LlamaStack service availability:
```bash
oc get pods -n claims-demo | grep llamastack
oc logs -n claims-demo <llamastack-pod-name>
```

### Database connection errors

Verify PostgreSQL secret and service:
```bash
oc get secret postgresql-secret -n claims-demo
oc get svc postgresql -n claims-demo
```

### Memory issues

Increase resource limits in component decorators:
- Docling parsing is memory-intensive (current: 8Gi)
- Adjust batch_size parameter to reduce memory usage

## Architecture

This batch pipeline complements the real-time claim processing workflow:

- **Batch (this pipeline)**: One-time initialization of historical data for RAG
- **Real-time (MCP Servers)**: Production claim processing with OCR + RAG + LLM

## RHOAI Version Compatibility

- RHOAI 3.0+: kfp >= 2.14.3
- RHOAI 3.2: Tested with Kubeflow Pipelines 2.4.x
- Data Science Pipelines 2.0 (not the legacy kfp-tekton)

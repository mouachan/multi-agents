# Development Guide

Guide for local development, testing, and contributing to the agentic claims demo.

## Local Development Setup

### Prerequisites

- Python 3.12+
- Node.js 18+ and npm
- Docker or Podman
- PostgreSQL 15+ (or Docker image)

### Backend Development

#### 1. Setup Python Environment

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-test.txt
```

#### 2. Configure Environment

Create `.env` file in `backend/` directory:

```bash
# Database
DATABASE_URL=postgresql://claims_user:claims_pass@localhost:5432/claims_db

# LlamaStack (point to dev instance or OpenShift)
LLAMASTACK_ENDPOINT=http://localhost:8321
LLAMASTACK_DEFAULT_MODEL=vllm-inference/llama-3-3-70b
LLAMASTACK_EMBEDDING_MODEL=vllm-embedding/embeddinggemma-300m

# MCP Servers (point to local or OpenShift)
OCR_SERVER_URL=http://localhost:8081
RAG_SERVER_URL=http://localhost:8082

# Application
DEBUG=true
LOG_LEVEL=DEBUG
ENVIRONMENT=development

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

#### 3. Run Local Database

Using Docker:

```bash
docker run -d \
  --name postgres-claims-dev \
  -e POSTGRES_USER=claims_user \
  -e POSTGRES_PASSWORD=claims_pass \
  -e POSTGRES_DB=claims_db \
  -p 5432:5432 \
  pgvector/pgvector:pg15

# Initialize database
psql -h localhost -U claims_user -d claims_db -f database/init.sql
psql -h localhost -U claims_user -d claims_db -f database/seed_data/001_sample_data.sql
```

#### 4. Run Backend Server

```bash
cd backend
source venv/bin/activate

# Run with auto-reload
uvicorn app.main:app --reload --port 8000

# Or with specific host
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access API: http://localhost:8000

API Docs: http://localhost:8000/docs

#### 5. Run MCP Servers Locally

**OCR Server**:
```bash
cd backend/mcp_servers/ocr_server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py  # Runs on port 8081
```

**RAG Server**:
```bash
cd backend/mcp_servers/rag_server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py  # Runs on port 8082
```

### Frontend Development

#### 1. Install Dependencies

```bash
cd frontend
npm install
```

#### 2. Configure Environment

Create `.env` file in `frontend/` directory:

```bash
REACT_APP_BACKEND_URL=http://localhost:8000
REACT_APP_ENV=development
```

#### 3. Run Development Server

```bash
cd frontend
npm start
```

Access UI: http://localhost:3000

#### 4. Build for Production

```bash
cd frontend
npm run build

# Test production build locally
npx serve -s build -p 3000
```

## Testing

### Backend Tests

#### Run All Tests

```bash
cd backend
pytest tests/ -v
```

#### Run with Coverage

```bash
pytest --cov=app --cov-report=html --cov-report=term tests/
```

View coverage report: `backend/htmlcov/index.html`

#### Run Specific Test Files

```bash
# Unit tests only
pytest tests/test_services/ -v

# Integration tests only
pytest tests/test_integration/ -v

# Specific test file
pytest tests/test_services/test_claim_service.py -v

# Specific test function
pytest tests/test_services/test_claim_service.py::test_process_claim_with_agent -v
```

#### Run with Markers

```bash
# Run only fast tests
pytest -m "not slow" -v

# Run only integration tests
pytest -m integration -v
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- ClaimList.test.tsx

# Update snapshots
npm test -- -u
```

## Building Container Images

### Build All Images

Use the provided script:

```bash
export REGISTRY=quay.io/your-org
export TAG=dev-$(date +%Y%m%d)

./scripts/build-all-images.sh $REGISTRY $TAG
```

### Build Individual Images

**Backend**:
```bash
# IMPORTANT: Build from parent directory
cd /path/to/agentic-claim-demo
podman build --platform linux/amd64 \
  -t quay.io/your-org/backend:dev \
  -f backend/Dockerfile .
```

**Frontend**:
```bash
# Must build sources first!
cd frontend
npm run build

podman build --platform linux/amd64 \
  -t quay.io/your-org/frontend:dev \
  -f Dockerfile.production .
```

**MCP Servers**:
```bash
# OCR Server
podman build --platform linux/amd64 \
  -t quay.io/your-org/ocr-server:dev \
  backend/mcp_servers/ocr_server/

# RAG Server
podman build --platform linux/amd64 \
  -t quay.io/your-org/rag-server:dev \
  backend/mcp_servers/rag_server/
```

**Note**: PostgreSQL uses the official `pgvector/pgvector:pg15` image, no custom build needed.

### Push Images

```bash
podman push quay.io/your-org/backend:dev
podman push quay.io/your-org/frontend:dev
podman push quay.io/your-org/ocr-server:dev
podman push quay.io/your-org/rag-server:dev
```

## Database Management

### Schema Changes

1. **Edit schema** in `database/init.sql`

2. **Sync to Helm** (IMPORTANT):
```bash
cp database/init.sql helm/agentic-claims-demo/files/cm.init-postgres/
```

3. **Apply locally** for testing:
```bash
psql -h localhost -U claims_user -d claims_db -f database/init.sql
```

### Seed Data Changes

1. **Edit seed data** in `database/seed_data/001_sample_data.sql`

2. **Sync to Helm** (IMPORTANT):
```bash
cp database/seed_data/001_sample_data.sql \
   helm/agentic-claims-demo/files/cm.init-postgres/seed.sql
```

3. **Reload seed data**:
```bash
psql -h localhost -U claims_user -d claims_db \
  -c "TRUNCATE claims, claim_documents, claim_decisions, users, user_contracts, knowledge_base CASCADE;"

psql -h localhost -U claims_user -d claims_db \
  -f database/seed_data/001_sample_data.sql
```

## Manual Deployment (OpenShift)

For manual deployment without Helm:

### 1. Apply Manifests by Type

```bash
# Secrets and ConfigMaps
oc apply -f openshift/secrets/
oc apply -f openshift/configmaps/

# Storage
oc apply -f openshift/pvcs/

# Deployments
oc apply -f openshift/deployments/

# Services
oc apply -f openshift/services/

# Routes
oc apply -f openshift/routes/

# Jobs (database init, etc.)
oc apply -f openshift/jobs/
```

### 2. Update Generated Manifests

After Helm chart changes, regenerate OpenShift manifests:

```bash
cd /path/to/agentic-claim-demo

# Generate from Helm
helm template agentic-claims-demo ./helm/agentic-claims-demo \
  --namespace claims-demo \
  > /tmp/all-manifests.yaml

# Split into organized directories
python3 scripts/split-manifests.py /tmp/all-manifests.yaml openshift/
```

## Debugging

### Backend Debugging

#### Enable Debug Logging

Set in `.env`:
```bash
LOG_LEVEL=DEBUG
DEBUG=true
```

#### Use Python Debugger

Add breakpoint in code:
```python
import pdb; pdb.set_trace()
```

Run server:
```bash
uvicorn app.main:app --reload
```

#### Check Logs

```bash
# OpenShift
oc logs -f deployment/backend -c backend -n claims-demo

# Local
tail -f logs/app.log
```

### Frontend Debugging

#### React DevTools

Install browser extension:
- Chrome: React Developer Tools
- Firefox: React Developer Tools

#### Console Logging

Enable in browser console:
```javascript
localStorage.setItem('debug', '*')
```

#### Network Debugging

Check API calls in browser DevTools Network tab.

### Database Debugging

#### Connect to Database

Local:
```bash
psql -h localhost -U claims_user -d claims_db
```

OpenShift:
```bash
oc exec -it statefulset/postgresql -n claims-demo -- \
  psql -U claims_user -d claims_db
```

#### Useful Queries

```sql
-- Check claim status
SELECT id, claim_number, status, processed_at
FROM claims
ORDER BY submitted_at DESC
LIMIT 10;

-- Check embeddings
SELECT COUNT(*) FROM claim_documents WHERE embedding IS NOT NULL;
SELECT COUNT(*) FROM knowledge_base WHERE embedding IS NOT NULL;

-- Check processing logs
SELECT * FROM processing_logs
WHERE claim_id = '...'
ORDER BY started_at;

-- Check PII detections
SELECT * FROM guardrails_detections
ORDER BY detected_at DESC
LIMIT 10;
```

## Code Style

### Python

Follow PEP 8. Use Black for formatting:

```bash
cd backend
black app/ tests/
isort app/ tests/
flake8 app/ tests/
```

### TypeScript/React

Use ESLint and Prettier:

```bash
cd frontend
npm run lint
npm run format
```

## Useful Scripts

### Backend

```bash
# Generate embeddings for all claims
python backend/scripts/generate_all_embeddings.py

# Parse PDFs with Docling
python backend/scripts/docling_parse_pdfs.py

# Generate realistic claim PDFs
python backend/scripts/generate_realistic_pdfs.py

# Show ReAct trace for a claim
./backend/scripts/show_react_trace.sh CLM-2024-0001
```

### Helm

```bash
# Validate Helm chart
helm lint helm/agentic-claims-demo/

# Render templates
helm template agentic-claims-demo ./helm/agentic-claims-demo \
  -f values-dev.yaml

# Show diff
helm diff upgrade agentic-claims-demo ./helm/agentic-claims-demo \
  -f values-dev.yaml -n claims-demo
```

## Performance Profiling

### Backend

Use py-spy for profiling:

```bash
pip install py-spy

# Profile running process
py-spy record -o profile.svg --pid <PID>

# Profile specific endpoint
py-spy record -o profile.svg -- python -m uvicorn app.main:app
```

### Frontend

Use React Profiler:

```javascript
import { Profiler } from 'react';

<Profiler id="ClaimList" onRender={callback}>
  <ClaimList />
</Profiler>
```

## Troubleshooting Development Issues

### Port Already in Use

```bash
# Find process
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Database Connection Failed

Check PostgreSQL is running:
```bash
docker ps | grep postgres
# Or
pg_isready -h localhost -p 5432
```

### MCP Server Not Responding

Check server logs:
```bash
cd backend/mcp_servers/ocr_server
tail -f server.log
```

Test health endpoint:
```bash
curl http://localhost:8081/health/ready
```

### Frontend Won't Connect to Backend

Check CORS settings in `backend/app/core/config.py`:

```python
cors_origins: List[str] = ["http://localhost:3000"]
```

Restart backend after changes.

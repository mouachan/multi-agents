#!/bin/bash
set -e

echo "=========================================="
echo "Deploying Agentic Claims Demo to OpenShift"
echo "=========================================="

PROJECT="claims-demo"

# Check if connected to OpenShift
if ! oc whoami &>/dev/null; then
    echo "Error: Not logged in to OpenShift"
    exit 1
fi

# Switch to project
echo "Using project: $PROJECT"
oc project $PROJECT || oc new-project $PROJECT

echo ""
echo "=========================================="
echo "Step 1: Deploy PostgreSQL + pgvector"
echo "=========================================="

echo "Creating PVC for PostgreSQL..."
oc apply -f openshift/pvcs/postgresql-pvc.yaml

echo "Deploying PostgreSQL StatefulSet..."
oc apply -f openshift/deployments/postgresql-statefulset.yaml

echo "Creating PostgreSQL Service..."
oc apply -f openshift/services/postgresql-service.yaml

echo "Waiting for PostgreSQL to be ready..."
oc wait --for=condition=ready pod -l app=postgresql --timeout=300s

echo ""
echo "=========================================="
echo "Step 2: Deploy MCP Servers (from Quay.io)"
echo "=========================================="

echo "Deploying OCR MCP Server..."
oc apply -f openshift/deployments/ocr-server-deployment.yaml
oc apply -f openshift/services/ocr-server-service.yaml

echo "Deploying RAG MCP Server..."
oc apply -f openshift/deployments/rag-server-deployment.yaml
oc apply -f openshift/services/rag-server-service.yaml

echo "Waiting for MCP servers to be ready..."
oc wait --for=condition=ready pod -l app=ocr-server --timeout=300s || true
oc wait --for=condition=ready pod -l app=rag-server --timeout=300s || true

echo ""
echo "=========================================="
echo "Step 3: Deploy LlamaStack Distribution"
echo "=========================================="

echo "Creating LlamaStack ConfigMap with run.yaml..."
oc create configmap llamastack-config \
    --from-file=run.yaml=openshift/llamastack/working-run.yaml \
    --dry-run=client -o yaml | oc apply -f -

echo "Deploying LlamaStack Distribution..."
oc apply -f openshift/crds/llamastack-distribution.yaml

echo "Waiting for LlamaStack to be ready..."
sleep 10
oc wait --for=condition=ready pod -l app.kubernetes.io/name=llamastack --timeout=300s || true

echo ""
echo "=========================================="
echo "Step 4: Build and Deploy Backend API"
echo "=========================================="

echo "Creating Backend ImageStream..."
oc apply -f openshift/imagestreams/backend-is.yaml

if ! oc get bc backend &>/dev/null; then
    echo "Creating BuildConfig for backend..."
    oc new-build --name=backend \
        --binary=true \
        --strategy=docker \
        --to=backend:latest
fi

echo "Starting backend build from source..."
oc start-build backend --from-dir=backend/ --follow

echo "Deploying Backend API..."
oc apply -f openshift/deployments/backend-deployment.yaml
oc apply -f openshift/services/backend-service.yaml
oc apply -f openshift/routes/backend-route.yaml

echo "Waiting for backend to be ready..."
oc wait --for=condition=ready pod -l app=backend --timeout=300s || true

echo ""
echo "=========================================="
echo "Step 5: Seed Database (Optional)"
echo "=========================================="

read -p "Do you want to seed the database with sample data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running RAG seeding job..."
    oc apply -f openshift/jobs/seed-rag-job.yaml

    echo "Running claims seeding job..."
    oc apply -f openshift/jobs/seed-claims-job.yaml
fi

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="

echo ""
echo "Services deployed:"
oc get pods -l 'app in (postgresql,ocr-mcp-server,rag-mcp-server,backend)'

echo ""
echo "Backend API Route:"
oc get route backend -o jsonpath='{.spec.host}' && echo

echo ""
echo "LlamaStack endpoint (internal):"
echo "http://llamastack.claims-demo.svc.cluster.local:8321"

echo ""
echo "To check logs:"
echo "  Backend:     oc logs -f deployment/backend"
echo "  OCR Server:  oc logs -f deployment/ocr-mcp-server"
echo "  RAG Server:  oc logs -f deployment/rag-mcp-server"
echo "  LlamaStack:  oc logs -f deployment/llamastack"

echo ""
echo "To test the API:"
BACKEND_URL=$(oc get route backend -o jsonpath='{.spec.host}')
echo "  curl https://$BACKEND_URL/api/v1/health"
echo "  curl https://$BACKEND_URL/api/v1/claims"

echo ""
echo "=========================================="

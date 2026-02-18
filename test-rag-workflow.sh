#!/bin/bash
set -e

echo "=========================================="
echo "Tests RAG Server + Workflow End-to-End"
echo "=========================================="

NAMESPACE="claims-demo"

# Couleurs pour les logs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}[1/5] Vérification des pods...${NC}"
echo "RAG Server:"
oc get pods -n ${NAMESPACE} -l app=rag-server
echo -e "\nBackend:"
oc get pods -n ${NAMESPACE} -l app=backend
echo -e "\nLlamaStack:"
oc get pods -n ${NAMESPACE} -l app=claims-llamastack

RAG_POD=$(oc get pod -n ${NAMESPACE} -l app=rag-server -o jsonpath='{.items[0].metadata.name}')
BACKEND_POD=$(oc get pod -n ${NAMESPACE} -l app=backend -o jsonpath='{.items[0].metadata.name}')

echo -e "\n${YELLOW}[2/5] Test RAG Server - Health Check${NC}"
oc exec -n ${NAMESPACE} ${RAG_POD} -- curl -s http://localhost:8080/health/ready | jq .

echo -e "\n${YELLOW}[3/5] Test RAG Server - Retrieve User Info${NC}"
echo "Query: health insurance contracts pour USER001"
oc exec -n ${NAMESPACE} ${RAG_POD} -- curl -s -X POST http://localhost:8080/retrieve_user_info \
  -H "Content-Type: application/json" \
  -d '{"user_id":"USER001","query":"health insurance contracts","top_k":3}' | jq .

echo -e "\n${YELLOW}[4/5] Test RAG Server - Search Knowledge Base${NC}"
echo "Query: claim submission guidelines"
oc exec -n ${NAMESPACE} ${RAG_POD} -- curl -s -X POST http://localhost:8080/search_knowledge_base \
  -H "Content-Type: application/json" \
  -d '{"query":"claim submission guidelines","top_k":3}' | jq .

echo -e "\n${YELLOW}[5/5] Test Workflow End-to-End - Process Claim${NC}"
echo "Processing claim 1 avec OCR + RAG..."

# Lancer le traitement
oc exec -n ${NAMESPACE} ${BACKEND_POD} -- curl -s -X POST http://localhost:8000/api/claims/1/process \
  -H 'Content-Type: application/json' \
  -d '{"enable_rag":true,"skip_ocr":false}' > /tmp/claim_response.json

echo -e "\n${GREEN}Résultat du traitement:${NC}"
cat /tmp/claim_response.json | jq .

echo -e "\n${YELLOW}Statut du claim:${NC}"
oc exec -n ${NAMESPACE} ${BACKEND_POD} -- curl -s http://localhost:8000/api/claims/1/status | jq .

echo -e "\n${YELLOW}Logs de traitement:${NC}"
oc exec -n ${NAMESPACE} ${BACKEND_POD} -- curl -s http://localhost:8000/api/claims/1/logs | jq .

echo -e "\n${GREEN}=========================================="
echo "✓ Tests terminés!"
echo "==========================================${NC}"

echo -e "\n${YELLOW}Pour voir les logs détaillés:${NC}"
echo "Backend:     oc logs -f -n ${NAMESPACE} ${BACKEND_POD}"
echo "RAG Server:  oc logs -f -n ${NAMESPACE} ${RAG_POD}"
echo "LlamaStack:  oc logs -f -n ${NAMESPACE} -l app=claims-llamastack"

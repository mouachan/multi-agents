#!/bin/bash
set -e

echo "=========================================="
echo "Déploiement RAG Server + Vector Store"
echo "=========================================="

NAMESPACE="claims-demo"
RAG_SERVER_DIR="/Users/mouchan/projects/agentic-claim-demo/backend/mcp_servers/rag_server"

# Couleurs pour les logs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}[1/6] Build et déploiement RAG Server...${NC}"
echo "Option 1: Build sur OpenShift (recommandé)"
oc start-build rag-server --from-dir=${RAG_SERVER_DIR}/ --follow -n ${NAMESPACE}

# Option 2 (alternative si Option 1 ne marche pas):
# echo "Option 2: Build local + push manuel"
# cd ${RAG_SERVER_DIR}
# podman build --platform linux/amd64 -t quay.io/mouchan/rag-server:latest .
# podman push quay.io/mouchan/rag-server:latest

echo -e "${GREEN}✓ Build terminé${NC}"

echo -e "\n${YELLOW}[2/6] Redémarrage du pod RAG Server...${NC}"
oc delete pods -l app=rag-server -n ${NAMESPACE}
echo "Attente du nouveau pod..."
oc wait --for=condition=ready pod -l app=rag-server -n ${NAMESPACE} --timeout=120s
echo -e "${GREEN}✓ RAG Server redémarré${NC}"

echo -e "\n${YELLOW}[3/6] Vérification des ConfigMaps et Secrets...${NC}"
oc get configmap init-vectorstore-script -n ${NAMESPACE} || {
  echo "Création du ConfigMap..."
  oc create configmap init-vectorstore-script \
    --from-file=init_vectorstore.py=/Users/mouchan/projects/agentic-claim-demo/database/scripts/init_vectorstore.py \
    -n ${NAMESPACE}
}
echo -e "${GREEN}✓ ConfigMap présent${NC}"

echo -e "\n${YELLOW}[4/6] Lancement du job d'initialisation du vector store...${NC}"
# Supprimer le job précédent s'il existe
oc delete job init-vectorstore -n ${NAMESPACE} --ignore-not-found=true
echo "Démarrage du job..."
oc apply -f /Users/mouchan/projects/agentic-claim-demo/openshift/jobs/init-vectorstore-job.yaml

echo "Attente de la complétion du job (max 5min)..."
oc wait --for=condition=complete job/init-vectorstore -n ${NAMESPACE} --timeout=300s

echo -e "${GREEN}✓ Initialisation terminée${NC}"

echo -e "\n${YELLOW}[5/6] Affichage des logs d'initialisation...${NC}"
oc logs -n ${NAMESPACE} -l job-name=init-vectorstore --tail=50

echo -e "\n${YELLOW}[6/6] Tests du RAG Server...${NC}"

# Test 1: Health check
echo -e "\nTest 1: Health check"
RAG_POD=$(oc get pod -n ${NAMESPACE} -l app=rag-server -o jsonpath='{.items[0].metadata.name}')
oc exec -n ${NAMESPACE} ${RAG_POD} -- curl -s http://localhost:8080/health/ready | jq .

# Test 2: Retrieve user info
echo -e "\nTest 2: Retrieve user info (USER001)"
oc exec -n ${NAMESPACE} ${RAG_POD} -- curl -s -X POST http://localhost:8080/retrieve_user_info \
  -H "Content-Type: application/json" \
  -d '{"user_id":"USER001","query":"health insurance contracts","top_k":3}' | jq .

# Test 3: Search knowledge base
echo -e "\nTest 3: Search knowledge base"
oc exec -n ${NAMESPACE} ${RAG_POD} -- curl -s -X POST http://localhost:8080/search_knowledge_base \
  -H "Content-Type: application/json" \
  -d '{"query":"claim submission guidelines","top_k":3}' | jq .

echo -e "\n${GREEN}=========================================="
echo "✓ Déploiement terminé avec succès!"
echo "==========================================${NC}"

echo -e "\n${YELLOW}Pour tester le workflow end-to-end:${NC}"
echo "1. Vérifier les logs du backend:"
echo "   oc logs -f -n ${NAMESPACE} -l app=backend"
echo ""
echo "2. Tester un claim complet via l'API backend:"
echo "   BACKEND_POD=\$(oc get pod -n ${NAMESPACE} -l app=backend -o jsonpath='{.items[0].metadata.name}')"
echo "   oc exec -n ${NAMESPACE} \${BACKEND_POD} -- curl -s -X POST http://localhost:8000/api/claims/1/process \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"enable_rag\":true,\"skip_ocr\":false}' | jq ."

#!/bin/bash
# Script to test claim processing on OpenShift
# This script runs from a backend pod to test OCR + RAG workflow

set -e

# Configuration
NAMESPACE="claims-demo"
BACKEND_POD=""
API_URL="http://localhost:8000/api/v1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  OpenShift Claim Processing Test${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Step 1: Find backend pod
echo -e "${YELLOW}🔍 Finding backend pod in namespace ${NAMESPACE}...${NC}"
BACKEND_POD=$(oc get pods -n ${NAMESPACE} -l app=backend -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$BACKEND_POD" ]; then
  echo -e "${RED}❌ No backend pod found in namespace ${NAMESPACE}${NC}"
  echo -e "${YELLOW}Available pods:${NC}"
  oc get pods -n ${NAMESPACE}
  exit 1
fi

echo -e "${GREEN}✅ Found backend pod: ${BACKEND_POD}${NC}"
echo ""

# Step 2: Check pod readiness
echo -e "${YELLOW}⏳ Checking pod readiness...${NC}"
POD_READY=$(oc get pod ${BACKEND_POD} -n ${NAMESPACE} -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')

if [ "$POD_READY" != "True" ]; then
  echo -e "${RED}❌ Pod is not ready${NC}"
  oc get pod ${BACKEND_POD} -n ${NAMESPACE}
  exit 1
fi

echo -e "${GREEN}✅ Pod is ready${NC}"
echo ""

# Step 3: Get a pending claim
echo -e "${YELLOW}📋 Fetching pending claims...${NC}"
CLAIM_RESPONSE=$(oc exec -n ${NAMESPACE} ${BACKEND_POD} -- curl -s "${API_URL}/claims/?page=1&page_size=50")

# Extract first pending claim ID
CLAIM_ID=$(echo "$CLAIM_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for claim in data.get('claims', []):
    if claim.get('status') == 'pending':
        print(claim['id'])
        break
" 2>/dev/null || echo "")

if [ -z "$CLAIM_ID" ]; then
  echo -e "${RED}❌ No pending claims found${NC}"
  echo -e "${YELLOW}Creating a test claim...${NC}"

  # Create a test claim
  CREATE_RESPONSE=$(oc exec -n ${NAMESPACE} ${BACKEND_POD} -- curl -s -X POST "${API_URL}/claims/" \
    -H "Content-Type: application/json" \
    -d "{
      \"user_id\": \"user_001\",
      \"claim_number\": \"CLM-TEST-$(date +%s)\",
      \"claim_type\": \"AUTO\",
      \"document_path\": \"/claim_documents/claim_auto_001.pdf\"
    }")

  CLAIM_ID=$(echo "$CREATE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")

  if [ -z "$CLAIM_ID" ]; then
    echo -e "${RED}❌ Failed to create claim${NC}"
    echo "$CREATE_RESPONSE"
    exit 1
  fi

  echo -e "${GREEN}✅ Created test claim: ${CLAIM_ID}${NC}"
else
  echo -e "${GREEN}✅ Found pending claim: ${CLAIM_ID}${NC}"
fi

# Get claim details
CLAIM_INFO=$(oc exec -n ${NAMESPACE} ${BACKEND_POD} -- curl -s "${API_URL}/claims/${CLAIM_ID}")
CLAIM_NUMBER=$(echo "$CLAIM_INFO" | python3 -c "import sys, json; print(json.load(sys.stdin).get('claim_number', 'N/A'))" 2>/dev/null || echo "N/A")
CLAIM_TYPE=$(echo "$CLAIM_INFO" | python3 -c "import sys, json; print(json.load(sys.stdin).get('claim_type', 'N/A'))" 2>/dev/null || echo "N/A")

echo -e "${BLUE}Claim Number: ${CLAIM_NUMBER}${NC}"
echo -e "${BLUE}Claim Type: ${CLAIM_TYPE}${NC}"
echo ""

# Step 4: Launch claim processing
echo -e "${YELLOW}🚀 Launching claim processing (OCR + RAG)...${NC}"
PROCESS_RESPONSE=$(oc exec -n ${NAMESPACE} ${BACKEND_POD} -- curl -s -X POST "${API_URL}/claims/${CLAIM_ID}/process" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "standard",
    "skip_ocr": false,
    "enable_rag": true,
    "skip_guardrails": false
  }')

echo "$PROCESS_RESPONSE" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))" 2>/dev/null || echo "$PROCESS_RESPONSE"
echo ""

# Step 5: Monitor processing status
echo -e "${YELLOW}⏳ Monitoring processing status...${NC}"
echo ""

MAX_WAIT=300  # 5 minutes max
ELAPSED=0
INTERVAL=3

while [ $ELAPSED -lt $MAX_WAIT ]; do
  STATUS_RESPONSE=$(oc exec -n ${NAMESPACE} ${BACKEND_POD} -- curl -s "${API_URL}/claims/${CLAIM_ID}/status")

  STATUS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "unknown")
  PROGRESS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('progress_percentage', 0))" 2>/dev/null || echo "0")
  CURRENT_STEP=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('current_step', 'N/A'))" 2>/dev/null || echo "N/A")

  TIMESTAMP=$(date +%H:%M:%S)
  echo -e "[${TIMESTAMP}] ${BLUE}Status: ${STATUS} | Progress: ${PROGRESS}% | Step: ${CURRENT_STEP}${NC}"

  if [ "$STATUS" == "completed" ]; then
    echo -e "${GREEN}✅ Processing completed!${NC}"
    break
  elif [ "$STATUS" == "failed" ]; then
    echo -e "${RED}❌ Processing failed!${NC}"
    break
  fi

  sleep $INTERVAL
  ELAPSED=$((ELAPSED + INTERVAL))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
  echo -e "${RED}⚠️  Timeout: Processing took longer than ${MAX_WAIT}s${NC}"
fi

echo ""

# Step 6: Get final decision
echo -e "${YELLOW}📊 Fetching decision...${NC}"
DECISION_RESPONSE=$(oc exec -n ${NAMESPACE} ${BACKEND_POD} -- curl -s "${API_URL}/claims/${CLAIM_ID}/decision")

echo "$DECISION_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"Decision: {data.get('decision', 'N/A')}\")
    print(f\"Confidence: {data.get('confidence', 0):.2%}\")
    print(f\"Reasoning: {data.get('reasoning', 'N/A')}\")
    print(f\"Model: {data.get('llm_model', 'N/A')}\")
except:
    print('Failed to parse decision')
" 2>/dev/null || echo "$DECISION_RESPONSE"

echo ""

# Step 7: Get processing logs
echo -e "${YELLOW}📝 Fetching processing logs...${NC}"
LOGS_RESPONSE=$(oc exec -n ${NAMESPACE} ${BACKEND_POD} -- curl -s "${API_URL}/claims/${CLAIM_ID}/logs")

echo "$LOGS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    logs = data.get('logs', [])
    print(f\"\n{'='*80}\")
    print(f\"Processing Logs ({len(logs)} steps):\")
    print(f\"{'='*80}\")
    for log in logs:
        step = log.get('step_name', 'N/A')
        status = log.get('status', 'N/A')
        duration = log.get('duration_ms', 0)
        print(f\"  • {step}: {status} ({duration}ms)\")
    print(f\"{'='*80}\")
except Exception as e:
    print(f'Failed to parse logs: {e}')
" 2>/dev/null || echo "$LOGS_RESPONSE"

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  Test completed!${NC}"
echo -e "${GREEN}================================================${NC}"

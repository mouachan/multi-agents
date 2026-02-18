#!/bin/bash
# Test script for Claims Processing API endpoints
# Usage: ./test-api-endpoints.sh

set -e

# Configuration
BACKEND_URL="${BACKEND_URL:-https://backend-claims-demo.apps.cluster-rk6mx.rk6mx.sandbox492.opentlc.com}"
API_PREFIX="/api/v1"

echo "🧪 Testing Claims Processing API"
echo "📍 Backend URL: $BACKEND_URL"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local data=$4

    echo -e "${YELLOW}Testing:${NC} $description"
    echo -e "  ${method} ${BACKEND_URL}${endpoint}"

    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "${BACKEND_URL}${endpoint}")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "${BACKEND_URL}${endpoint}" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "  ${GREEN}✓ Success${NC} (HTTP $http_code)"
        echo "  Response: $(echo $body | jq -C . 2>/dev/null || echo $body | head -c 100)"
    else
        echo -e "  ${RED}✗ Failed${NC} (HTTP $http_code)"
        echo "  Response: $(echo $body | jq -C . 2>/dev/null || echo $body)"
    fi
    echo ""
}

# Run tests
echo "=== Health Checks ==="
test_endpoint "GET" "/" "Root endpoint"
test_endpoint "GET" "/health/live" "Liveness probe"
test_endpoint "GET" "/health/ready" "Readiness probe"

echo "=== Claims API ==="
test_endpoint "GET" "${API_PREFIX}/claims" "List all claims"
test_endpoint "GET" "${API_PREFIX}/claims?status=pending" "List pending claims"

# Get first claim ID if available
CLAIM_ID=$(curl -s "${BACKEND_URL}${API_PREFIX}/claims" | jq -r '.claims[0].id // empty' 2>/dev/null)

if [ ! -z "$CLAIM_ID" ]; then
    echo "Using claim ID: $CLAIM_ID"
    test_endpoint "GET" "${API_PREFIX}/claims/${CLAIM_ID}" "Get claim details"
    test_endpoint "POST" "${API_PREFIX}/claims/${CLAIM_ID}/process" "Process claim" '{}'
    test_endpoint "GET" "${API_PREFIX}/claims/${CLAIM_ID}/status" "Get processing status"
    test_endpoint "GET" "${API_PREFIX}/claims/${CLAIM_ID}/logs" "Get processing logs"
else
    echo -e "${YELLOW}⚠ No claims found in database. Skipping claim-specific tests.${NC}"
fi

echo "=== Documents API ==="
echo -e "${YELLOW}Note:${NC} Document upload requires multipart/form-data - use separate test"

echo ""
echo "=== Summary ==="
echo "All endpoints tested. Check for any failures above."
echo ""
echo "💡 Tips:"
echo "  - Correct API prefix is: ${API_PREFIX} (not /api)"
echo "  - Ensure database is seeded with claims for full testing"
echo "  - Check logs: oc logs -n claims-demo deployment/backend --tail=50"

#!/bin/bash

NS=${1:-claims-demo}

PG_SECRET="$(oc -n "$NS" get secret -l app=postgresql -o name | head -1)"
DATABASE="$(oc -n "$NS" get "$PG_SECRET" -o yaml | yq -r '.data["POSTGRES_DATABASE"]' | base64 --decode)"
BACKEND="$(oc -n "$NS" get route backend -o yaml | yq -r .spec.host)"
FRONTEND="$(oc -n "$NS" get route frontend -o yaml | yq -r .spec.host)"

echo "════════════════════════════════════════════════════════════════"
echo "🗑️  CLEANING DATABASE..."
echo "════════════════════════════════════════════════════════════════"

# Delete all existing claims
oc exec postgresql-0 -n "$NS" -- psql -d "$DATABASE" -c "DELETE FROM claim_decisions; DELETE FROM processing_logs; DELETE FROM claims;"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📝 CREATING 10 PENDING CLAIMS..."
echo "════════════════════════════════════════════════════════════════"

BACKEND_URL="https://$BACKEND/api/v1/claims/"

# Array to store claim IDs
declare -a CLAIMS

# Claim 1 - USER001 - T-bone collision
CLAIMS[1]=$(curl -s -X POST "$BACKEND_URL" -H "Content-Type: application/json" -d '{"user_id":"USER001","claim_number":"CLM-2026-AUTO-001","claim_type":"AUTO","document_path":"/claim_documents/claim_auto_001.pdf"}' | jq -r '.id')
echo "✓ Claim 1 created: ${CLAIMS[1]}"

# Claim 2 - USER002 - Multi-vehicle pileup
CLAIMS[2]=$(curl -s -X POST "$BACKEND_URL" -H "Content-Type: application/json" -d '{"user_id":"USER002","claim_number":"CLM-2026-AUTO-002","claim_type":"AUTO","document_path":"/claim_documents/claim_auto_002.pdf"}' | jq -r '.id')
echo "✓ Claim 2 created: ${CLAIMS[2]}"

# Claim 3 - USER003 - Parking lot collision (NO CONTRACTS)
CLAIMS[3]=$(curl -s -X POST "$BACKEND_URL" -H "Content-Type: application/json" -d '{"user_id":"USER003","claim_number":"CLM-2026-AUTO-003","claim_type":"AUTO","document_path":"/claim_documents/claim_auto_003.pdf"}' | jq -r '.id')
echo "✓ Claim 3 created: ${CLAIMS[3]}"

# Claim 4 - USER001 - T-bone collision
CLAIMS[4]=$(curl -s -X POST "$BACKEND_URL" -H "Content-Type: application/json" -d '{"user_id":"USER001","claim_number":"CLM-2026-AUTO-004","claim_type":"AUTO","document_path":"/claim_documents/claim_auto_001.pdf"}' | jq -r '.id')
echo "✓ Claim 4 created: ${CLAIMS[4]}"

# Claim 5 - USER002 - Multi-vehicle pileup
CLAIMS[5]=$(curl -s -X POST "$BACKEND_URL" -H "Content-Type: application/json" -d '{"user_id":"USER002","claim_number":"CLM-2026-AUTO-005","claim_type":"AUTO","document_path":"/claim_documents/claim_auto_002.pdf"}' | jq -r '.id')
echo "✓ Claim 5 created: ${CLAIMS[5]}"

# Claim 6 - USER003 - Parking lot collision (NO CONTRACTS)
CLAIMS[6]=$(curl -s -X POST "$BACKEND_URL" -H "Content-Type: application/json" -d '{"user_id":"USER003","claim_number":"CLM-2026-AUTO-006","claim_type":"AUTO","document_path":"/claim_documents/claim_auto_003.pdf"}' | jq -r '.id')
echo "✓ Claim 6 created: ${CLAIMS[6]}"

# Claim 7 - USER001 - T-bone collision
CLAIMS[7]=$(curl -s -X POST "$BACKEND_URL" -H "Content-Type: application/json" -d '{"user_id":"USER001","claim_number":"CLM-2026-AUTO-007","claim_type":"AUTO","document_path":"/claim_documents/claim_auto_001.pdf"}' | jq -r '.id')
echo "✓ Claim 7 created: ${CLAIMS[7]}"

# Claim 8 - USER002 - Multi-vehicle pileup
CLAIMS[8]=$(curl -s -X POST "$BACKEND_URL" -H "Content-Type: application/json" -d '{"user_id":"USER002","claim_number":"CLM-2026-AUTO-008","claim_type":"AUTO","document_path":"/claim_documents/claim_auto_002.pdf"}' | jq -r '.id')
echo "✓ Claim 8 created: ${CLAIMS[8]}"

# Claim 9 - USER001 - T-bone collision
CLAIMS[9]=$(curl -s -X POST "$BACKEND_URL" -H "Content-Type: application/json" -d '{"user_id":"USER001","claim_number":"CLM-2026-AUTO-009","claim_type":"AUTO","document_path":"/claim_documents/claim_auto_001.pdf"}' | jq -r '.id')
echo "✓ Claim 9 created: ${CLAIMS[9]}"

# Claim 10 - USER003 - Parking lot collision (NO CONTRACTS)
CLAIMS[10]=$(curl -s -X POST "$BACKEND_URL" -H "Content-Type: application/json" -d '{"user_id":"USER003","claim_number":"CLM-2026-AUTO-010","claim_type":"AUTO","document_path":"/claim_documents/claim_auto_003.pdf"}' | jq -r '.id')
echo "✓ Claim 10 created: ${CLAIMS[10]}"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ SUCCESSFULLY CREATED 10 PENDING CLAIMS!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 CLAIM DETAILS:"
echo ""
echo "Claim 1 (USER001 - T-bone, \$3,153)"
echo "  https://$FRONTEND/claims/${CLAIMS[1]}"
echo ""
echo "Claim 2 (USER002 - Pileup, \$6,497)"
echo "  https://$FRONTEND/claims/${CLAIMS[2]}"
echo ""
echo "Claim 3 (USER003 - Parking, \$6,793 - NO CONTRACTS)"
echo "  https://$FRONTEND/claims/${CLAIMS[3]}"
echo ""
echo "Claim 4 (USER001 - T-bone, \$3,153)"
echo "  https://$FRONTEND/claims/${CLAIMS[4]}"
echo ""
echo "Claim 5 (USER002 - Pileup, \$6,497)"
echo "  https://$FRONTEND/claims/${CLAIMS[5]}"
echo ""
echo "Claim 6 (USER003 - Parking, \$6,793 - NO CONTRACTS)"
echo "  https://$FRONTEND/claims/${CLAIMS[6]}"
echo ""
echo "Claim 7 (USER001 - T-bone, \$3,153)"
echo "  https://$FRONTEND/claims/${CLAIMS[7]}"
echo ""
echo "Claim 8 (USER002 - Pileup, \$6,497)"
echo "  https://$FRONTEND/claims/${CLAIMS[8]}"
echo ""
echo "Claim 9 (USER001 - T-bone, \$3,153)"
echo "  https://$FRONTEND/claims/${CLAIMS[9]}"
echo ""
echo "Claim 10 (USER003 - Parking, \$6,793 - NO CONTRACTS)"
echo "  https://$FRONTEND/claims/${CLAIMS[10]}"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🎯 MAIN CLAIMS LIST:"
echo "   https://$FRONTEND/claims"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "💡 Expected outcomes:"
echo "   - Claims with USER001/USER002: Should APPROVE (have contracts)"
echo "   - Claims with USER003: Should MANUAL_REVIEW (no contracts)"
echo ""

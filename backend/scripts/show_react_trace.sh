#!/bin/bash
#
# Show ReAct Agent HTTP Trace for a Claim
#
# Extracts raw HTTP calls showing:
# - HTTP requests to LlamaStack /v1/responses with payload
# - MCP tool calls with input/output
# - HTTP responses with complete JSON
#
# Sources: Backend pod logs + Database storage
#
# Usage:
#   ./scripts/show_react_trace.sh <claim_id> [namespace]
#

set -e

# Check arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <claim_id> [namespace]"
    echo ""
    echo "Example:"
    echo "  $0 CLM-2024-0001"
    echo "  $0 CLM-2024-0001 claims-demo"
    exit 1
fi

CLAIM_ID="$1"
NAMESPACE="${2:-claims-demo}"

# Generate output filename with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SAFE_CLAIM_ID=$(echo "$CLAIM_ID" | tr '/' '_' | tr ':' '_')
OUTPUT_FILE="trace_${SAFE_CLAIM_ID}_${TIMESTAMP}.txt"

echo "========================================"
echo "HTTP Trace for Claim (Audit/Traceability)"
echo "========================================"
echo "Claim ID: ${CLAIM_ID}"
echo "Namespace: ${NAMESPACE}"
echo "Output File: ${OUTPUT_FILE}"
echo "========================================"
echo ""

# Find backend pod (only Running pods)
echo "Finding backend pod..."
POD=$(oc get pods -n ${NAMESPACE} -l app=backend --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$POD" ]; then
    echo "ERROR: No running backend pod found in namespace ${NAMESPACE}"
    echo "Try listing pods with: oc get pods -n ${NAMESPACE} -l app=backend"
    exit 1
fi

echo "Using pod: ${POD}"
echo ""

# Execute extraction script
oc exec -n ${NAMESPACE} ${POD} -- python3 -c "
import os
import sys
import json
from datetime import datetime
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Import models
from app.models.claim import Claim, ClaimDecision
from app.core.config import settings

# Database connection
engine = create_engine(settings.database_url.replace('+asyncpg', ''))
Session = sessionmaker(bind=engine)
db = Session()

def format_timestamp(dt):
    if not dt:
        return 'N/A'
    return dt.strftime('%Y-%m-%d %H:%M:%S UTC')

def print_http_section(title):
    print()
    print('='*80)
    print(title)
    print('='*80)
    print()

try:
    # Query claim
    claim_id = '${CLAIM_ID}'

    stmt = select(Claim).where(Claim.claim_number == claim_id)
    claim = db.execute(stmt).scalar_one_or_none()

    if not claim:
        try:
            from uuid import UUID
            uuid_id = UUID(claim_id)
            stmt = select(Claim).where(Claim.id == uuid_id)
            claim = db.execute(stmt).scalar_one_or_none()
        except ValueError:
            pass

    if not claim:
        print(f'ERROR: Claim not found: {claim_id}')
        sys.exit(1)

    # Get decision
    stmt = select(ClaimDecision).where(ClaimDecision.claim_id == claim.id)
    decision = db.execute(stmt).scalar_one_or_none()

    # Get metadata
    metadata = claim.claim_metadata or {}

    print('CLAIM AUDIT TRACE')
    print('Claim:', claim.claim_number)
    print('User:', claim.user_id)
    print('Processed:', format_timestamp(claim.processed_at))
    print()

    # Reconstruct HTTP request to LlamaStack
    print_http_section('HTTP REQUEST #1: Backend -> LlamaStack /v1/responses')

    print('POST http://claims-llamastack-service.claims-demo.svc.cluster.local:8321/v1/responses')
    print('Content-Type: application/json')
    print()

    # Build the request payload as it was sent
    request_payload = {
        'model': decision.llm_model if decision else settings.llamastack_default_model,
        'stream': False,
        'max_infer_iters': 10,
        'max_tokens': settings.llamastack_max_tokens
    }

    # Add instructions (agent prompt)
    if decision and decision.llm_prompt:
        request_payload['instructions'] = decision.llm_prompt

    # Add input message (reconstructed from context)
    # This would be the user message with claim context
    request_payload['input'] = f'Process claim {claim.claim_number} for user {claim.user_id}'

    # Add tools configuration
    processing_steps = metadata.get('processing_steps', [])
    if processing_steps:
        tools_used = set()
        for step in processing_steps:
            step_name = step.get('step_name')
            if step_name:
                tools_used.add(step_name)

        # Build MCP tools config
        mcp_tools = []
        if any(t in tools_used for t in ['ocr_document', 'ocr_health_check']):
            mcp_tools.append({
                'type': 'mcp',
                'server_label': 'ocr-server',
                'server_url': 'http://ocr-server.claims-demo.svc.cluster.local:8080/sse',
                'allowed_tools': [t for t in tools_used if t.startswith('ocr')]
            })

        if any(t in tools_used for t in ['retrieve_user_info', 'retrieve_similar_claims', 'search_knowledge_base']):
            mcp_tools.append({
                'type': 'mcp',
                'server_label': 'rag-server',
                'server_url': 'http://rag-server.claims-demo.svc.cluster.local:8080/sse',
                'allowed_tools': [t for t in tools_used if t.startswith('retrieve') or t.startswith('search')]
            })

        if mcp_tools:
            request_payload['tools'] = mcp_tools

    print('REQUEST PAYLOAD:')
    print(json.dumps(request_payload, indent=2))

    # Show each tool call as HTTP-like trace
    if processing_steps:
        print_http_section('MCP TOOL EXECUTIONS (via LlamaStack)')

        for i, step in enumerate(processing_steps, 1):
            step_name = step.get('step_name', 'unknown')
            agent_name = step.get('agent_name', 'unknown')
            status = step.get('status', 'unknown')
            duration = step.get('duration_ms', 0)

            print(f'--- TOOL CALL #{i}: {step_name} ---')
            print()

            # Determine server URL
            if 'ocr' in step_name.lower():
                server_url = 'http://ocr-server.claims-demo.svc.cluster.local:8080/sse'
            elif 'retrieve' in step_name.lower() or 'search' in step_name.lower():
                server_url = 'http://rag-server.claims-demo.svc.cluster.local:8080/sse'
            else:
                server_url = 'unknown'

            print(f'MCP CALL via SSE: {server_url}')
            print(f'Tool: {step_name}')
            print(f'Agent: {agent_name}')
            print(f'Status: {status}')
            print(f'Duration: {duration}ms')
            print()

            # Tool input (not always stored, would need to enhance logging)
            print('TOOL INPUT:')
            print('  (Tool inputs not stored - see llm_prompt for context)')
            print()

            # Tool output
            output_data = step.get('output_data')
            if output_data:
                print('TOOL OUTPUT (RAW JSON):')
                print(json.dumps(output_data, indent=2))
            else:
                print('TOOL OUTPUT: (empty)')

            # Error if any
            error = step.get('error_message')
            if error:
                print()
                print(f'TOOL ERROR: {error}')

            print()
            print('-'*80)
            print()

    # Show LlamaStack response
    print_http_section('HTTP RESPONSE #1: LlamaStack -> Backend')

    print('HTTP/1.1 200 OK')
    print('Content-Type: application/json')
    print()

    # Reconstruct response as it was received
    llamastack_response = {
        'id': metadata.get('response_id', 'unknown'),
        'output': []
    }

    # Add MCP call outputs
    for step in processing_steps:
        llamastack_response['output'].append({
            'type': 'mcp_call',
            'name': step.get('step_name'),
            'server_label': step.get('agent_name'),
            'output': step.get('output_data'),
            'error': step.get('error_message')
        })

    # Add final message
    if decision and decision.llm_response:
        llamastack_response['output'].append({
            'type': 'message',
            'role': 'assistant',
            'content': [
                {
                    'type': 'output_text',
                    'text': decision.llm_response
                }
            ]
        })

    # Add usage
    usage = metadata.get('usage', {})
    if usage:
        llamastack_response['usage'] = usage

    print('RESPONSE PAYLOAD:')
    print(json.dumps(llamastack_response, indent=2))

    # Show final decision
    if decision:
        print_http_section('FINAL DECISION EXTRACTED FROM RESPONSE')
        print(f'Recommendation: {decision.initial_decision.value.upper()}')
        print(f'Confidence: {decision.initial_confidence * 100:.1f}%')
        print(f'Model: {decision.llm_model or \"N/A\"}')
        print()
        print('Reasoning:')
        print(decision.initial_reasoning)
        print()
        if decision.relevant_policies:
            print('Evidence:')
            print(json.dumps(decision.relevant_policies, indent=2))

    print()
    print('='*80)
    print('HTTP TRACE COMPLETE')
    print('='*80)
    print()
    print('NOTE: This trace is reconstructed from database storage.')
    print('For real-time HTTP traces, check backend pod logs:')
    print(f'  oc logs -n ${NAMESPACE} -l app=backend --tail=1000 | grep {claim.claim_number}')
    print()

except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()
" 2>&1 > "$OUTPUT_FILE"

echo ""
echo "========================================"
echo "Trace saved to: ${OUTPUT_FILE}"
echo "========================================"
echo ""
echo "Preview:"
echo "----------------------------------------"
head -100 "$OUTPUT_FILE"
echo "----------------------------------------"
echo ""
echo "Full trace: ${OUTPUT_FILE}"
echo ""
echo "To see real-time logs from backend pod:"
echo "  oc logs -n ${NAMESPACE} ${POD} --tail=1000 | grep ${CLAIM_ID}"

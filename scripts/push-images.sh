#!/bin/bash
set -e

echo "=========================================="
echo "Pushing MCP Server Images to Quay.io"
echo "=========================================="

QUAY_REPO="quay.io/mouachan/agentic-claims-demo"

# Check if logged in to Quay.io
if ! podman login quay.io --get-login &>/dev/null; then
    echo "Not logged in to Quay.io. Please login:"
    podman login quay.io
fi

echo ""
echo "Pushing OCR Server image..."
podman push ${QUAY_REPO}/ocr-server:latest

echo ""
echo "Pushing RAG Server image..."
podman push ${QUAY_REPO}/rag-server:latest

echo ""
echo "=========================================="
echo "Images pushed successfully!"
echo "=========================================="

echo ""
echo "Images available at:"
echo "  - ${QUAY_REPO}/ocr-server:latest"
echo "  - ${QUAY_REPO}/rag-server:latest"

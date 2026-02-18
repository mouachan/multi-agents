#!/bin/bash

# Script to upload claim PDFs to OpenShift PVC
# Usage: ./upload_pdfs_to_openshift.sh

set -e

NAMESPACE="claims-demo"
PVC_NAME="claim-documents"
LOCAL_PDF_DIR="/tmp/claim_documents"

echo "=== Uploading Claim PDFs to OpenShift ==="
echo "Namespace: $NAMESPACE"
echo "PVC: $PVC_NAME"
echo "Local directory: $LOCAL_PDF_DIR"
echo

# Check if PDFs exist locally
if [ ! -d "$LOCAL_PDF_DIR" ]; then
    echo "Error: PDF directory not found: $LOCAL_PDF_DIR"
    echo "Please run generate_claim_pdfs.py first"
    exit 1
fi

PDF_COUNT=$(ls -1 $LOCAL_PDF_DIR/*.pdf 2>/dev/null | wc -l)
if [ "$PDF_COUNT" -eq 0 ]; then
    echo "Error: No PDF files found in $LOCAL_PDF_DIR"
    exit 1
fi

echo "Found $PDF_COUNT PDF files to upload"
echo

# Create a temporary pod to mount the PVC
echo "Creating temporary upload pod..."
cat <<EOF | oc apply -n $NAMESPACE -f -
apiVersion: v1
kind: Pod
metadata:
  name: pdf-uploader
  namespace: $NAMESPACE
spec:
  containers:
  - name: uploader
    image: registry.access.redhat.com/ubi8/ubi-minimal:latest
    command: ["sleep", "3600"]
    volumeMounts:
    - name: claim-documents
      mountPath: /claim_documents
  volumes:
  - name: claim-documents
    persistentVolumeClaim:
      claimName: $PVC_NAME
  restartPolicy: Never
EOF

# Wait for pod to be ready
echo "Waiting for pod to be ready..."
oc wait --for=condition=Ready pod/pdf-uploader -n $NAMESPACE --timeout=60s

# Create directory in PVC if it doesn't exist
echo "Creating directory structure in PVC..."
oc exec pdf-uploader -n $NAMESPACE -- mkdir -p /claim_documents

# Copy PDFs to the PVC
echo "Copying PDF files..."
oc rsync $LOCAL_PDF_DIR/ pdf-uploader:/claim_documents/ -n $NAMESPACE

# Verify upload
echo
echo "Verifying upload..."
FILE_COUNT=$(oc exec pdf-uploader -n $NAMESPACE -- ls -1 /claim_documents/*.pdf 2>/dev/null | wc -l)
echo "Files in PVC: $FILE_COUNT"

# Clean up
echo
echo "Cleaning up temporary pod..."
oc delete pod pdf-uploader -n $NAMESPACE

echo
echo "✓ Upload complete!"
echo "PDFs are now available at /claim_documents/ in the PVC"

#!/bin/bash

set -e

echo ============================================
echo Copying test claim documents to PVC
echo ============================================

# GitHub repository details
REPO=mouachan/agentic-claim-demo
BRANCH=main
PDF_DIR=backend/test_data/claim_documents

# Target directory in PVC
TARGET_DIR=/claim_documents

# Create target directory
mkdir -p $TARGET_DIR

# Generate list of all PDF files (50 total)
PDF_FILES=()

# Auto claims (20 files: claim_auto_001 to claim_auto_020)
for i in {1..20}; do
  PDF_FILES+=("claim_auto_$(printf "%03d" "$i").pdf")
done

# Home claims (15 files: claim_home_001 to claim_home_015)
for i in {1..15}; do
  PDF_FILES+=("claim_home_$(printf "%03d" "$i").pdf")
done

# Medical claims (15 files: claim_medical_001 to claim_medical_015)
for i in {1..15}; do
  PDF_FILES+=("claim_medical_$(printf "%03d" "$i").pdf")
done

echo ""
echo "Downloading ${#PDF_FILES[@]} PDF files from GitHub..."
echo ""

# Download each PDF file
DOWNLOADED=0
FAILED=0

for PDF_FILE in "${PDF_FILES[@]}"; do
  URL="https://raw.githubusercontent.com/$REPO/$BRANCH/$PDF_DIR/$PDF_FILE"
  echo "Downloading: $PDF_FILE"

  if curl -L -s -f -o "$TARGET_DIR/$PDF_FILE" "$URL"; then
    echo "  ✓ Downloaded successfully"
    DOWNLOADED=$((DOWNLOADED + 1))
  else
    echo "  ✗ Failed to download"
    FAILED=$((FAILED + 1))
  fi
done

echo ""
echo ============================================
echo "Download summary: $DOWNLOADED successful, $FAILED failed"
echo ============================================

if [ "$FAILED" -gt 0 ]; then
  echo WARNING: Some files failed to download
fi

echo ""
echo ============================================
echo "Download summary (claims): $DOWNLOADED successful, $FAILED failed"
echo ============================================

# ============================================
# Tender / AO documents
# ============================================
echo ""
echo ============================================
echo Copying test AO (tender) documents to PVC
echo ============================================

AO_PDF_DIR=backend/test_data/tender_documents
AO_TARGET_DIR=/claim_documents/ao
mkdir -p $AO_TARGET_DIR

AO_FILES=(
  "ao_2026_0042.pdf"
  "ao_2026_0043.pdf"
  "ao_2026_0044.pdf"
  "ao_2026_0045.pdf"
  "ao_2026_0046.pdf"
)

AO_DOWNLOADED=0
AO_FAILED=0

for AO_FILE in "${AO_FILES[@]}"; do
  URL="https://raw.githubusercontent.com/$REPO/$BRANCH/$AO_PDF_DIR/$AO_FILE"
  echo "Downloading: $AO_FILE"

  if curl -L -s -f -o "$AO_TARGET_DIR/$AO_FILE" "$URL"; then
    echo "  OK Downloaded successfully"
    AO_DOWNLOADED=$((AO_DOWNLOADED + 1))
  else
    echo "  FAIL Failed to download"
    AO_FAILED=$((AO_FAILED + 1))
  fi
done

echo ""
echo ============================================
echo "Download summary (AO): $AO_DOWNLOADED successful, $AO_FAILED failed"
echo ============================================

if [ "$FAILED" -gt 0 ] || [ "$AO_FAILED" -gt 0 ]; then
  echo WARNING: Some files failed to download
fi

echo ""
echo ============================================
echo Verifying files in PVC...
echo ============================================
ls -lhR "$TARGET_DIR"/

echo ""
TOTAL=$((DOWNLOADED + AO_DOWNLOADED))
echo ============================================
echo "Done: $TOTAL documents copied ($DOWNLOADED claims + $AO_DOWNLOADED AO)"
echo ============================================

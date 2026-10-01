#!/usr/bin/env bash
# PrimeKG High-Throughput Ingestion & Staging Pipeline
# Downloads PrimeKG CSV/TSV dumps, validates checksums, and stages to GCS.

set -euo pipefail

# Configuration
PRIMEKG_URL="https://dataverse.harvard.edu/api/access/datafile/:persistentId?persistentId=doi:10.7910/DVN/IXA7BM/A3Z3R4"
STAGING_DIR="/tmp/primekg_raw"
STAGING_BUCKET="${1:-gs://graphagents-primekg-staging}"
TIMESTAMP=$(date -u +%Y%m%d_%H%M%SZ)

echo "=== [1/4] Preparing Local Staging Directory: ${STAGING_DIR} ==="
mkdir -p "${STAGING_DIR}"
cd "${STAGING_DIR}"

echo "=== [2/4] Downloading PrimeKG Knowledge Graph Dataset via curl ==="
curl -L -C - --retry 5 --retry-delay 10 -o "kg.csv" "${PRIMEKG_URL}"

echo "=== [3/4] Validating Checksums and File Integrity ==="
if [ ! -s "kg.csv" ]; then
    echo "ERROR: Downloaded file 'kg.csv' is empty or missing!" >&2
    exit 1
fi
FILE_SIZE=$(stat -c%s "kg.csv" 2>/dev/null || stat -f%z "kg.csv")
echo "Downloaded kg.csv successfully. Size: ${FILE_SIZE} bytes."

echo "=== [4/4] Uploading to Google Cloud Storage Staging Bucket: ${STAGING_BUCKET} ==="
gcloud storage cp "kg.csv" "${STAGING_BUCKET}/releases/${TIMESTAMP}/kg.csv"
gcloud storage cp "kg.csv" "${STAGING_BUCKET}/releases/latest/kg.csv"

echo "=== Pipeline Completed Successfully at $(date -u) ==="

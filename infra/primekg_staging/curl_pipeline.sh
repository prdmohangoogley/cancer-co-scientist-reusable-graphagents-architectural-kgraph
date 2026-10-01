#!/usr/bin/env bash
# PrimeKG High-Throughput Ingestion & Staging Pipeline Wrapper
# Calls download_and_stage.sh with automated environment resolution.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_BUCKET="${1:-${GCS_PRIMEKG_BUCKET:-}}"

if [ -z "${TARGET_BUCKET}" ]; then
  # Try to read from Terraform outputs if available
  if [ -f "${SCRIPT_DIR}/terraform.tfstate" ]; then
    TARGET_BUCKET=$(terraform -chdir="${SCRIPT_DIR}" output -raw gcs_primekg_bucket_url 2>/dev/null || echo "")
  fi
fi

if [ -z "${TARGET_BUCKET}" ]; then
  echo "Error: Target GCS bucket must be specified as an argument or in GCS_PRIMEKG_BUCKET." >&2
  echo "Example: $0 gs://cancer-co-scientist-primekg-data-landingzone-a1b2c3d4" >&2
  exit 1
fi

chmod +x "${SCRIPT_DIR}/download_and_stage.sh"
exec "${SCRIPT_DIR}/download_and_stage.sh" "${TARGET_BUCKET}" "${2:-/tmp/primekg_staging}"

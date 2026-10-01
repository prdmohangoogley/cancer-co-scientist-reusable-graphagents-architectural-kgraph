#!/usr/bin/env bash
# PrimeKG Complete Dataset Acquisition & Staging Pipeline
# Harvard Dataverse DOI: doi:10.7910/DVN/IXA7BM
# MIMS Harvard PrimeKG: https://github.com/mims-harvard/PrimeKG

set -euo pipefail

TARGET_BUCKET="${1:-${GCS_PRIMEKG_BUCKET:-}}"
WORK_DIR="${2:-/tmp/primekg_staging}"
DATAVERSE_BASE="https://dataverse.harvard.edu/api/access/datafile"
TIMESTAMP=$(date -u +%Y%m%d_%H%M%SZ)

if [ -z "${TARGET_BUCKET}" ]; then
  echo "Usage: $0 <gs://cancer-co-scientist-primekg-data-landingzone-uuid> [work_dir]" >&2
  echo "Or export GCS_PRIMEKG_BUCKET environment variable." >&2
  exit 1
fi

# Ensure gs:// prefix
if [[ ! "${TARGET_BUCKET}" =~ ^gs:// ]]; then
  TARGET_BUCKET="gs://${TARGET_BUCKET}"
fi

echo "================================================================="
echo "  PrimeKG Data Acquisition & Staging Pipeline"
echo "  Target Bucket: ${TARGET_BUCKET}"
echo "  Working Dir:   ${WORK_DIR}"
echo "  Timestamp:     ${TIMESTAMP}"
echo "================================================================="

mkdir -p "${WORK_DIR}"
cd "${WORK_DIR}"

# Dataset inventory from Harvard Dataverse DOI: doi:10.7910/DVN/IXA7BM
# Format: <filename>|<file_id>|<expected_approx_bytes>|<description>
FILES=(
  "kg.csv|6180620|981751236|Primary Precision Medicine Knowledge Graph"
  "nodes.tab|6180617|8893757|Biomedical Node Taxonomy & Metadata"
  "edges.csv|6180616|386582390|Graph Edge Relationships List"
  "drug_features.tab|6180619|10030011|Drug Molecular Properties & Indications"
  "disease_features.tab|6180618|113534270|Disease Phenotypes & Clinical Guidelines"
  "README.txt|6191270|3137|Dataset Release Notes & Attribution"
)

echo "--- [1/4] Downloading Datasets from Harvard Dataverse ---"

for entry in "${FILES[@]}"; do
  IFS="|" read -r fname fid exp_size desc <<< "${entry}"
  url="${DATAVERSE_BASE}/${fid}"
  
  echo -n "Fetching ${fname} (${desc})... "
  if [ -f "${fname}" ]; then
    curr_size=$(stat -c%s "${fname}" 2>/dev/null || stat -f%z "${fname}")
    if [ "${curr_size}" -ge "${exp_size}" ]; then
      echo "Already exists locally (${curr_size} bytes). Skipping download."
      continue
    fi
    echo "Resuming partial download..."
  fi

  curl -L -C - \
    --retry 5 \
    --retry-delay 5 \
    --retry-connrefused \
    -o "${fname}" \
    "${url}"
  
  actual_size=$(stat -c%s "${fname}" 2>/dev/null || stat -f%z "${fname}")
  echo "Done. (${actual_size} bytes)"
done

echo ""
echo "--- [2/4] Verifying File Integrity & Checksums ---"
MANIFEST_JSON="manifest.json"
echo "{" > "${MANIFEST_JSON}"
echo "  \"dataset\": \"PrimeKG (Precision Medicine Knowledge Graph)\"," >> "${MANIFEST_JSON}"
echo "  \"source_doi\": \"10.7910/DVN/IXA7BM\"," >> "${MANIFEST_JSON}"
echo "  \"timestamp_utc\": \"${TIMESTAMP}\"," >> "${MANIFEST_JSON}"
echo "  \"staged_bucket\": \"${TARGET_BUCKET}\"," >> "${MANIFEST_JSON}"
echo "  \"files\": [" >> "${MANIFEST_JSON}"

first=true
for entry in "${FILES[@]}"; do
  IFS="|" read -r fname fid exp_size desc <<< "${entry}"
  
  if [ ! -s "${fname}" ]; then
    echo "ERROR: File ${fname} is empty or missing!" >&2
    exit 1
  fi
  
  actual_size=$(stat -c%s "${fname}" 2>/dev/null || stat -f%z "${fname}")
  sha256=$(sha256sum "${fname}" 2>/dev/null | awk '{print $1}' || shasum -a 256 "${fname}" | awk '{print $1}')
  
  echo "  - ${fname}: ${actual_size} bytes | SHA256: ${sha256:0:16}..."
  
  if [ "$first" = true ]; then
    first=false
  else
    echo "," >> "${MANIFEST_JSON}"
  fi

  cat <<EOF >> "${MANIFEST_JSON}"
    {
      "filename": "${fname}",
      "file_id": ${fid},
      "bytes": ${actual_size},
      "sha256": "${sha256}",
      "description": "${desc}"
    }
EOF
done

echo "  ]" >> "${MANIFEST_JSON}"
echo "}" >> "${MANIFEST_JSON}"

echo ""
echo "--- [3/4] Staging Raw Datasets to GCS Landing Zone ---"
echo "Uploading raw dumps and manifest to: ${TARGET_BUCKET}/raw/${TIMESTAMP}/"
gcloud storage cp "${MANIFEST_JSON}" "${TARGET_BUCKET}/raw/${TIMESTAMP}/manifest.json"
for entry in "${FILES[@]}"; do
  IFS="|" read -r fname _ _ _ <<< "${entry}"
  gcloud storage cp "${fname}" "${TARGET_BUCKET}/raw/${TIMESTAMP}/${fname}"
done

echo ""
echo "--- [4/4] Updating Canonical Latest Pointers ---"
echo "Mirroring to canonical ingestion target: ${TARGET_BUCKET}/releases/latest/"
gcloud storage cp "${MANIFEST_JSON}" "${TARGET_BUCKET}/releases/latest/manifest.json"
for entry in "${FILES[@]}"; do
  IFS="|" read -r fname _ _ _ <<< "${entry}"
  gcloud storage cp "${fname}" "${TARGET_BUCKET}/releases/latest/${fname}"
done

echo ""
echo "================================================================="
echo "  Acquisition & Staging Completed Successfully!"
echo "  Manifest: ${TARGET_BUCKET}/releases/latest/manifest.json"
echo "  Ready for Worker Tier ingestion (packages/graphagent)"
echo "================================================================="

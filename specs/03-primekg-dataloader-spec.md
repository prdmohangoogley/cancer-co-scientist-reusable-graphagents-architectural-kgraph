# Spec 03: Monorepo Phase 2 - PrimeKG Data Acquisition & Staging

**Milestone**: Phase 2 PrimeKG Data Acquisition & Staging  
**Status**: APPROVED & IMPLEMENTED  
**Governing Architecture MCP**: [gea-agents-arch-guidelines-mcp-server](https://github.com/prdmohangoogley/gea-agents-arch-guidelines-mcp-server)  
**Guidelines Cited**: `DOC-02` (Zero Ambient Authority & Agentic SecOps), `DOC-09` (Platform-Native State Management & Data Lakes)

---

## 1. Executive Summary & Context

To bootstrap the biomedical reasoning capabilities of the **Cancer Co-Scientist**, the platform requires the canonical **Precision Medicine Knowledge Graph (PrimeKG)** created by Harvard University and MIMS. 

PrimeKG integrates 20 high-quality biomedical resources, encompassing 17,080 diseases, 4,050,249 relationships across 10 biological scales (genes, drugs, diseases, pathways, phenotypes, molecular functions, and cellular components).

This specification defines the infrastructure as code (IaC) and automation pipelines for downloading the full PrimeKG release from the Harvard Dataverse repository and staging it into a secure, multi-regional Google Cloud Storage (GCS) landing zone bucket for downstream ingestion by the Worker Tier (`packages/graphagent`).

---

## 2. Architecture & Data Flow

```mermaid
graph TD
    subgraph ExternalSource["External Biomedical Repositories"]
        Harvard["Harvard Dataverse [doi:10.7910/DVN/IXA7BM]"]
        MIMS["MIMS Harvard PrimeKG Repository"]
    end

    subgraph GCPInfrastructure["Google Cloud Platform [fivedaysai-prd-sandbox-317383]"]
        RunnerVM["GCE Staging Runner [e2-standard-2 / 100GB SSD]"]
        RunnerSA["ZAA Scoped SA [primekg-staging-runner-sa]"]
        
        subgraph LandingZoneBucket["Multi-Regional US Landing Zone Bucket"]
            RawDir["raw/[TIMESTAMP]/ [Immutable Raw Dumps]"]
            LatestDir["releases/latest/ [Worker Ingestion Target]"]
            Manifest["manifest.json [SHA-256 Checksums]"]
        end
    end

    subgraph DownstreamWorkers["Worker Ingestion Tier [packages/graphagent]"]
        DataLoader["PrimeKG Ingestion Pipeline [data_loaders/primekg_loader.py]"]
        Spanner["Cloud Spanner Graph [PrimeKGGraph]"]
        BigQuery["BigQuery Feature Tables"]
    end

    Harvard -->|High-Throughput curl [-C -]| RunnerVM
    RunnerSA -->|Least Privilege Storage Write| RunnerVM
    RunnerVM -->|gcloud storage cp / manifest| RawDir
    RunnerVM -->|gcloud storage cp / manifest| LatestDir
    LatestDir --> DataLoader
    DataLoader --> Spanner
    DataLoader --> BigQuery
```

---

## 3. Configuration & Target Variables

| Variable | Target Value | Description |
| :--- | :--- | :--- |
| `GCP_PROJECT_ID` | `fivedaysai-prd-sandbox-317383` | Active Google Cloud project |
| `GCS_PRIMEKG_BUCKET` | `cancer-co-scientist-primekg-data-landingzone-<uuid>` | US Multi-regional GCS landing zone bucket |
| `GCS_LOCATION` | `US` | Multi-regional bucket location for global replication |
| `GCE_MACHINE_TYPE` | `e2-standard-2` | 2 vCPUs, 8 GB RAM, high-throughput network egress/ingress |
| `GCE_DISK` | `100 GB pd-ssd` | Fast I/O for 1.5GB+ concurrent download, hashing, and compression |
| `GCE_ZONE` | `us-central1-a` | Compute zone for runner instance |
| `SERVICE_ACCOUNT` | `primekg-staging-runner-sa` | Scoped SA adhering strictly to Zero Ambient Authority (`DOC-02`) |

---

## 4. Dataset Inventory (Harvard Dataverse DOI: 10.7910/DVN/IXA7BM)

The pipeline downloads and stages the complete suite of canonical PrimeKG files:

| Filename | Dataverse File ID | Approx. Size | Description |
| :--- | :---: | :---: | :--- |
| `kg.csv` | `6180620` | 981.8 MB | The core multimodal knowledge graph with 4.05M edges |
| `nodes.tab` | `6180617` | 8.9 MB | Taxonomy, node IDs, types, and biomedical entity metadata |
| `edges.csv` | `6180616` | 386.6 MB | Source-target-relation edge listing across 10 scales |
| `drug_features.tab` | `6180619` | 10.0 MB | Drug molecular properties, indications, and off-label uses |
| `disease_features.tab` | `6180618` | 113.5 MB | Disease clinical guidelines, phenotypes, and ontologies |
| `README.txt` | `6191270` | 3.1 KB | Official Harvard publication citations and usage guidelines |

---

## 5. Security & Zero Ambient Authority (DOC-02)

To satisfy `PAT-ZAA` from the Enterprise Agents Architecture guidelines:
1. **Zero Broad Project Permissions**: The GCE runner instance does not execute with the default Compute Engine service account (`PROJECT_NUMBER-compute@developer.gserviceaccount.com`).
2. **Dedicated Service Account**: A custom service account `primekg-staging-runner-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com` is provisioned.
3. **Targeted Bucket Scoping**: The SA is granted `roles/storage.objectAdmin` **exclusively** on the generated landing zone bucket (`google_storage_bucket.primekg_landingzone.name`). It possesses zero ambient read or write access to any other project buckets, BigQuery datasets, or Spanner databases.
4. **OS Login Enabled**: Direct SSH access enforces Google Cloud IAM authentication (`enable-oslogin = TRUE`).

---

## 6. Infrastructure as Code Implementation

The staging IaC resides in [`infra/primekg_staging/`](file:///Users/prdmohan/ge_spark_workspace/projects/cancer-co-scientist-reusable-graphagents-architectural-kgraph/infra/primekg_staging/):

- [`main.tf`](file:///Users/prdmohan/ge_spark_workspace/projects/cancer-co-scientist-reusable-graphagents-architectural-kgraph/infra/primekg_staging/main.tf):
  - `random_id.bucket_suffix`: Generates an 8-character hex UUID.
  - `google_storage_bucket.primekg_landingzone`: Provisions the `US` multi-region bucket with object versioning and 90-day archive lifecycle management.
  - `google_service_account.primekg_staging_runner`: Provisions the scoped identity.
  - `google_storage_bucket_iam_member.staging_writer`: Grants least-privilege bucket writes.
  - `google_compute_instance.staging_runner`: Provisions the `e2-standard-2` VM with Debian 12 and startup dependency provisioning.
- [`variables.tf`](file:///Users/prdmohan/ge_spark_workspace/projects/cancer-co-scientist-reusable-graphagents-architectural-kgraph/infra/primekg_staging/variables.tf): Configurable parameters with defaults.
- [`outputs.tf`](file:///Users/prdmohan/ge_spark_workspace/projects/cancer-co-scientist-reusable-graphagents-architectural-kgraph/infra/primekg_staging/outputs.tf): Exposes bucket name, bucket URL, instance details, and execution commands.

---

## 7. Pipeline Execution Scripts

### 7.1 Automated Ingestion Script (`download_and_stage.sh`)
Located in [`infra/primekg_staging/download_and_stage.sh`](file:///Users/prdmohan/ge_spark_workspace/projects/cancer-co-scientist-reusable-graphagents-architectural-kgraph/infra/primekg_staging/download_and_stage.sh):
1. **Resilient Acquisition**: Executes `curl -L -C - --retry 5 --retry-delay 5` against Harvard Dataverse persistent file endpoints. Resumes interrupted downloads automatically.
2. **Integrity Verification**: Computes SHA-256 checksums and file sizes for all downloaded artifacts.
3. **Structured Manifest**: Emits `manifest.json` containing timestamps, file IDs, sizes, and hashes.
4. **Dual Staging**:
   - `gs://${BUCKET}/raw/${TIMESTAMP}/`: Timestamped immutable dump.
   - `gs://${BUCKET}/releases/latest/`: Canonical endpoint for Worker Tier ingestion.

### 7.2 Wrapper Execution Script (`curl_pipeline.sh`)
Located in [`infra/primekg_staging/curl_pipeline.sh`](file:///Users/prdmohan/ge_spark_workspace/projects/cancer-co-scientist-reusable-graphagents-architectural-kgraph/infra/primekg_staging/curl_pipeline.sh):
- Automatically resolves target bucket URL from Terraform outputs or environment variables.

---

## 8. Deployment & Execution Instructions

### Step 1: Provision Staging Infrastructure
```bash
cd infra/primekg_staging
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

### Step 2: Trigger Acquisition Pipeline
To execute the pipeline directly on the high-speed GCE runner VM:
```bash
# Retrieve instance name and zone from Terraform output
RUNNER_VM=$(terraform output -raw gce_instance_name)
ZONE=$(terraform output -raw gce_instance_zone)
BUCKET_URL=$(terraform output -raw gcs_primekg_bucket_url)

# Execute acquisition remotely via gcloud compute ssh
gcloud compute ssh "${RUNNER_VM}" --zone="${ZONE}" --command="
  sudo apt-get update && sudo apt-get install -y curl jq coreutils
  curl -sSL https://raw.githubusercontent.com/prdmohangoogley/cancer-co-scientist-reusable-graphagents-architectural-kgraph/main/infra/primekg_staging/download_and_stage.sh -o /tmp/download_and_stage.sh
  chmod +x /tmp/download_and_stage.sh
  /tmp/download_and_stage.sh '${BUCKET_URL}'
"
```

*Alternatively, execute locally or in Cloud Shell:*
```bash
./infra/primekg_staging/download_and_stage.sh "${BUCKET_URL}"
```

---

## 9. Acceptance Criteria Verification

The milestone is verified when:
1. Terraform successfully initializes, plans, and provisions without permission errors:
   ```bash
   terraform -chdir=infra/primekg_staging validate
   # Output: Success! The configuration is valid.
   ```
2. The GCS landing zone bucket exists in multi-region `US`:
   ```bash
   gcloud storage buckets describe "${BUCKET_URL}" --format="value(location)"
   # Output: US
   ```
3. Staged files are visible in the bucket with matching sizes:
   ```bash
   gcloud storage ls --long "${BUCKET_URL}/releases/latest/"
   ```
   Expected artifacts:
   - `kg.csv` (~982 MB)
   - `edges.csv` (~387 MB)
   - `disease_features.tab` (~114 MB)
   - `drug_features.tab` (~10 MB)
   - `nodes.tab` (~8.9 MB)
   - `manifest.json` (~1 KB)

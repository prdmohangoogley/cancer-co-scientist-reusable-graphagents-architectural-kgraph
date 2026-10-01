# Open Knowledge Format (OKF) Guidelines: PrimeKG & Precision Oncology

## 1. Overview
The Open Knowledge Format (OKF) defines schema invariants, ontology mappings, and serialization standards for biomedical knowledge graphs within the `graphagents` ecosystem.

Our primary precision oncology knowledge graph is derived from **PrimeKG** (Precision Medicine Knowledge Graph), integrating 20+ biomedical databases into a unified, semantically typed graph.

---

## 2. PrimeKG Ontology Specification

### 2.1. Node Types & Identifiers
Every node in the graph must contain a globally unique composite identifier (`type:id`), a canonical name, and domain-specific attributes:

| Node Label | Identifier Prefix | Standard Ontology Source | Example |
| :--- | :--- | :--- | :--- |
| `Gene` / `Protein` | `NCBI:` / `HGNC:` | NCBI Entrez Gene, HGNC | `NCBI:7157` (`TP53`) |
| `Disease` | `MONDO:` | Mondo Disease Ontology | `MONDO:0005070` (`Non-small cell lung carcinoma`) |
| `Drug` | `DRUGBANK:` / `CHEBI:` | DrugBank, ChEBI | `DRUGBANK:DB00530` (`Erlotinib`) |
| `Pathway` | `REACTOME:` / `KEGG:` | Reactome, KEGG Pathways | `REACTOME:R-HSA-5683057` (`MAPK signaling`) |
| `Phenotype` | `HP:` | Human Phenotype Ontology | `HP:0001903` (`Anemia`) |
| `BiologicalProcess` | `GO:` | Gene Ontology | `GO:0008219` (`Cell death`) |
| `MolecularFunction` | `GO:` | Gene Ontology | `GO:0003677` (`DNA binding`) |

### 2.2. Edge Types & Semantics
Edges represent directed, typed relationships with confidence scores and source citations:

| Relationship Label | Source Node | Target Node | Description |
| :--- | :--- | :--- | :--- |
| `TARGETS` | `Drug` | `Gene` | Pharmacological target binding |
| `INDICATION` | `Drug` | `Disease` | Approved therapeutic indication |
| `OFF_LABEL_USE` | `Drug` | `Disease` | Documented off-label clinical application |
| `ASSOCIATED_WITH` | `Gene` | `Disease` | Genetic association / mutation implication |
| `INTERACTS_WITH` | `Gene` | `Gene` | Protein-protein interaction (PPI) |
| `PART_OF_PATHWAY` | `Gene` | `Pathway` | Pathway membership |
| `HAS_PHENOTYPE` | `Disease` | `Phenotype` | Clinical phenotypic presentation |
| `CONTRAINDICATION`| `Drug` | `Disease` | Documented clinical adverse contraindication |

---

## 3. Data Lake & Staging Invariants (DOC-09)
1. **Raw Storage Tier (`infra/datalake`)**:
   - Bucket URI: `gs://<project>-okf-datalake/primekg/raw/`
   - Formats: Immutable compressed archives (`.tar.gz`, `.parquet`, `.csv.gz`).
2. **Staging & Processing (`infra/primekg_staging`)**:
   - GCE High-Throughput curl pipeline instance fetches upstream data releases.
   - Computes SHA256 checksums before staging into Google Cloud Storage.
3. **Serving Tier (`packages/graphagent/iac`)**:
   - Converted to Cloud Spanner Graph Property Graph tables (`Nodes`, `Edges`).
   - Feature tables and high-dimensional embeddings loaded into BigQuery.

---

## 4. Enterprise Architectural Best Practices OKF Corpus

In addition to precision oncology graphs, the repository relies on the **Enterprise Agent Architecture Best Practices OKF Corpus** to bootstrap the remote Guidelines FastMCP server (`gea-agents-arch-guidelines-mcp-server`).

### 4.1. Canonical GCS Storage Location
```text
gs://gea_agent_development_architectural_best_practices_1790796607/okf/
├── MANIFEST.json       # Master inventory (20 documents, 73 Mermaid diagrams, 94 tables)
├── bundle.json         # OKF schema validation rules and domain taxonomies
├── index.md            # Knowledge base index and reference cross-links
├── log.md              # Ingestion log & git commit provenance
├── concepts/           # 20 Foundational Architectural Best Practices (DOC-01 to DOC-20)
└── img/                # Rendered architectural blueprints and visual diagrams
```

### 4.2. Instructions for Replicating into Your Own Project Bucket
To provision the architecture knowledge base in your own GCP project:

```bash
# 1. Create your target knowledge base GCS bucket
gcloud storage buckets create gs://YOUR_TARGET_BUCKET_NAME \
  --project=YOUR_GCP_PROJECT_ID \
  --location=us-central1 \
  --uniform-bucket-level-access

# 2. Dump/sync the entire OKF bundle directly from the source bucket to your bucket
gcloud storage cp --recursive \
  gs://gea_agent_development_architectural_best_practices_1790796607/okf \
  gs://YOUR_TARGET_BUCKET_NAME/

# 3. (Optional) Download locally for offline development or local pipeline inspection
mkdir -p data/okf
gcloud storage cp --recursive \
  gs://gea_agent_development_architectural_best_practices_1790796607/okf \
  ./data/
```

### 4.3. Ingestion into Cloud Spanner Graph & BigQuery
Once copied to your bucket or local filesystem, run the NL2KG Triplification pipeline in `gea-agents-arch-guidelines-mcp-server`:
```bash
# Triplify documents into nodes and labeled relationships
uv run nl2kg-pipeline extract --source-dir ./data/okf/concepts/

# Validate ontology constraints
uv run nl2kg-pipeline validate --input-file build/graph/triples.json

# Load into Cloud Spanner Graph (ArchGuidelinesGraph) and BigQuery
uv run nl2kg-pipeline load --project-id YOUR_GCP_PROJECT_ID
```


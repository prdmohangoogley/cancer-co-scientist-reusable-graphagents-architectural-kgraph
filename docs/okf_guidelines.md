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

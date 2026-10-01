# BigQuery Dataset for PrimeKG Analytics & Vector Embeddings
resource "google_bigquery_dataset" "primekg_analytics" {
  project                     = var.project_id
  dataset_id                  = "primekg_analytics_${var.environment}"
  friendly_name               = "PrimeKG Precision Oncology Analytics"
  description                 = "Analytical storage for high-dimensional omics embeddings, target metrics, and clinical trials"
  location                    = var.region
  default_table_expiration_ms = null

  labels = {
    environment = var.environment
    domain      = "precision-oncology"
    component   = "bigquery-analytics"
    governance  = "gea-arch-guidelines"
  }
}

# BigQuery Table: Disease Features (Phenotypic descriptions, MONDO/UMLS, clinical guidelines)
resource "google_bigquery_table" "disease_features" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.primekg_analytics.dataset_id
  table_id   = "disease_features"

  schema = <<-EOF
  [
    {"name": "disease_id", "type": "STRING", "mode": "REQUIRED", "description": "Disease identifier (e.g. MONDO or UMLS)"},
    {"name": "disease_name", "type": "STRING", "mode": "REQUIRED", "description": "Canonical disease name"},
    {"name": "mondo_id", "type": "STRING", "mode": "NULLABLE", "description": "MONDO ontology ID"},
    {"name": "umls_cui", "type": "STRING", "mode": "NULLABLE", "description": "UMLS Concept Unique Identifier"},
    {"name": "phenotypic_features", "type": "STRING", "mode": "NULLABLE", "description": "Associated clinical phenotypes"},
    {"name": "clinical_description", "type": "STRING", "mode": "NULLABLE", "description": "Clinical guidelines text"},
    {"name": "updated_at", "type": "TIMESTAMP", "mode": "NULLABLE", "description": "Ingestion timestamp"}
  ]
  EOF

  deletion_protection = false
}

# BigQuery Table: Drug Features (Molecular weight, SMILES, indications, pharmacodynamics)
resource "google_bigquery_table" "drug_features" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.primekg_analytics.dataset_id
  table_id   = "drug_features"

  schema = <<-EOF
  [
    {"name": "drug_id", "type": "STRING", "mode": "REQUIRED", "description": "DrugBank ID or PubChem CID"},
    {"name": "drug_name", "type": "STRING", "mode": "REQUIRED", "description": "Canonical drug name"},
    {"name": "indication", "type": "STRING", "mode": "NULLABLE", "description": "Approved therapeutic indication"},
    {"name": "pharmacodynamics", "type": "STRING", "mode": "NULLABLE", "description": "Mechanism of action summary"},
    {"name": "smiles", "type": "STRING", "mode": "NULLABLE", "description": "Chemical canonical SMILES string"},
    {"name": "molecular_weight", "type": "FLOAT64", "mode": "NULLABLE", "description": "Molecular weight in g/mol"},
    {"name": "updated_at", "type": "TIMESTAMP", "mode": "NULLABLE", "description": "Ingestion timestamp"}
  ]
  EOF

  deletion_protection = false
}

# BigQuery Table: Node Embeddings (Vector Search)
resource "google_bigquery_table" "node_embeddings" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.primekg_analytics.dataset_id
  table_id   = "node_embeddings"

  time_partitioning {
    type = "DAY"
  }

  schema = <<-EOF
  [
    {"name": "node_id", "type": "STRING", "mode": "REQUIRED", "description": "Canonical node ID"},
    {"name": "label", "type": "STRING", "mode": "REQUIRED", "description": "Entity type (Gene, Disease, etc.)"},
    {"name": "name", "type": "STRING", "mode": "REQUIRED", "description": "Canonical entity name"},
    {"name": "embedding", "type": "FLOAT64", "mode": "REPEATED", "description": "768-dim text-embedding-004 representation"},
    {"name": "updated_at", "type": "TIMESTAMP", "mode": "REQUIRED", "description": "Commit timestamp"}
  ]
  EOF

  deletion_protection = false
}

# BigQuery Dataset for PrimeKG Analytics & Vector Embeddings
resource "google_bigquery_dataset" "primekg_analytics" {
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

# BigQuery Table: Node Embeddings (Vector Search)
resource "google_bigquery_table" "node_embeddings" {
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

# BigQuery Table: Clinical Evidence & Druggability Scores
resource "google_bigquery_table" "clinical_evidence" {
  dataset_id = google_bigquery_dataset.primekg_analytics.dataset_id
  table_id   = "clinical_evidence"

  schema = <<-EOF
  [
    {"name": "evidence_id", "type": "STRING", "mode": "REQUIRED"},
    {"name": "source_node_id", "type": "STRING", "mode": "REQUIRED"},
    {"name": "target_node_id", "type": "STRING", "mode": "REQUIRED"},
    {"name": "evidence_source", "type": "STRING", "mode": "REQUIRED"},
    {"name": "pubmed_id", "type": "STRING", "mode": "NULLABLE"},
    {"name": "clinical_phase", "type": "STRING", "mode": "NULLABLE"},
    {"name": "druggability_tier", "type": "STRING", "mode": "NULLABLE"},
    {"name": "score", "type": "FLOAT64", "mode": "REQUIRED"}
  ]
  EOF

  deletion_protection = false
}

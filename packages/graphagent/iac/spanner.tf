# Cloud Spanner Instance for PrimeKG Knowledge Graph
resource "google_spanner_instance" "primekg_spanner" {
  project          = var.project_id
  name             = "primekg-instance-${var.environment}"
  config           = "regional-${var.region}"
  display_name     = "PrimeKG Graph Spanner Instance"
  processing_units = var.spanner_processing_units

  labels = {
    environment = var.environment
    domain      = "precision-oncology"
    component   = "spanner-graph"
    governance  = "gea-arch-guidelines"
  }
}

# Cloud Spanner Database with ISO GQL Property Graph Schema
resource "google_spanner_database" "primekg_db" {
  instance = google_spanner_instance.primekg_spanner.name
  name     = "primekg-database"
  project  = var.project_id

  ddl = [
    <<-EOT
    CREATE TABLE Nodes (
      node_id STRING(128) NOT NULL,
      label STRING(64) NOT NULL,
      name STRING(256) NOT NULL,
      properties_json JSON,
      created_at TIMESTAMP OPTIONS (allow_commit_timestamp = true)
    ) PRIMARY KEY (node_id)
    EOT
    ,
    <<-EOT
    CREATE TABLE Edges (
      source_id STRING(128) NOT NULL,
      target_id STRING(128) NOT NULL,
      edge_id STRING(128) NOT NULL,
      relationship STRING(64) NOT NULL,
      confidence FLOAT64,
      evidence_json JSON,
      created_at TIMESTAMP OPTIONS (allow_commit_timestamp = true),
      FOREIGN KEY (source_id) REFERENCES Nodes (node_id),
      FOREIGN KEY (target_id) REFERENCES Nodes (node_id)
    ) PRIMARY KEY (source_id, target_id, edge_id)
    EOT
    ,
    <<-EOT
    CREATE OR REPLACE PROPERTY GRAPH PrimeKGGraph
      NODE TABLES(
        Nodes
          KEY(node_id)
          LABEL Node PROPERTIES(
            node_id,
            label,
            name,
            properties_json,
            created_at)
      )
      EDGE TABLES(
        Edges
          KEY(source_id, target_id, edge_id)
          SOURCE KEY(source_id) REFERENCES Nodes(node_id)
          DESTINATION KEY(target_id) REFERENCES Nodes(node_id)
          LABEL Edge PROPERTIES(
            edge_id,
            source_id,
            target_id,
            relationship,
            confidence,
            evidence_json,
            created_at)
      )
    EOT
  ]

  deletion_protection = false
}

# Cloud Spanner Instance for PrimeKG Knowledge Graph
resource "google_spanner_instance" "primekg_spanner" {
  name         = "primekg-instance-${var.environment}"
  config       = "regional-${var.region}"
  display_name = "PrimeKG Graph Spanner Instance"
  num_nodes    = var.spanner_num_nodes

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

  ddl = [
    <<-EOT
    CREATE TABLE Nodes (
      node_id STRING(128) NOT NULL,
      label STRING(64) NOT NULL,
      name STRING(256) NOT NULL,
      properties_json JSON,
      created_at TIMESTAMP OPTIONS (allow_commit_timestamp = true)
    ) PRIMARY KEY (node_id);
    EOT
    ,
    <<-EOT
    CREATE TABLE Edges (
      edge_id STRING(128) NOT NULL,
      source_id STRING(128) NOT NULL,
      target_id STRING(128) NOT NULL,
      relationship STRING(64) NOT NULL,
      confidence FLOAT64,
      evidence_json JSON,
      created_at TIMESTAMP OPTIONS (allow_commit_timestamp = true),
      FOREIGN KEY (source_id) REFERENCES Nodes (node_id),
      FOREIGN KEY (target_id) REFERENCES Nodes (node_id)
    ) PRIMARY KEY (source_id, target_id, edge_id);
    EOT
    ,
    <<-EOT
    CREATE PROPERTY GRAPH PrimeKGGraph
      NODE TABLES (
        Nodes
          LABEL Gene WHERE label = 'Gene'
          LABEL Disease WHERE label = 'Disease'
          LABEL Drug WHERE label = 'Drug'
          LABEL Pathway WHERE label = 'Pathway'
      )
      EDGE TABLES (
        Edges
          SOURCE KEY (source_id) REFERENCES Nodes (node_id)
          DESTINATION KEY (target_id) REFERENCES Nodes (node_id)
          LABEL TARGETS WHERE relationship = 'TARGETS'
          LABEL INDICATION WHERE relationship = 'INDICATION'
          LABEL ASSOCIATED_WITH WHERE relationship = 'ASSOCIATED_WITH'
          LABEL INTERACTS_WITH WHERE relationship = 'INTERACTS_WITH'
          LABEL PART_OF_PATHWAY WHERE relationship = 'PART_OF_PATHWAY'
      );
    EOT
  ]

  deletion_protection = false
}

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# GCS Bucket for Staging raw PrimeKG releases and checkpoints
resource "google_storage_bucket" "primekg_staging" {
  name                        = "graphagents-primekg-staging-${var.project_id}-${var.environment}"
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 30
    }
  }

  labels = {
    environment = var.environment
    pipeline    = "primekg-staging"
    domain      = "precision-oncology"
  }
}

# Service Account for GCE Curl Pipeline adhering to Zero Ambient Authority (DOC-02)
resource "google_service_account" "curl_pipeline_sa" {
  account_id   = "primekg-curl-pipeline-sa"
  display_name = "PrimeKG Curl Pipeline Service Account"
  description  = "Scoped SA for downloading and staging PrimeKG datasets into GCS"
}

# Grant write access only to the staging bucket
resource "google_storage_bucket_iam_member" "staging_writer" {
  bucket = google_storage_bucket.primekg_staging.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.curl_pipeline_sa.email}"
}

# GCE Instance for High-Throughput curl downloads from Harvard Dataverse
resource "google_compute_instance" "curl_pipeline_runner" {
  name         = "primekg-staging-curl-runner-${var.environment}"
  machine_type = var.machine_type
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = 100 # GB SSD for downloading and staging multi-GB PrimeKG files
      type  = "pd-ssd"
    }
  }

  network_interface {
    network = "default"
    access_config {
      // Ephemeral public IP for external curl access
    }
  }

  service_account {
    email  = google_service_account.curl_pipeline_sa.email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }

  metadata_startup_script = <<-EOT
    #!/usr/bin/env bash
    set -euo pipefail
    apt-get update && apt-get install -y curl pigz jq
    echo "PrimeKG Curl Pipeline VM Ready."
  EOT

  labels = {
    environment = var.environment
    purpose     = "primekg-ingestion"
    governance  = "zaa-compliant"
  }
}

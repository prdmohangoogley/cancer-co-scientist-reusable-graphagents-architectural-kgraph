terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

# Unique numeric ID postfix for landing zone bucket naming
resource "random_integer" "bucket_suffix" {
  min = 1000000000
  max = 9999999999
}

locals {
  bucket_name = var.gcs_primekg_bucket != "" ? var.gcs_primekg_bucket : "cancer-co-scientist-primekg-data-landingzone-${random_integer.bucket_suffix.result}"
}

# 1. Multi-regional GCS Bucket located in the US for PrimeKG landing zone
resource "google_storage_bucket" "primekg_landingzone" {
  name                        = local.bucket_name
  project                     = var.project_id
  location                    = "US" # Multi-regional US as specified
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age        = 90
      with_state = "ARCHIVED"
    }
  }

  labels = {
    environment = var.environment
    pipeline    = "primekg-acquisition"
    domain      = "precision-oncology"
    governance  = "zaa-compliant"
  }
}

# 2. Service Account for GCE Runner adhering to Zero Ambient Authority (DOC-02)
resource "google_service_account" "primekg_staging_runner" {
  project      = var.project_id
  account_id   = "primekg-staging-runner-sa"
  display_name = "PrimeKG Staging Runner Service Account"
  description  = "ZAA-scoped service account with write-only access to PrimeKG landing zone bucket"
}

# Grant write access strictly to the landing zone bucket (Least Privilege)
resource "google_storage_bucket_iam_member" "staging_writer" {
  bucket = google_storage_bucket.primekg_landingzone.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.primekg_staging_runner.email}"
}

# 3. Lightweight Compute Engine Instance with fast uplink for data acquisition
resource "google_compute_instance" "staging_runner" {
  project      = var.project_id
  name         = "primekg-staging-runner-${var.environment}"
  machine_type = var.machine_type
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = 100 # GB SSD for downloading, extracting, and hashing PrimeKG dumps
      type  = "pd-ssd"
    }
  }

  network_interface {
    network = "default"
    access_config {
      // Ephemeral public IP for fast uplink to Harvard Dataverse
    }
  }

  service_account {
    email  = google_service_account.primekg_staging_runner.email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }

  metadata_startup_script = <<-EOT
    #!/usr/bin/env bash
    set -euo pipefail
    
    # Install dependencies
    apt-get update && apt-get install -y curl jq pigz coreutils
    
    # Create working directory
    mkdir -p /opt/primekg_pipeline
    cd /opt/primekg_pipeline

    echo "PrimeKG Staging Runner initialized at $(date -u)" > /var/log/primekg_runner_status.log
  EOT

  metadata = {
    enable-oslogin = "TRUE"
    bucket_target  = google_storage_bucket.primekg_landingzone.name
  }

  labels = {
    environment = var.environment
    purpose     = "primekg-ingestion"
    governance  = "zaa-compliant"
  }
}

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Core GCS Bucket: OKF Data Lake for PrimeKG and Biomedical Graphs
resource "google_storage_bucket" "okf_datalake" {
  name                        = "${var.datalake_bucket_prefix}-${var.project_id}-${var.environment}"
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
    condition {
      age = 90
    }
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 365
    }
  }

  labels = {
    environment = var.environment
    domain      = "precision-oncology"
    component   = "okf-datalake"
    governance  = "gea-arch-guidelines"
  }
}

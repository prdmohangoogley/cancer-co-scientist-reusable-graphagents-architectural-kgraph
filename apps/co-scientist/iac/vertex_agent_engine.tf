# Vertex AI Reasoning Engine & Gemini Enterprise Agent Provisioning (Spec 09)
# Governed by DOC-01, DOC-02 (ZAA), DOC-03 (A2UI), DOC-08, DOC-09

# GCS Bucket for Staging Vertex AI Reasoning Engine Artifacts & Pickled Graph Models
resource "google_storage_bucket" "vertex_agent_staging" {
  name                        = "${var.project_id}-vertex-agent-staging"
  location                    = var.region
  project                     = var.project_id
  force_destroy               = false
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    tier        = "orchestrator"
    application = "cancer-co-scientist"
    environment = var.environment
  }
}

# Grant Vertex AI Service Agent and Orchestrator SA Access to Agent Staging Bucket
resource "google_storage_bucket_iam_member" "orchestrator_staging_admin" {
  bucket = google_storage_bucket.vertex_agent_staging.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

# IAM Role: Vertex AI User for Lead Orchestrator
resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

# IAM Role: Cloud Trace Agent for Distributed Spans (DOC-01)
resource "google_project_iam_member" "trace_agent" {
  project = var.project_id
  role    = "roles/cloudtrace.agent"
  member  = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

# IAM Role: Cloud Monitoring Metric Writer (DOC-01)
resource "google_project_iam_member" "monitoring_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

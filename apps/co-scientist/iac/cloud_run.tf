# Dedicated Service Account for Co-Scientist Orchestrator (DOC-02: Zero Ambient Authority)
resource "google_service_account" "orchestrator_sa" {
  account_id   = "co-scientist-orchestrator-sa"
  display_name = "Cancer Co-Scientist Orchestrator Service Account"
  description  = "Least-privilege SA for executing ADK orchestration and Spanner/BigQuery queries"
}

# Grant Spanner Graph Database Reader
resource "google_project_iam_member" "spanner_reader" {
  project = var.project_id
  role    = "roles/spanner.databaseReader"
  member  = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

# Grant BigQuery Data Viewer & User
resource "google_project_iam_member" "bq_viewer" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

resource "google_project_iam_member" "bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

# Cloud Run Service: Lead Orchestrator Backend
resource "google_cloud_run_v2_service" "orchestrator_service" {
  name     = "cancer-co-scientist-orchestrator-${var.environment}"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.orchestrator_sa.email

    containers {
      image = var.orchestrator_image

      resources {
        limits = {
          cpu    = "2"
          memory = "4Gi"
        }
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name  = "GCP_PROJECT"
        value = var.project_id
      }
      env {
        name  = "ARCH_GUIDELINES_MCP_URL"
        value = "https://gea-guidelines-mcp-${var.project_id}.run.app/sse"
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        initial_delay_seconds = 5
        period_seconds        = 10
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        period_seconds = 15
      }
    }

    scaling {
      min_instance_count = 0 # Scale to zero (DOC-03)
      max_instance_count = 10
    }
  }

  labels = {
    tier        = "orchestrator"
    application = "cancer-co-scientist"
    environment = var.environment
  }
}

# Cloud Run Service: A2UI Web Client
resource "google_cloud_run_v2_service" "ui_service" {
  name     = "cancer-co-scientist-ui-${var.environment}"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = var.ui_image

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }
  }

  labels = {
    tier        = "ui"
    application = "cancer-co-scientist"
    environment = var.environment
  }
}

# Allow unauthenticated access to UI frontend
resource "google_cloud_run_v2_service_iam_member" "ui_public_access" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.ui_service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

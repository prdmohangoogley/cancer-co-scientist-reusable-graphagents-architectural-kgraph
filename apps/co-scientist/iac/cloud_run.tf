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
      env {
        name  = "JWT_SECRET_KEY"
        value = var.jwt_secret_key
      }
      env {
        name  = "OIDC_ISSUER"
        value = var.oidc_issuer
      }
      env {
        name  = "SPANNER_DATABASE"
        value = var.spanner_database
      }
      env {
        name  = "BQ_DATASET"
        value = var.bq_dataset
      }
      env {
        name  = "ENABLE_MEMORY_BANK"
        value = var.enable_memory_bank
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

# Cloud Armor Security Policy for API Protection & Rate Limiting (DOC-02: ZAA)
resource "google_compute_security_policy" "cloud_armor_policy" {
  name        = "cancer-co-scientist-armor-${var.environment}"
  project     = var.project_id
  description = "Enterprise Cloud Armor security policy enforcing rate limiting and WAF (DOC-02)"

  # Default rule: allow traffic
  rule {
    action   = "allow"
    priority = "2147483647"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default allow rule"
  }

  # Rate limiting rule: 60 requests per minute per IP
  rule {
    action   = "throttle"
    priority = "1000"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"
      rate_limit_threshold {
        count        = 60
        interval_sec = 60
      }
    }
    description = "Rate limit at 60 requests per minute per IP"
  }

  # OWASP Top 10 ModSecurity Preconfigured Core Rule Set (SQLi, XSS, Scanner detection)
  rule {
    action   = "deny(403)"
    priority = "2000"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('sqli-v33-stable') || evaluatePreconfiguredExpr('xss-v33-stable') || evaluatePreconfiguredExpr('scannerdetection-v33-stable')"
      }
    }
    description = "OWASP CRS protection against SQLi, XSS, and vulnerability scanners"
  }
}


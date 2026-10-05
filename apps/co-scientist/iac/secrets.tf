# Google Cloud Secret Manager configuration for Zero Ambient Authority (DOC-02)

resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "jwt-secret-key"

  replication {
    auto {}
  }

  labels = {
    tier        = "security"
    governance  = "zaa-doc-02"
    application = "cancer-co-scientist"
    managed_by  = "terraform"
  }
}

resource "google_secret_manager_secret_iam_member" "runtime_jwt_secret_accessor" {
  secret_id = google_secret_manager_secret.jwt_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:agent-runtime-sa@fivedaysai-prd-sandbox-317383.iam.gserviceaccount.com"
}

output "orchestrator_uri" {
  description = "The Cloud Run URL of the Lead Orchestrator service"
  value       = google_cloud_run_v2_service.orchestrator_service.uri
}

output "ui_uri" {
  description = "The Cloud Run URL of the Cancer Co-Scientist UI"
  value       = google_cloud_run_v2_service.ui_service.uri
}

output "orchestrator_service_account" {
  description = "Service account running the orchestrator"
  value       = google_service_account.orchestrator_sa.email
}

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

output "cloud_armor_security_policy_id" {
  description = "The ID of the Cloud Armor security policy"
  value       = google_compute_security_policy.cloud_armor_policy.id
}


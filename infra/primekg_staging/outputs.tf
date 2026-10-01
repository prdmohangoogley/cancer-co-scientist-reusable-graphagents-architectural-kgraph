output "staging_bucket_name" {
  description = "Name of the PrimeKG staging GCS bucket"
  value       = google_storage_bucket.primekg_staging.name
}

output "staging_vm_name" {
  description = "Name of the GCE curl pipeline instance"
  value       = google_compute_instance.curl_pipeline_runner.name
}

output "service_account_email" {
  description = "Service Account email used for curl pipeline"
  value       = google_service_account.curl_pipeline_sa.email
}

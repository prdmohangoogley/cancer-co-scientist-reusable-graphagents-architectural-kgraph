output "gcs_primekg_bucket_name" {
  description = "Name of the provisioned Multi-Regional US PrimeKG Landing Zone GCS Bucket"
  value       = google_storage_bucket.primekg_landingzone.name
}

output "gcs_primekg_bucket_url" {
  description = "GCS URL of the provisioned Landing Zone bucket"
  value       = "gs://${google_storage_bucket.primekg_landingzone.name}"
}

output "service_account_email" {
  description = "Email of the ZAA-scoped GCE pipeline runner service account"
  value       = google_service_account.primekg_staging_runner.email
}

output "gce_instance_name" {
  description = "Name of the GCE pipeline runner instance"
  value       = google_compute_instance.staging_runner.name
}

output "gce_instance_zone" {
  description = "Zone of the GCE pipeline runner instance"
  value       = google_compute_instance.staging_runner.zone
}

output "staging_pipeline_command" {
  description = "Example command to execute data acquisition remotely on the GCE runner via IAP tunnel"
  value       = "gcloud compute ssh ${google_compute_instance.staging_runner.name} --zone=${google_compute_instance.staging_runner.zone} --tunnel-through-iap --command='bash /opt/primekg_pipeline/download_and_stage.sh gs://${google_storage_bucket.primekg_landingzone.name}'"
}

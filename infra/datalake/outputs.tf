output "datalake_bucket_name" {
  description = "Name of the created OKF Data Lake GCS bucket"
  value       = google_storage_bucket.okf_datalake.name
}

output "datalake_bucket_url" {
  description = "Direct GCS URI for the Data Lake bucket"
  value       = google_storage_bucket.okf_datalake.url
}

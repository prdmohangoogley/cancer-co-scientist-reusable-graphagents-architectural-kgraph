output "spanner_instance_id" {
  description = "Cloud Spanner Instance ID for PrimeKG"
  value       = google_spanner_instance.primekg_spanner.name
}

output "spanner_database_id" {
  description = "Cloud Spanner Database ID"
  value       = google_spanner_database.primekg_db.name
}

output "bigquery_dataset_id" {
  description = "BigQuery Dataset ID for PrimeKG Analytics"
  value       = google_bigquery_dataset.primekg_analytics.dataset_id
}

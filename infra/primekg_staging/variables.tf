variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
  default     = "fivedaysai-prd-sandbox-317383"
}

variable "gcs_primekg_bucket" {
  description = "Custom GCS bucket name for PrimeKG landing zone. If empty, defaults to cancer-co-scientist-primekg-data-landingzone-<uuid>."
  type        = string
  default     = ""
}

variable "region" {
  description = "GCP Region for staging resources (compute instance)"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP Zone for the GCE Curl Pipeline instance"
  type        = string
  default     = "us-central1-a"
}

variable "machine_type" {
  description = "Compute Engine instance type for high-throughput downloads"
  type        = string
  default     = "e2-standard-2"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

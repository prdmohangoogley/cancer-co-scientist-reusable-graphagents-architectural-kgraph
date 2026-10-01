variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region for Data Lake buckets"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "datalake_bucket_prefix" {
  description = "Prefix name for the OKF Data Lake GCS bucket"
  type        = string
  default     = "graphagents-okf-datalake"
}

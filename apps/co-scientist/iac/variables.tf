variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region for Cloud Run deployment"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "orchestrator_image" {
  description = "Container image for Co-Scientist Orchestrator service"
  type        = string
  default     = "gcr.io/google-samples/cancer-co-scientist-orchestrator:latest"
}

variable "ui_image" {
  description = "Container image for Cancer Co-Scientist UI frontend"
  type        = string
  default     = "gcr.io/google-samples/cancer-co-scientist-ui:latest"
}

variable "jwt_secret_key" {
  description = "HMAC secret key for signing and verifying JWT tokens (DOC-02 ZAA)"
  type        = string
  sensitive   = true
  default     = "dev-insecure-secret-key-change-in-production-32bytes"
}

variable "oidc_issuer" {
  description = "OIDC Issuer URL for identity federation"
  type        = string
  default     = "https://auth.cancer-coscientist.app"
}

variable "spanner_database" {
  description = "Cloud Spanner database name for graph and session persistence"
  type        = string
  default     = "primekg-database"
}

variable "bq_dataset" {
  description = "BigQuery analytics dataset name"
  type        = string
  default     = "primekg_analytics_dev"
}

variable "enable_memory_bank" {
  description = "Enable progressive disclosure memory bank engine"
  type        = string
  default     = "true"
}


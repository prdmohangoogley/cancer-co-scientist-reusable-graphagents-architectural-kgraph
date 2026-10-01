variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
  default     = "fivedaysai-prd-sandbox-317383"
}

variable "region" {
  description = "Spanner and BigQuery region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "spanner_processing_units" {
  description = "Processing units for Spanner instance (100 PU = 0.1 node, cost-effective for dev)"
  type        = number
  default     = 100
}

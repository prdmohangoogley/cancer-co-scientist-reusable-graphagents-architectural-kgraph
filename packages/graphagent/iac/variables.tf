variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
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

variable "spanner_num_nodes" {
  description = "Number of compute nodes for Spanner instance"
  type        = number
  default     = 1
}

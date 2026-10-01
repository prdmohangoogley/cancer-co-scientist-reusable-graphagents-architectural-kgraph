variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region for staging resources"
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
  default     = "e2-standard-4"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

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

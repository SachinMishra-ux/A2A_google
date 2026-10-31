# ==============================================================================
# Terraform Blueprint: Production Deployment on Google Cloud Platform (GCP)
# Services: Cloud Run, Secret Manager, Serverless VPC Access, Cloud Load Balancer
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

variable "project_id" {
  type        = string
  description = "Google Cloud Project ID"
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "Target GCP Region"
}

variable "gemini_api_key" {
  type        = string
  sensitive   = true
  description = "Google Gemini API Key for autonomous agents"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Secret Manager for API Key Security
resource "google_secret_manager_secret" "gemini_key" {
  secret_id = "a2a-gemini-api-key"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "gemini_key_val" {
  secret      = google_secret_manager_secret.gemini_key.id
  secret_data = var.gemini_api_key
}

# 2. Service Account for A2A Runtime
resource "google_service_account" "a2a_sa" {
  account_id   = "a2a-agent-runtime-sa"
  display_name = "Service Account for A2A Multi-Agent System"
}

resource "google_secret_manager_secret_iam_member" "sa_secret_access" {
  secret_id = google_secret_manager_secret.gemini_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.a2a_sa.email}"
}

# 3. Google Cloud Run: Unified Multi-Agent Gateway Service
resource "google_cloud_run_v2_service" "a2a_gateway" {
  name     = "a2a-multiagent-gateway"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.a2a_sa.email
    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }
    containers {
      image = "gcr.io/${var.project_id}/a2a-system:latest"
      ports {
        container_port = 8000
      }
      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }
      env {
        name  = "PORT"
        value = "8000"
      }
      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_key.secret_id
            version = "latest"
          }
        }
      }
    }
  }
}

# 4. Allow Unauthenticated Public Access (Protected by OAuth2 / A2A Tokens at Gateway)
resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.a2a_gateway.location
  service  = google_cloud_run_v2_service.a2a_gateway.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "a2a_gateway_url" {
  value       = google_cloud_run_v2_service.a2a_gateway.uri
  description = "Public URL for A2A Protocol Gateway & Inspector UI"
}

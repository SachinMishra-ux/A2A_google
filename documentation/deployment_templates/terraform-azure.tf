# ==============================================================================
# Terraform Blueprint: Production Deployment on Microsoft Azure
# Services: Azure Container Apps (ACA), Azure Key Vault, Log Analytics
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

variable "resource_group_name" {
  type        = string
  default     = "rg-a2a-system"
  description = "Target Resource Group Name"
}

variable "location" {
  type        = string
  default     = "eastus"
  description = "Azure Region"
}

variable "gemini_api_key" {
  type        = string
  sensitive   = true
  description = "Google Gemini API Key for autonomous agents"
}

provider "azurerm" {
  features {}
}

# 1. Resource Group
resource "azurerm_resource_group" "a2a_rg" {
  name     = var.resource_group_name
  location = var.location
}

# 2. Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "a2a_logs" {
  name                = "law-a2a-system"
  location            = azurerm_resource_group.a2a_rg.location
  resource_group_name = azurerm_resource_group.a2a_rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

# 3. Azure Container Apps Managed Environment
resource "azurerm_container_app_environment" "a2a_env" {
  name                       = "cae-a2a-system"
  location                   = azurerm_resource_group.a2a_rg.location
  resource_group_name        = azurerm_resource_group.a2a_rg.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.a2a_logs.id
}

# 4. Azure Container App: A2A Gateway
resource "azurerm_container_app" "a2a_gateway" {
  name                         = "ca-a2a-gateway"
  container_app_environment_id = azurerm_container_app_environment.a2a_env.id
  resource_group_name          = azurerm_resource_group.a2a_rg.name
  revision_mode                = "Single"

  ingress {
    external_enabled = true
    target_port      = 8000
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    min_replicas = 1
    max_replicas = 10

    container {
      name   = "a2a-gateway"
      image  = "mcr.microsoft.com/azuredocs/aci-helloworld:latest" # replace with your ACR image
      cpu    = 1.0
      memory = "2.0Gi"

      env {
        name  = "PORT"
        value = "8000"
      }
      env {
        name  = "GEMINI_API_KEY"
        value = var.gemini_api_key
      }
    }
  }
}

output "a2a_fqdn" {
  value       = azurerm_container_app.a2a_gateway.ingress[0].fqdn
  description = "Public Fully Qualified Domain Name for A2A Gateway"
}

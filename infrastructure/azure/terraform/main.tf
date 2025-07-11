# ========================================
# Azure OpenAI Service Integration
# Infrastructure as Code for Yuyama RAG System
# ========================================

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
  }
}

# Data source for existing resource group
data "azurerm_resource_group" "yuyama" {
  name = "yuyama"
}

# Data source for current client
data "azurerm_client_config" "current" {}

# ========================================
# Azure OpenAI Service
# ========================================

resource "azurerm_cognitive_account" "openai" {
  name                = "yuyama-openai"
  location            = data.azurerm_resource_group.yuyama.location
  resource_group_name = data.azurerm_resource_group.yuyama.name
  kind                = "OpenAI"
  sku_name            = "S0"

  custom_subdomain_name = "yuyama-openai"
  public_network_access_enabled = true

  tags = {
    Environment = "production"
    Project     = "yuyama-rag"
    Service     = "openai"
  }
}

# GPT-4 Deployment
resource "azurerm_cognitive_deployment" "gpt4" {
  name                 = "gpt-4"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "gpt-4"
    version = "1106-Preview"
  }

  scale {
    type = "Standard"
  }

  depends_on = [azurerm_cognitive_account.openai]
}

# GPT-4 Vision Deployment for Multimodal RAG
resource "azurerm_cognitive_deployment" "gpt4_vision" {
  name                 = "gpt-4-vision"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "gpt-4"
    version = "vision-preview"
  }

  scale {
    type = "Standard"
  }

  depends_on = [azurerm_cognitive_account.openai]
}

# Text Embedding Deployment
resource "azurerm_cognitive_deployment" "text_embedding" {
  name                 = "text-embedding-ada-002"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "text-embedding-ada-002"
    version = "2"
  }

  scale {
    type = "Standard"
  }

  depends_on = [azurerm_cognitive_account.openai]
}

# ========================================
# Azure AI Search Service
# ========================================

resource "azurerm_search_service" "ai_search" {
  name                = "yuyama-ai-search"
  resource_group_name = data.azurerm_resource_group.yuyama.name
  location            = data.azurerm_resource_group.yuyama.location
  sku                 = "standard"
  replica_count       = 1
  partition_count     = 1

  public_network_access_enabled = true
  allowed_ips = []

  tags = {
    Environment = "production"
    Project     = "yuyama-rag"
    Service     = "search"
  }
}

# ========================================
# Azure Key Vault for Secure Secret Management
# ========================================

resource "azurerm_key_vault" "yuyama_vault" {
  name                        = "yuyama-keyvault"
  location                    = data.azurerm_resource_group.yuyama.location
  resource_group_name         = data.azurerm_resource_group.yuyama.name
  enabled_for_disk_encryption = true
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false
  sku_name                    = "standard"

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    key_permissions = [
      "Get",
      "List",
      "Create",
      "Delete",
      "Update",
      "Purge",
      "Recover"
    ]

    secret_permissions = [
      "Get",
      "List",
      "Set",
      "Delete",
      "Purge",
      "Recover"
    ]

    certificate_permissions = [
      "Get",
      "List",
      "Create",
      "Delete",
      "Update",
      "Purge",
      "Recover"
    ]
  }

  tags = {
    Environment = "production"
    Project     = "yuyama-rag"
    Service     = "keyvault"
  }
}

# Store OpenAI API Key in Key Vault
resource "azurerm_key_vault_secret" "openai_api_key" {
  name         = "openai-api-key"
  value        = azurerm_cognitive_account.openai.primary_access_key
  key_vault_id = azurerm_key_vault.yuyama_vault.id

  depends_on = [azurerm_key_vault.yuyama_vault]
}

# Store OpenAI Endpoint in Key Vault
resource "azurerm_key_vault_secret" "openai_endpoint" {
  name         = "openai-endpoint"
  value        = azurerm_cognitive_account.openai.endpoint
  key_vault_id = azurerm_key_vault.yuyama_vault.id

  depends_on = [azurerm_key_vault.yuyama_vault]
}

# Store AI Search Admin Key in Key Vault
resource "azurerm_key_vault_secret" "search_admin_key" {
  name         = "search-admin-key"
  value        = azurerm_search_service.ai_search.primary_key
  key_vault_id = azurerm_key_vault.yuyama_vault.id

  depends_on = [azurerm_key_vault.yuyama_vault]
}

# Store AI Search Endpoint in Key Vault
resource "azurerm_key_vault_secret" "search_endpoint" {
  name         = "search-endpoint"
  value        = "https://${azurerm_search_service.ai_search.name}.search.windows.net"
  key_vault_id = azurerm_key_vault.yuyama_vault.id

  depends_on = [azurerm_key_vault.yuyama_vault]
}

# ========================================
# Application Insights for Monitoring
# ========================================

resource "azurerm_application_insights" "yuyama" {
  name                = "yuyama-appinsights"
  location            = data.azurerm_resource_group.yuyama.location
  resource_group_name = data.azurerm_resource_group.yuyama.name
  application_type    = "web"

  tags = {
    Environment = "production"
    Project     = "yuyama-rag"
    Service     = "monitoring"
  }
}

# Store Application Insights Connection String in Key Vault
resource "azurerm_key_vault_secret" "appinsights_connection_string" {
  name         = "appinsights-connection-string"
  value        = azurerm_application_insights.yuyama.connection_string
  key_vault_id = azurerm_key_vault.yuyama_vault.id

  depends_on = [azurerm_key_vault.yuyama_vault]
}

# ========================================
# Managed Identity for App Services
# ========================================

resource "azurerm_user_assigned_identity" "yuyama_identity" {
  name                = "yuyama-managed-identity"
  resource_group_name = data.azurerm_resource_group.yuyama.name
  location            = data.azurerm_resource_group.yuyama.location

  tags = {
    Environment = "production"
    Project     = "yuyama-rag"
    Service     = "identity"
  }
}

# Grant Managed Identity access to Key Vault
resource "azurerm_key_vault_access_policy" "app_identity" {
  key_vault_id = azurerm_key_vault.yuyama_vault.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_user_assigned_identity.yuyama_identity.principal_id

  secret_permissions = [
    "Get",
    "List"
  ]

  depends_on = [azurerm_user_assigned_identity.yuyama_identity]
}

# ========================================
# Storage Account for Blob Storage
# ========================================

resource "azurerm_storage_account" "yuyama_storage" {
  name                     = "yuyamablob"
  resource_group_name      = data.azurerm_resource_group.yuyama.name
  location                 = data.azurerm_resource_group.yuyama.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"

  blob_properties {
    cors_rule {
      allowed_headers    = ["*"]
      allowed_methods    = ["GET", "HEAD", "PUT", "POST"]
      allowed_origins    = ["*"]
      exposed_headers    = ["*"]
      max_age_in_seconds = 86400
    }
  }

  tags = {
    Environment = "production"
    Project     = "yuyama-rag"
    Service     = "storage"
  }
}

# Create containers for different document types
resource "azurerm_storage_container" "documents" {
  name                  = "documents"
  storage_account_name  = azurerm_storage_account.yuyama_storage.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "images" {
  name                  = "images"
  storage_account_name  = azurerm_storage_account.yuyama_storage.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "audio" {
  name                  = "audio"
  storage_account_name  = azurerm_storage_account.yuyama_storage.name
  container_access_type = "private"
}

# Store Storage Account Connection String in Key Vault
resource "azurerm_key_vault_secret" "storage_connection_string" {
  name         = "storage-connection-string"
  value        = azurerm_storage_account.yuyama_storage.primary_connection_string
  key_vault_id = azurerm_key_vault.yuyama_vault.id

  depends_on = [azurerm_key_vault.yuyama_vault]
}

# ========================================
# Outputs
# ========================================

output "openai_endpoint" {
  description = "Azure OpenAI Service endpoint"
  value       = azurerm_cognitive_account.openai.endpoint
  sensitive   = false
}

output "openai_key" {
  description = "Azure OpenAI Service API key"
  value       = azurerm_cognitive_account.openai.primary_access_key
  sensitive   = true
}

output "search_endpoint" {
  description = "Azure AI Search endpoint"
  value       = "https://${azurerm_search_service.ai_search.name}.search.windows.net"
  sensitive   = false
}

output "search_admin_key" {
  description = "Azure AI Search admin key"
  value       = azurerm_search_service.ai_search.primary_key
  sensitive   = true
}

output "key_vault_uri" {
  description = "Azure Key Vault URI"
  value       = azurerm_key_vault.yuyama_vault.vault_uri
  sensitive   = false
}

output "managed_identity_client_id" {
  description = "Managed Identity Client ID"
  value       = azurerm_user_assigned_identity.yuyama_identity.client_id
  sensitive   = false
}

output "storage_account_name" {
  description = "Storage Account Name"
  value       = azurerm_storage_account.yuyama_storage.name
  sensitive   = false
}

output "application_insights_connection_string" {
  description = "Application Insights Connection String"
  value       = azurerm_application_insights.yuyama.connection_string
  sensitive   = true
}

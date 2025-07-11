# ========================================
# Terraform Variables for Yuyama RAG System
# ========================================

variable "resource_group_name" {
  description = "Name of the Azure resource group"
  type        = string
  default     = "yuyama"
}

variable "location" {
  description = "Azure region for resource deployment"
  type        = string
  default     = "Japan East"
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name for tagging and naming"
  type        = string
  default     = "yuyama-rag"
}

# OpenAI Configuration
variable "openai_sku" {
  description = "SKU for Azure OpenAI Service"
  type        = string
  default     = "S0"
}

variable "openai_models" {
  description = "List of OpenAI models to deploy"
  type = list(object({
    name    = string
    format  = string
    version = string
    scale_type = string
  }))
  default = [
    {
      name       = "gpt-4"
      format     = "OpenAI"
      version    = "1106-Preview"
      scale_type = "Standard"
    },
    {
      name       = "gpt-4"
      format     = "OpenAI"
      version    = "vision-preview"
      scale_type = "Standard"
    },
    {
      name       = "text-embedding-ada-002"
      format     = "OpenAI"
      version    = "2"
      scale_type = "Standard"
    }
  ]
}

# AI Search Configuration
variable "search_sku" {
  description = "SKU for Azure AI Search"
  type        = string
  default     = "standard"
}

variable "search_replica_count" {
  description = "Number of replicas for Azure AI Search"
  type        = number
  default     = 1
}

variable "search_partition_count" {
  description = "Number of partitions for Azure AI Search"
  type        = number
  default     = 1
}

# Storage Configuration
variable "storage_tier" {
  description = "Storage account tier"
  type        = string
  default     = "Standard"
}

variable "storage_replication" {
  description = "Storage account replication type"
  type        = string
  default     = "LRS"
}

# Key Vault Configuration
variable "key_vault_soft_delete_retention_days" {
  description = "Number of days to retain soft-deleted keys"
  type        = number
  default     = 7
}

variable "enable_purge_protection" {
  description = "Enable purge protection for Key Vault"
  type        = bool
  default     = false
}

# Monitoring Configuration
variable "application_insights_type" {
  description = "Application type for Application Insights"
  type        = string
  default     = "web"
}

# Security Configuration
variable "allowed_ip_ranges" {
  description = "List of allowed IP ranges for services"
  type        = list(string)
  default     = []
}

variable "enable_public_access" {
  description = "Enable public network access for services"
  type        = bool
  default     = true
}

# Tagging
variable "additional_tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}

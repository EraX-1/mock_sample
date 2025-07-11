import os
from typing import Any

import toml
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient

# config.tomlからモック設定を読み込む（優先順位：config.local.toml > config.toml > 環境変数）
config_local_path = os.path.join(os.path.dirname(__file__), "../../config.local.toml")
config_path = os.path.join(os.path.dirname(__file__), "../../config.toml")

config = {}
if os.path.exists(config_local_path):
    config = toml.load(config_local_path)
elif os.path.exists(config_path):
    config = toml.load(config_path)

# Azure環境では環境変数を優先、ローカル環境では設定ファイルを優先
env_use_mock = os.getenv("USE_MOCK_SERVICES")
if env_use_mock is not None:
    # 環境変数が設定されている場合はそれを使用（Azure環境）
    USE_MOCK_SERVICES = env_use_mock.lower() == "true"
else:
    # 環境変数が設定されていない場合は設定ファイルを使用（ローカル環境）
    USE_MOCK_SERVICES = config.get("mock", {}).get("USE_MOCK_SERVICES", False)


# モック用の設定
MOCK_CONFIG = {
    "use_mock_services": USE_MOCK_SERVICES,
    "mock_user": {
        "id": "mock-user-001",
        "mail": "test.user@example.com",
        "displayName": "Test User",
    },
    "mock_admin_user": {
        "id": "mock-admin-001",
        "mail": "admin@example.com",
        "displayName": "Admin User",
    },
}

# ========================================
# Azure Key Vault Integration
# ========================================


class SecureConfigManager:
    """
    Secure configuration manager with Azure Key Vault integration
    Implements zero-trust security model for secret management
    """

    def __init__(self):
        self.key_vault_uri = os.getenv("AZURE_KEY_VAULT_URI")
        self.managed_identity_client_id = os.getenv("AZURE_MANAGED_IDENTITY_CLIENT_ID")
        self._secret_client: SecretClient | None = None
        self._config_cache: dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes cache TTL
        self._last_fetch_time = 0

    def _get_credential(self):
        """Get appropriate Azure credential based on environment"""
        try:
            if self.managed_identity_client_id:
                # Use Managed Identity in Azure environment
                return ManagedIdentityCredential(
                    client_id=self.managed_identity_client_id
                )
            else:
                # Use Default credential chain for local development
                return DefaultAzureCredential()
        except Exception as e:
            print(f"Warning: Failed to get Azure credential: {e}")
            return None

    def _get_secret_client(self) -> SecretClient | None:
        """Initialize and return Key Vault Secret Client"""
        if not self._secret_client and self.key_vault_uri:
            try:
                credential = self._get_credential()
                if credential:
                    self._secret_client = SecretClient(
                        vault_url=self.key_vault_uri, credential=credential
                    )
            except Exception as e:
                print(f"Warning: Failed to initialize Key Vault client: {e}")
        return self._secret_client

    def get_secret(self, secret_name: str, default_value: str = None) -> str | None:
        """
        Get secret from Key Vault with fallback to environment variables
        """
        # First try environment variable (for local development)
        env_value = os.getenv(secret_name.upper().replace("-", "_"))
        if env_value:
            return env_value

        # Try Key Vault
        client = self._get_secret_client()
        if client:
            try:
                secret = client.get_secret(secret_name)
                return secret.value
            except Exception as e:
                print(
                    f"Warning: Failed to get secret '{secret_name}' from Key Vault: {e}"
                )

        return default_value

    def get_config(self, force_refresh: bool = False) -> dict[str, Any]:
        """
        Get complete configuration with caching
        """
        import time

        current_time = time.time()

        # Return cached config if still valid
        if (
            not force_refresh
            and self._config_cache
            and (current_time - self._last_fetch_time) < self._cache_ttl
        ):
            return self._config_cache

        # Fetch fresh configuration
        config = self._fetch_configuration()
        self._config_cache = config
        self._last_fetch_time = current_time

        return config

    def _fetch_configuration(self) -> dict[str, Any]:
        """
        Fetch configuration from Key Vault and environment variables
        """
        return {
            # Azure OpenAI Configuration
            "openai": {
                "endpoint": self.get_secret(
                    "openai-endpoint", os.getenv("AZURE_OPENAI_ENDPOINT")
                ),
                "api_key": self.get_secret(
                    "openai-api-key", os.getenv("AZURE_OPENAI_API_KEY")
                ),
                "api_version": os.getenv(
                    "AZURE_OPENAI_API_VERSION", "2024-02-15-preview"
                ),
                "deployment_name": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4"),
                "embedding_deployment_name": os.getenv(
                    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME", "text-embedding-ada-002"
                ),
                "vision_deployment_name": os.getenv(
                    "AZURE_OPENAI_VISION_DEPLOYMENT_NAME", "gpt-4-vision"
                ),
            },
            # Azure AI Search Configuration (常に実際のAzureサービスを使用)
            "search": {
                "endpoint": self.get_secret(
                    "search-endpoint",
                    os.getenv(
                        "AZURE_SEARCH_ENDPOINT",
                        "https://yuyama-ai-search-std.search.windows.net/",
                    ),
                ),
                "admin_key": self.get_secret(
                    "search-admin-key",
                    os.getenv("AZURE_SEARCH_ADMIN_KEY"),
                ),
                "api_version": os.getenv("AZURE_SEARCH_API_VERSION", "2023-11-01"),
                "index_name": os.getenv(
                    "AZURE_SEARCH_INDEX_NAME", "yuyama-documents-index"
                ),
            },
            # Azure Blob Storage Configuration
            "storage": {
                "account_name": os.getenv("AZURE_STORAGE_ACCOUNT_NAME"),
                "connection_string": self.get_secret(
                    "storage-connection-string",
                    os.getenv("AZURE_STORAGE_CONNECTION_STRING"),
                ),
                "containers": {
                    "documents": "documents",
                    "images": "images",
                    "audio": "audio",
                },
            },
            # Application Insights Configuration
            "monitoring": {
                "connection_string": self.get_secret(
                    "appinsights-connection-string",
                    os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"),
                ),
                "instrumentation_key": os.getenv("APPINSIGHTS_INSTRUMENTATION_KEY"),
            },
            # Security Configuration
            "security": {
                "managed_identity_client_id": self.managed_identity_client_id,
                "key_vault_uri": self.key_vault_uri,
                "enable_auth": os.getenv("ENABLE_AUTHENTICATION", "true").lower()
                == "true",
            },
            # Application Configuration
            "app": {
                "environment": os.getenv("ENVIRONMENT", "production"),
                "debug": os.getenv("DEBUG", "false").lower() == "true",
                "log_level": os.getenv("LOG_LEVEL", "INFO"),
                "cors_origins": os.getenv("CORS_ORIGINS", "*").split(","),
            },
        }


# Global configuration manager instance
secure_config = SecureConfigManager()

# ========================================
# Enhanced Azure Configuration
# ========================================


# Update AZURE_CONFIG with secure configuration
def get_azure_config() -> dict[str, Any]:
    """Get Azure configuration with Key Vault integration"""
    config = secure_config.get_config()

    return {
        # Azure AD Configuration
        "client_id": os.getenv("AZURE_CLIENT_ID"),
        "client_secret": os.getenv("AZURE_CLIENT_SECRET"),
        "authority": f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID')}",
        "scope": ["https://graph.microsoft.com/User.Read"],
        "redirect_uri": os.getenv("REDIRECT_URI"),
        "frontend_url": os.getenv("FRONTEND_URL", "http://localhost:3000"),
        # Enhanced configuration from Key Vault
        "openai": config["openai"],
        "search": config["search"],
        "storage": config["storage"],
        "monitoring": config["monitoring"],
        "security": config["security"],
        "app": config["app"],
    }


# Update the original AZURE_CONFIG to use the new secure configuration
AZURE_CONFIG = get_azure_config()

# ========================================
# Configuration Helper Functions
# ========================================


def is_production() -> bool:
    """Check if running in production environment"""
    return AZURE_CONFIG.get("app", {}).get("environment") == "production"


def is_mock_enabled() -> bool:
    """Check if mock services are enabled"""
    return USE_MOCK_SERVICES


def get_openai_config() -> dict[str, str]:
    """Get OpenAI configuration"""
    return AZURE_CONFIG.get("openai", {})


def get_search_config() -> dict[str, str]:
    """Get AI Search configuration"""
    search_config = AZURE_CONFIG.get("search", {})
    return search_config


def get_storage_config() -> dict[str, str]:
    """Get Storage configuration"""
    return AZURE_CONFIG.get("storage", {})


def refresh_config():
    """Refresh configuration from Key Vault"""
    global AZURE_CONFIG
    AZURE_CONFIG = get_azure_config()

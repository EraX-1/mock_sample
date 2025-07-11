import logging
import os
import time
from collections.abc import AsyncGenerator
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import toml
from openai import AsyncAzureOpenAI
from openai import AzureOpenAI as AOAI
from openai.types.chat import ChatCompletion
from tenacity import retry, stop_after_attempt, wait_exponential


class StreamingMode(Enum):
    """ストリーミングモードの種類"""

    STANDARD = "standard"
    ADAPTIVE = "adaptive"
    TURBO = "turbo"
    BANDWIDTH_AWARE = "bandwidth_aware"


@dataclass
class ClientMetrics:
    """クライアントメトリクス"""

    bandwidth_mbps: float = 0.0
    latency_ms: float = 0.0
    processing_power: float = 1.0  # 1.0 = 標準
    connection_quality: float = 1.0  # 1.0 = 最高品質
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class OpenAIMetrics:
    """OpenAI API使用メトリクス"""

    request_count: int = 0
    error_count: int = 0
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    response_time_ms: float = 0.0
    requests_per_minute: int = 0
    errors_per_minute: int = 0
    last_request_time: datetime | None = None


class AzureOpenAI:
    """
    Azure OpenAI Service integration
    Features:
    - Advanced error handling and retry mechanisms
    - Rate limiting and quota management
    - Comprehensive monitoring and metrics
    - Streaming response optimization
    - Security and performance enhancements
    """

    def __init__(self):
        # デバッグログを追加
        logger = logging.getLogger(__name__)
        logger.info("AzureOpenAI initialization")

        # 設定ファイルから直接読み込み
        self.config = self._load_config()
        self.api_key = os.environ.get("AOAI_API_KEY") or self.config.get(
            "AOAI_API_KEY", "<AOAI_API_KEY>"
        )
        self.endpoint = os.environ.get("AOAI_ENDPOINT") or self.config.get(
            "AOAI_ENDPOINT", "https://yuyama-openai.openai.azure.com/"
        )
        self.api_version = os.environ.get("AOAI_API_VERSION") or self.config.get(
            "AOAI_API_VERSION", "2024-02-15-preview"
        )
        logger.info(f"Using Azure OpenAI configuration - endpoint: {self.endpoint}")

        # Model deployments (動的設定対応)
        self.chat_deployment = (
            os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")
            or os.environ.get("CHAT_DEPLOYMENT_NAME")
            or self.config.get("CHAT_DEPLOYMENT_NAME")
            or self.config.get("AZURE_OPENAI_DEPLOYMENT_NAME")
            or "gpt-4o"
        )
        self.embedding_deployment = (
            os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
            or os.environ.get("EMBEDDING_DEPLOYMENT_NAME")
            or self.config.get("EMBEDDING_DEPLOYMENT_NAME")
            or self.config.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
            or "text-embedding-ada-002"
        )

        # Logger setup
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Metrics
        self.metrics = OpenAIMetrics()
        self._setup_metrics()

        # Rate limiting
        self.rate_limiter = {
            "requests_per_minute": 600,  # Conservative limit
            "tokens_per_minute": 150000,
            "current_requests": 0,
            "current_tokens": 0,
            "window_start": time.time(),
        }

        # Circuit breaker state
        self.circuit_breaker = {
            "failure_count": 0,
            "failure_threshold": 5,
            "recovery_timeout": 60,
            "last_failure_time": None,
            "state": "closed",  # closed, open, half-open
        }

        # Initialize clients
        self._sync_client = None
        self._async_client = None

    def _load_config(self) -> dict[str, Any]:
        """設定ファイルを読み込み"""
        config_local_path = os.path.join(
            os.path.dirname(__file__), "../../config.local.toml"
        )
        config_path = os.path.join(os.path.dirname(__file__), "../../config.toml")

        config = {}
        if os.path.exists(config_local_path):
            config = toml.load(config_local_path)
        elif os.path.exists(config_path):
            config = toml.load(config_path)

        # env セクションの値を返す
        return config.get("env", {})

    def _setup_metrics(self):
        """Setup metrics that don't cause errors"""

        class DummyMetric:
            def inc(self, *args, **kwargs):
                pass

            def observe(self, *args, **kwargs):
                pass

            def set(self, *args, **kwargs):
                pass

            def labels(self, *args, **kwargs):
                return self

        self.prom_request_count = DummyMetric()
        self.prom_request_duration = DummyMetric()
        self.prom_token_usage = DummyMetric()
        self.prom_rate_limit_remaining = DummyMetric()

    def _check_circuit_breaker(self) -> bool:
        """Circuit breaker pattern implementation"""
        current_time = time.time()

        if self.circuit_breaker["state"] == "open":
            if (
                current_time - self.circuit_breaker["last_failure_time"]
            ) > self.circuit_breaker["recovery_timeout"]:
                self.circuit_breaker["state"] = "half-open"
                self.logger.info("Circuit breaker moved to half-open state")
                return True
            return False

        return True  # closed or half-open

    def _record_failure(self):
        """Record API failure for circuit breaker"""
        self.circuit_breaker["failure_count"] += 1
        self.circuit_breaker["last_failure_time"] = time.time()

        if (
            self.circuit_breaker["failure_count"]
            >= self.circuit_breaker["failure_threshold"]
        ):
            self.circuit_breaker["state"] = "open"
            self.logger.error("Circuit breaker opened due to failures")

    def _record_success(self):
        """Record API success for circuit breaker"""
        self.circuit_breaker["failure_count"] = 0
        if self.circuit_breaker["state"] == "half-open":
            self.circuit_breaker["state"] = "closed"
            self.logger.info("Circuit breaker closed after successful request")

    def _check_rate_limit(self, estimated_tokens: int = 1000) -> bool:
        """Rate limiting check"""
        current_time = time.time()

        # Reset window if needed
        if current_time - self.rate_limiter["window_start"] >= 60:
            self.rate_limiter["current_requests"] = 0
            self.rate_limiter["current_tokens"] = 0
            self.rate_limiter["window_start"] = current_time

        # Check limits
        if (
            self.rate_limiter["current_requests"]
            >= self.rate_limiter["requests_per_minute"]
            or self.rate_limiter["current_tokens"] + estimated_tokens
            > self.rate_limiter["tokens_per_minute"]
        ):
            return False

        return True

    def _update_rate_limit(self, tokens_used: int):
        """Update rate limit counters"""
        self.rate_limiter["current_requests"] += 1
        self.rate_limiter["current_tokens"] += tokens_used

        # Update Prometheus metrics
        remaining_requests = max(
            0,
            self.rate_limiter["requests_per_minute"]
            - self.rate_limiter["current_requests"],
        )
        remaining_tokens = max(
            0,
            self.rate_limiter["tokens_per_minute"]
            - self.rate_limiter["current_tokens"],
        )

        self.prom_rate_limit_remaining.labels(type="requests").set(remaining_requests)
        self.prom_rate_limit_remaining.labels(type="tokens").set(remaining_tokens)

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _make_request_with_retry(self, func, *args, **kwargs):
        """Retry wrapper for API requests"""
        if not self._check_circuit_breaker():
            raise Exception("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            self.logger.error(f"API request failed: {str(e)}")
            raise

    def init_client(self):
        """Initialize OpenAI client with production configurations"""
        self.logger.info("Initializing Azure OpenAI client")

        if not self._sync_client:
            try:
                self.logger.info(
                    f"Initializing Azure OpenAI client with endpoint: {self.endpoint}"
                )
                self._sync_client = AOAI(
                    api_key=self.api_key,
                    api_version=self.api_version,
                    azure_endpoint=self.endpoint,
                    timeout=60.0,  # タイムアウトを60秒に延長
                    max_retries=3,
                )
                self.logger.info("Azure OpenAI client initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
                raise

        return self._sync_client

    def init_async_client(self):
        """Initialize async OpenAI client"""
        if not self._async_client:
            self._async_client = AsyncAzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.endpoint,
                timeout=60.0,  # タイムアウトを60秒に延長
                max_retries=3,
            )

        return self._async_client

    def create_chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str = None,
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> ChatCompletion | AsyncGenerator:
        """Create chat completion with enhanced error handling"""
        model = model or self.chat_deployment

        # Estimate tokens for rate limiting
        estimated_tokens = (
            sum(len(msg.get("content", "").split()) for msg in messages) * 1.3
        )

        if not self._check_rate_limit(int(estimated_tokens)):
            raise Exception("Rate limit exceeded")

        start_time = time.time()

        try:
            self.logger.info(f"Creating chat completion - model: {model}")

            client = self.init_client()
            response = self._make_request_with_retry(
                client.chat.completions.create,
                model=model,
                messages=messages,
                stream=stream,
                temperature=temperature,
                max_tokens=max_tokens,
                stream_options={"include_usage": True} if stream else None,
                **kwargs,
            )

            # Update metrics
            response_time = (time.time() - start_time) * 1000
            self.metrics.response_time_ms = response_time
            self.metrics.request_count += 1
            self.metrics.last_request_time = datetime.now()

            # Prometheus metrics
            self.prom_request_count.labels(model=model, status="success").inc()
            self.prom_request_duration.labels(model=model, operation="chat").observe(
                response_time / 1000
            )

            if not stream and hasattr(response, "usage"):
                usage = response.usage
                self.prom_token_usage.labels(model=model, type="prompt").inc(
                    usage.prompt_tokens
                )
                self.prom_token_usage.labels(model=model, type="completion").inc(
                    usage.completion_tokens
                )
                self._update_rate_limit(usage.total_tokens)

            return response

        except Exception as e:
            self.metrics.error_count += 1
            self.prom_request_count.labels(model=model, status="error").inc()

            # 詳細なエラーログを出力
            import traceback

            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "model": model,
                "endpoint": self.endpoint,
                "traceback": traceback.format_exc(),
            }
            self.logger.error(
                f"Chat completion failed with detailed info: {error_details}"
            )
            raise

    async def acreate_chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str = None,
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> ChatCompletion | AsyncGenerator:
        """Async chat completion"""
        model = model or self.chat_deployment

        if not self._check_rate_limit():
            raise Exception("Rate limit exceeded")

        start_time = time.time()

        try:
            client = self.init_async_client()

            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                stream=stream,
                temperature=temperature,
                max_tokens=max_tokens,
                stream_options={"include_usage": True} if stream else None,
                **kwargs,
            )

            # Update metrics
            response_time = (time.time() - start_time) * 1000
            self.prom_request_duration.labels(model=model, operation="chat").observe(
                response_time / 1000
            )

            return response

        except Exception as e:
            self.logger.error(f"Async chat completion failed: {str(e)}")
            raise

    def create_embedding(self, input_text: str | list[str], model: str = None):
        """Create embeddings with error handling"""
        model = model or self.embedding_deployment

        if not self._check_rate_limit():
            raise Exception("Rate limit exceeded")

        start_time = time.time()

        try:
            self.logger.info(f"Creating embedding - model: {model}")

            client = self.init_client()
            response = self._make_request_with_retry(
                client.embeddings.create, model=model, input=input_text
            )

            # Update metrics
            response_time = (time.time() - start_time) * 1000
            self.prom_request_duration.labels(
                model=model, operation="embedding"
            ).observe(response_time / 1000)

            if hasattr(response, "usage"):
                self.prom_token_usage.labels(model=model, type="prompt").inc(
                    response.usage.prompt_tokens
                )
                self._update_rate_limit(response.usage.total_tokens)

            return response

        except Exception as e:
            # 詳細なエラーログを出力
            import traceback

            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "model": model,
                "endpoint": self.endpoint,
                "input_type": type(input_text).__name__,
                "traceback": traceback.format_exc(),
            }
            self.logger.error(
                f"Embedding creation failed with detailed info: {error_details}"
            )
            raise

    def get_metrics(self) -> dict[str, Any]:
        """Get current metrics"""
        metrics_dict = asdict(self.metrics)
        # Convert datetime to string for JSON serialization
        if metrics_dict.get("last_request_time"):
            metrics_dict["last_request_time"] = metrics_dict[
                "last_request_time"
            ].isoformat()
        return metrics_dict

    def get_health_status(self) -> dict[str, Any]:
        """Get service health status"""
        return {
            "status": "healthy"
            if self.circuit_breaker["state"] == "closed"
            else f"degraded_{self.circuit_breaker['state']}",
            "circuit_breaker": self.circuit_breaker,
            "rate_limit": {
                "requests_remaining": max(
                    0,
                    self.rate_limiter["requests_per_minute"]
                    - self.rate_limiter["current_requests"],
                ),
                "tokens_remaining": max(
                    0,
                    self.rate_limiter["tokens_per_minute"]
                    - self.rate_limiter["current_tokens"],
                ),
            },
            "metrics": self.get_metrics(),
        }

"""
Azure OpenAI Service Health Check and Monitoring Endpoints
本番環境でのヘルスチェックとモニタリング機能を提供
"""

import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from src.services.azure_openai import AzureOpenAI

# Router setup
router = APIRouter(prefix="/health/azure-openai", tags=["health", "monitoring"])

# Logger setup
logger = logging.getLogger(__name__)

# Global production client instance
production_client = None


def get_production_client() -> AzureOpenAI:
    """Get or create production Azure OpenAI client"""
    global production_client
    if production_client is None:
        production_client = AzureOpenAI()
    return production_client


@router.get("/status")
async def get_health_status(client: AzureOpenAI = Depends(get_production_client)):
    """
    Azure OpenAI Service health status endpoint

    Returns:
        Dict containing health status, circuit breaker state, and metrics
    """
    try:
        health_status = client.get_health_status()

        # Add timestamp
        health_status["timestamp"] = time.time()
        health_status["service"] = "azure-openai"

        # Determine HTTP status code based on health
        if health_status["status"] == "healthy":
            return JSONResponse(content=health_status, status_code=200)
        else:
            return JSONResponse(content=health_status, status_code=503)

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            content={
                "status": "error",
                "error": str(e),
                "timestamp": time.time(),
                "service": "azure-openai",
            },
            status_code=500,
        )


@router.get("/metrics")
async def get_metrics(client: AzureOpenAI = Depends(get_production_client)):
    """
    Get detailed metrics for Azure OpenAI Service

    Returns:
        Dict containing detailed metrics and performance data
    """
    try:
        metrics = client.get_metrics()

        # Add additional computed metrics
        extended_metrics = {
            **metrics,
            "timestamp": time.time(),
            "service": "azure-openai",
            "computed_metrics": {
                "error_rate": (
                    metrics["error_count"] / max(metrics["request_count"], 1)
                )
                * 100,
                "avg_response_time_ms": metrics["response_time_ms"],
                "uptime_seconds": time.time()
                - (metrics.get("last_request_time", time.time()) or time.time()),
            },
        }

        return JSONResponse(content=extended_metrics, status_code=200)

    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Metrics collection failed: {str(e)}"
        )


@router.get("/debug/config")
async def get_debug_config(client: AzureOpenAI = Depends(get_production_client)):
    """
    Get detailed configuration information for debugging

    Returns:
        Dict containing detailed configuration and environment information
    """
    try:
        import os

        from src.config.azure_config import MOCK_CONFIG, get_openai_config

        debug_info = {
            "timestamp": time.time(),
            "service": "azure-openai-debug",
            "mock_config": MOCK_CONFIG,
            "client_info": {
                "use_mock": False,
                "aoai_endpoint": getattr(client, "aoai_endpoint", "Not set"),
                "aoai_api_version": getattr(client, "aoai_api_version", "Not set"),
                "chat_deployment": client.chat_deployment,
                "embedding_deployment": client.embedding_deployment,
            },
            "environment_variables": {
                "USE_MOCK_SERVICES": os.getenv("USE_MOCK_SERVICES"),
                "AOAI_ENDPOINT": os.getenv("AOAI_ENDPOINT"),
                "AOAI_API_KEY": "***" if os.getenv("AOAI_API_KEY") else None,
                "AOAI_API_VERSION": os.getenv("AOAI_API_VERSION"),
            },
            "openai_config": get_openai_config(),
            "client_type": type(client._sync_client).__name__
            if client._sync_client
            else "Not initialized",
        }

        return JSONResponse(content=debug_info, status_code=200)

    except Exception as e:
        logger.error(f"Debug config failed: {str(e)}")
        return JSONResponse(
            content={
                "status": "error",
                "error": str(e),
                "timestamp": time.time(),
                "service": "azure-openai-debug",
            },
            status_code=500,
        )


@router.post("/test/connectivity")
async def test_connectivity(client: AzureOpenAI = Depends(get_production_client)):
    """
    Test Azure OpenAI Service connectivity

    Returns:
        Dict containing connectivity test results
    """
    start_time = time.time()

    try:
        logger.info(f"Starting connectivity test - use_mock: {False}")

        # Simple connectivity test
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": "Hello! This is a connectivity test. Please respond with 'Connection successful'.",
            },
        ]

        response = client.create_chat_completion(
            messages=test_messages,
            model=client.chat_deployment,
            max_tokens=50,
            temperature=0.1,
        )

        response_time = (time.time() - start_time) * 1000

        # Extract response content
        response_content = ""
        if hasattr(response, "choices") and response.choices:
            response_content = response.choices[0].message.content

        logger.info(f"Connectivity test successful - response: {response_content}")

        return JSONResponse(
            content={
                "status": "success",
                "response_time_ms": response_time,
                "response_content": response_content,
                "model": client.chat_deployment,
                "use_mock": False,
                "endpoint": getattr(client, "aoai_endpoint", "Unknown"),
                "timestamp": time.time(),
                "service": "azure-openai",
            },
            status_code=200,
        )

    except Exception as e:
        response_time = (time.time() - start_time) * 1000

        # 詳細なエラーログを出力
        import traceback

        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "use_mock": False,  # 常にFalse（モックは削除済み）
            "endpoint": getattr(client, "endpoint", "Unknown"),
            "traceback": traceback.format_exc(),
        }
        logger.error(f"Connectivity test failed with detailed info: {error_details}")

        return JSONResponse(
            content={
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "response_time_ms": response_time,
                "use_mock": False,
                "endpoint": getattr(client, "aoai_endpoint", "Unknown"),
                "timestamp": time.time(),
                "service": "azure-openai",
            },
            status_code=503,
        )


@router.post("/test/embedding")
async def test_embedding(client: AzureOpenAI = Depends(get_production_client)):
    """
    Test Azure OpenAI embedding functionality

    Returns:
        Dict containing embedding test results
    """
    start_time = time.time()

    try:
        # Test embedding generation
        test_text = "This is a test for embedding generation."

        response = client.create_embedding(
            input_text=test_text, model=client.embedding_deployment
        )

        response_time = (time.time() - start_time) * 1000

        # Validate embedding response
        embedding_vector = None
        if hasattr(response, "data") and response.data:
            embedding_vector = response.data[0].embedding
            embedding_length = len(embedding_vector) if embedding_vector else 0
        else:
            embedding_length = 0

        return JSONResponse(
            content={
                "status": "success",
                "response_time_ms": response_time,
                "embedding_length": embedding_length,
                "model": client.embedding_deployment,
                "timestamp": time.time(),
                "service": "azure-openai-embedding",
            },
            status_code=200,
        )

    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.error(f"Embedding test failed: {str(e)}")

        return JSONResponse(
            content={
                "status": "failed",
                "error": str(e),
                "response_time_ms": response_time,
                "timestamp": time.time(),
                "service": "azure-openai-embedding",
            },
            status_code=503,
        )


@router.get("/circuit-breaker/status")
async def get_circuit_breaker_status(
    client: AzureOpenAI = Depends(get_production_client),
):
    """
    Get circuit breaker status

    Returns:
        Dict containing circuit breaker state and statistics
    """
    try:
        circuit_breaker_info = {
            "circuit_breaker": client.circuit_breaker,
            "timestamp": time.time(),
            "service": "azure-openai",
        }

        return JSONResponse(content=circuit_breaker_info, status_code=200)

    except Exception as e:
        logger.error(f"Circuit breaker status check failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Circuit breaker status check failed: {str(e)}"
        )


@router.post("/circuit-breaker/reset")
async def reset_circuit_breaker(client: AzureOpenAI = Depends(get_production_client)):
    """
    Reset circuit breaker (admin operation)

    Returns:
        Dict containing reset operation result
    """
    try:
        # Reset circuit breaker state
        client.circuit_breaker["failure_count"] = 0
        client.circuit_breaker["state"] = "closed"
        client.circuit_breaker["last_failure_time"] = None

        logger.info("Circuit breaker manually reset")

        return JSONResponse(
            content={
                "status": "success",
                "message": "Circuit breaker reset successfully",
                "circuit_breaker": client.circuit_breaker,
                "timestamp": time.time(),
                "service": "azure-openai",
            },
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Circuit breaker reset failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Circuit breaker reset failed: {str(e)}"
        )


@router.get("/rate-limit/status")
async def get_rate_limit_status(client: AzureOpenAI = Depends(get_production_client)):
    """
    Get current rate limit status

    Returns:
        Dict containing rate limit information
    """
    try:
        current_time = time.time()

        # Calculate time until reset
        time_until_reset = 60 - (current_time - client.rate_limiter["window_start"])
        if time_until_reset < 0:
            time_until_reset = 0

        rate_limit_info = {
            "rate_limiter": {
                **client.rate_limiter,
                "time_until_reset_seconds": time_until_reset,
                "requests_remaining": max(
                    0,
                    client.rate_limiter["requests_per_minute"]
                    - client.rate_limiter["current_requests"],
                ),
                "tokens_remaining": max(
                    0,
                    client.rate_limiter["tokens_per_minute"]
                    - client.rate_limiter["current_tokens"],
                ),
            },
            "timestamp": current_time,
            "service": "azure-openai",
        }

        return JSONResponse(content=rate_limit_info, status_code=200)

    except Exception as e:
        logger.error(f"Rate limit status check failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Rate limit status check failed: {str(e)}"
        )


# Prometheus metrics endpoint
@router.get("/prometheus")
async def get_prometheus_metrics():
    """
    Get Prometheus-formatted metrics

    Returns:
        Text response with Prometheus metrics
    """
    try:
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

        metrics_data = generate_latest()

        return JSONResponse(
            content=metrics_data.decode("utf-8"),
            status_code=200,
            headers={"Content-Type": CONTENT_TYPE_LATEST},
        )

    except Exception as e:
        logger.error(f"Prometheus metrics collection failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Prometheus metrics collection failed: {str(e)}"
        )

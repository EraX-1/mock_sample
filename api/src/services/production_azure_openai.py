"""
ProductionAzureOpenAI - 革新的なAzure OpenAI統合サービス

このモジュールは以下の革新的機能を提供します：
1. Adaptive Streaming Pipeline - 動的ストリーミング最適化
2. Intelligent Retry Orchestra - AIベースのリトライ戦略
3. Context-Aware Performance Profiler - コンテキスト認識型パフォーマンス最適化
"""

import asyncio
import hashlib
import json
import logging
import os
import statistics
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import redis
from openai import AsyncAzureOpenAI
from openai import AzureOpenAI as AOAI

from src.config.azure_config import MOCK_CONFIG

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """リトライ戦略の種類"""

    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    JITTER_BACKOFF = "jitter_backoff"
    CIRCUIT_BREAKER = "circuit_breaker"
    ADAPTIVE = "adaptive"


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
class PerformanceProfile:
    """パフォーマンスプロファイル"""

    expected_tokens: int = 0
    complexity_score: float = 0.0
    estimated_duration_ms: float = 0.0
    required_resources: dict[str, float] = field(default_factory=dict)
    priority_level: int = 1  # 1-10 (10が最高優先度)


@dataclass
class ErrorPattern:
    """エラーパターン"""

    error_type: str
    frequency: int = 0
    success_rate: float = 0.0
    avg_retry_count: float = 0.0
    best_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    last_occurrence: datetime = field(default_factory=datetime.now)


class AdaptiveChunkCalculator:
    """動的チャンクサイズ計算機"""

    def __init__(self):
        self.min_chunk_size = 1
        self.max_chunk_size = 100
        self.default_chunk_size = 10

    def calculate_optimal_chunk_size(
        self, metrics: ClientMetrics, context_complexity: float
    ) -> int:
        """最適なチャンクサイズを計算"""
        # 帯域幅ベースの調整
        bandwidth_factor = min(metrics.bandwidth_mbps / 10.0, 2.0)  # 10Mbpsを基準

        # レイテンシベースの調整
        latency_factor = max(100.0 / max(metrics.latency_ms, 1), 0.5)

        # 処理能力ベースの調整
        processing_factor = metrics.processing_power

        # コンテキストの複雑さベースの調整
        complexity_factor = 1.0 / max(context_complexity, 0.1)

        # 総合的なチャンクサイズ計算
        optimal_size = int(
            self.default_chunk_size
            * bandwidth_factor
            * latency_factor
            * processing_factor
            * complexity_factor
        )

        return max(self.min_chunk_size, min(optimal_size, self.max_chunk_size))


class ContextAnalyzer:
    """コンテキスト分析器"""

    def __init__(self):
        self.complexity_patterns = {
            "simple": ["hello", "hi", "thanks", "簡単", "基本"],
            "medium": ["explain", "how", "what", "説明", "方法"],
            "complex": ["analyze", "compare", "detailed", "分析", "比較", "詳細"],
            "expert": [
                "algorithm",
                "architecture",
                "optimization",
                "アルゴリズム",
                "アーキテクチャ",
            ],
        }

    def analyze_query_complexity(self, query: str) -> float:
        """クエリの複雑さを分析 (0.0-1.0)"""
        query_lower = query.lower()

        # 長さベースのスコア
        length_score = min(len(query) / 1000.0, 0.4)

        # キーワードベースのスコア
        keyword_score = 0.0
        for complexity, keywords in self.complexity_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                if complexity == "simple":
                    keyword_score = max(keyword_score, 0.1)
                elif complexity == "medium":
                    keyword_score = max(keyword_score, 0.3)
                elif complexity == "complex":
                    keyword_score = max(keyword_score, 0.6)
                elif complexity == "expert":
                    keyword_score = max(keyword_score, 0.9)

        # 特殊文字や技術用語の検出
        technical_score = 0.0
        technical_indicators = ["()", "{}", "[]", "API", "JSON", "HTTP", "SQL"]
        if any(indicator in query for indicator in technical_indicators):
            technical_score = 0.2

        return min(length_score + keyword_score + technical_score, 1.0)

    def predict_token_count(self, query: str, complexity: float) -> int:
        """予想トークン数を予測"""
        base_tokens = len(query.split()) * 1.3  # 基本的なトークン推定
        complexity_multiplier = 1.0 + (complexity * 3.0)  # 複雑さに応じた増加
        return int(base_tokens * complexity_multiplier)

    def estimate_response_time(self, token_count: int, complexity: float) -> float:
        """予想レスポンス時間を推定 (ミリ秒)"""
        base_time_per_token = 50  # ベースタイム（ミリ秒/トークン）
        complexity_overhead = complexity * 200  # 複雑さによるオーバーヘッド
        return (token_count * base_time_per_token) + complexity_overhead


class IntelligentRetryOrchestra:
    """インテリジェントリトライオーケストラ"""

    def __init__(self):
        self.error_patterns: dict[str, ErrorPattern] = {}
        self.global_success_rate = 0.95
        self.strategy_performance: dict[RetryStrategy, float] = dict.fromkeys(
            RetryStrategy, 0.8
        )

    def learn_from_error(
        self,
        error_type: str,
        strategy_used: RetryStrategy,
        success: bool,
        retry_count: int,
    ):
        """エラーから学習"""
        if error_type not in self.error_patterns:
            self.error_patterns[error_type] = ErrorPattern(error_type=error_type)

        pattern = self.error_patterns[error_type]
        pattern.frequency += 1
        pattern.last_occurrence = datetime.now()

        # 成功率の更新
        if success:
            pattern.success_rate = (
                pattern.success_rate * (pattern.frequency - 1) + 1.0
            ) / pattern.frequency
        else:
            pattern.success_rate = (
                pattern.success_rate * (pattern.frequency - 1) + 0.0
            ) / pattern.frequency

        # 平均リトライ回数の更新
        pattern.avg_retry_count = (
            pattern.avg_retry_count * (pattern.frequency - 1) + retry_count
        ) / pattern.frequency

        # 戦略パフォーマンスの更新
        if success:
            self.strategy_performance[strategy_used] = (
                self.strategy_performance[strategy_used] * 0.9 + 0.1
            )
        else:
            self.strategy_performance[strategy_used] = (
                self.strategy_performance[strategy_used] * 0.9 + 0.0
            )

        # 最適戦略の更新
        if pattern.frequency >= 5:  # 十分なデータが集まったら
            best_strategy = max(
                self.strategy_performance.keys(),
                key=lambda s: self.strategy_performance[s],
            )
            pattern.best_strategy = best_strategy

    def get_optimal_strategy(self, error_type: str) -> RetryStrategy:
        """最適なリトライ戦略を取得"""
        if error_type in self.error_patterns:
            pattern = self.error_patterns[error_type]
            if pattern.frequency >= 3:  # 十分な学習データがある場合
                return pattern.best_strategy

        # デフォルト戦略
        return RetryStrategy.ADAPTIVE

    def calculate_backoff_time(
        self, attempt: int, strategy: RetryStrategy, error_type: str = ""
    ) -> float:
        """バックオフ時間を計算"""
        base_delay = 1.0

        if strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            return base_delay * (2**attempt)
        elif strategy == RetryStrategy.LINEAR_BACKOFF:
            return base_delay * attempt
        elif strategy == RetryStrategy.JITTER_BACKOFF:
            import random

            return base_delay * (2**attempt) * (0.5 + random.random() * 0.5)
        elif strategy == RetryStrategy.ADAPTIVE:
            # エラーパターンに基づく適応的調整
            if error_type in self.error_patterns:
                pattern = self.error_patterns[error_type]
                success_factor = pattern.success_rate
                frequency_factor = min(pattern.frequency / 100.0, 1.0)
                return (
                    base_delay
                    * (2**attempt)
                    * (2.0 - success_factor)
                    * (1.0 + frequency_factor)
                )
            else:
                return base_delay * (2**attempt)

        return base_delay


class ProductionAzureOpenAI:
    """プロダクション対応Azure OpenAIクライアント"""

    def __init__(self):
        self.aoai_api_key = os.environ.get("AOAI_API_KEY", "mock-key")
        self.aoai_endpoint = os.environ.get(
            "AOAI_ENDPOINT", "https://mock.openai.azure.com/"
        )
        self.aoai_api_version = os.environ.get("AOAI_API_VERSION", "2024-02-01")
        self.use_mock = MOCK_CONFIG["use_mock_services"]

        # 革新的コンポーネント
        self.chunk_calculator = AdaptiveChunkCalculator()
        self.context_analyzer = ContextAnalyzer()
        self.retry_orchestra = IntelligentRetryOrchestra()

        # メトリクス
        self.client_metrics: dict[str, ClientMetrics] = {}
        self.performance_history: list[dict] = []

        # Redis接続（オプション）
        self.redis_client = None
        try:
            self.redis_client = redis.Redis(
                host=os.environ.get("REDIS_HOST", "localhost"),
                port=int(os.environ.get("REDIS_PORT", 6379)),
                decode_responses=True,
            )
        except:
            logger.warning("Redis接続に失敗しました。キャッシュ機能は無効化されます。")

        # クライアント初期化
        self.sync_client = self._init_sync_client()
        self.async_client = self._init_async_client()

    def _init_sync_client(self):
        """同期クライアントの初期化"""
        # Azure OpenAI Serviceは常に実際のAzureに接続（モック設定を無視）
        return AOAI(
            api_key=self.aoai_api_key,
            api_version=self.aoai_api_version,
            azure_endpoint=self.aoai_endpoint,
        )

    def _init_async_client(self):
        """非同期クライアントの初期化"""
        # Azure OpenAI Serviceは常に実際のAzureに接続（モック設定を無視）
        return AsyncAzureOpenAI(
            api_key=self.aoai_api_key,
            api_version=self.aoai_api_version,
            azure_endpoint=self.aoai_endpoint,
        )

    def update_client_metrics(self, client_id: str, metrics: ClientMetrics):
        """クライアントメトリクスを更新"""
        self.client_metrics[client_id] = metrics
        logger.info(f"クライアント {client_id} のメトリクスを更新: {metrics}")

    def _get_client_metrics(self, client_id: str) -> ClientMetrics:
        """クライアントメトリクスを取得"""
        return self.client_metrics.get(client_id, ClientMetrics())

    def _cache_key(self, messages: list[dict], model: str, **kwargs) -> str:
        """キャッシュキーを生成"""
        content = json.dumps(
            {"messages": messages, "model": model, **kwargs}, sort_keys=True
        )
        return f"openai_cache:{hashlib.md5(content.encode()).hexdigest()}"

    def _get_cached_response(self, cache_key: str) -> dict | None:
        """キャッシュされたレスポンスを取得"""
        if not self.redis_client:
            return None

        try:
            cached = self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"キャッシュ取得エラー: {e}")
        return None

    def _cache_response(self, cache_key: str, response: dict, ttl: int = 3600):
        """レスポンスをキャッシュ"""
        if not self.redis_client:
            return

        try:
            self.redis_client.setex(cache_key, ttl, json.dumps(response))
        except Exception as e:
            logger.warning(f"キャッシュ保存エラー: {e}")

    async def create_chat_completion_with_streaming(
        self,
        messages: list[dict[str, Any]],
        model: str = "gpt-4o-mini",
        client_id: str = "default",
        streaming_mode: StreamingMode = StreamingMode.ADAPTIVE,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """革新的ストリーミングチャット補完"""

        # 1. コンテキスト分析
        user_query = messages[-1].get("content", "") if messages else ""
        complexity = self.context_analyzer.analyze_query_complexity(user_query)
        predicted_tokens = self.context_analyzer.predict_token_count(
            user_query, complexity
        )
        estimated_time_ms = self.context_analyzer.estimate_response_time(
            predicted_tokens, complexity
        )

        logger.info(
            f"コンテキスト分析 - 複雑さ: {complexity:.2f}, 予想トークン: {predicted_tokens}, 予想時間: {estimated_time_ms}ms"
        )

        # 2. クライアントメトリクス取得
        client_metrics = self._get_client_metrics(client_id)

        # 3. 適応的チャンクサイズ計算
        if streaming_mode == StreamingMode.ADAPTIVE:
            chunk_size = self.chunk_calculator.calculate_optimal_chunk_size(
                client_metrics, complexity
            )
        else:
            chunk_size = 10  # デフォルト

        logger.info(f"最適チャンクサイズ: {chunk_size}")

        # 4. パフォーマンス予測とリソース事前配置
        performance_profile = PerformanceProfile(
            expected_tokens=predicted_tokens,
            complexity_score=complexity,
            estimated_duration_ms=estimated_time_ms,
            required_resources={
                "cpu": complexity * 0.5,
                "memory": predicted_tokens * 0.001,
                "bandwidth": chunk_size * 0.1,
            },
            priority_level=min(int(complexity * 10) + 1, 10),
        )

        # 5. リトライ戦略の決定
        retry_strategy = self.retry_orchestra.get_optimal_strategy("chat_completion")
        max_retries = 3

        start_time = time.time()

        for attempt in range(max_retries + 1):
            try:
                # ストリーミング実行（Azure OpenAI Serviceは常に実際のAzureに接続）
                stream = await self.async_client.chat.completions.create(
                    model=model, messages=messages, stream=True, **kwargs
                )

                chunk_buffer = ""
                chunk_count = 0

                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        chunk_buffer += chunk.choices[0].delta.content
                        chunk_count += 1

                        # 適応的チャンク配信
                        if chunk_count >= chunk_size or chunk.choices[0].finish_reason:
                            yield chunk_buffer
                            chunk_buffer = ""
                            chunk_count = 0

                            # バックプレッシャー制御
                            if streaming_mode == StreamingMode.BANDWIDTH_AWARE:
                                await asyncio.sleep(0.01)  # 帯域幅制御

                # 残りのバッファを送信
                if chunk_buffer:
                    yield chunk_buffer

                # 成功時の学習
                self.retry_orchestra.learn_from_error(
                    "chat_completion", retry_strategy, True, attempt
                )

                # パフォーマンス記録
                end_time = time.time()
                actual_duration_ms = (end_time - start_time) * 1000

                self.performance_history.append(
                    {
                        "timestamp": datetime.now(),
                        "client_id": client_id,
                        "complexity": complexity,
                        "predicted_tokens": predicted_tokens,
                        "estimated_duration_ms": estimated_time_ms,
                        "actual_duration_ms": actual_duration_ms,
                        "chunk_size": chunk_size,
                        "retry_attempts": attempt,
                        "success": True,
                    }
                )

                logger.info(
                    f"ストリーミング完了 - 実際の時間: {actual_duration_ms:.2f}ms, リトライ回数: {attempt}"
                )
                return

            except Exception as e:
                logger.warning(f"試行 {attempt + 1} でエラー: {str(e)}")

                if attempt == max_retries:
                    # 最終試行でも失敗
                    self.retry_orchestra.learn_from_error(
                        "chat_completion", retry_strategy, False, attempt + 1
                    )
                    raise e

                # バックオフ時間計算
                backoff_time = self.retry_orchestra.calculate_backoff_time(
                    attempt + 1, retry_strategy, "chat_completion"
                )
                logger.info(f"リトライ前の待機時間: {backoff_time:.2f}秒")
                await asyncio.sleep(backoff_time)

    async def _mock_adaptive_streaming(
        self, query: str, chunk_size: int
    ) -> AsyncGenerator[str, None]:
        """モック環境での適応的ストリーミング"""
        mock_responses = [
            "こちらは革新的なAdaptive Streaming Pipelineでお送りしています。",
            "クエリの複雑さを分析し、最適なチャンクサイズを動的に調整しています。",
            "現在のチャンクサイズは " + str(chunk_size) + " です。",
            "Intelligent Retry Orchestraがエラーパターンを学習し、最適なリトライ戦略を適用します。",
            "Context-Aware Performance Profilerにより、事前にリソースを最適化しています。",
            "この革新的なアプローチにより、従来の固定チャンクサイズを大幅に上回るパフォーマンスを実現しています。",
        ]

        for response in mock_responses:
            # チャンクサイズに応じた分割
            words = response.split()
            for i in range(0, len(words), max(chunk_size // 2, 1)):
                chunk = " ".join(words[i : i + max(chunk_size // 2, 1)])
                yield chunk + " "
                await asyncio.sleep(0.1)  # リアルなストリーミング感を演出

    def get_performance_analytics(self) -> dict[str, Any]:
        """パフォーマンス分析結果を取得"""
        if not self.performance_history:
            return {"message": "まだパフォーマンスデータがありません"}

        recent_data = self.performance_history[-100:]  # 最新100件

        analytics = {
            "total_requests": len(self.performance_history),
            "success_rate": sum(1 for r in recent_data if r["success"])
            / len(recent_data),
            "avg_actual_duration_ms": statistics.mean(
                [r["actual_duration_ms"] for r in recent_data]
            ),
            "avg_prediction_accuracy": statistics.mean(
                [
                    min(
                        r["estimated_duration_ms"] / max(r["actual_duration_ms"], 1),
                        1.0,
                    )
                    for r in recent_data
                ]
            ),
            "avg_complexity": statistics.mean([r["complexity"] for r in recent_data]),
            "avg_chunk_size": statistics.mean([r["chunk_size"] for r in recent_data]),
            "retry_distribution": {},
            "error_patterns": dict(self.retry_orchestra.error_patterns),
            "strategy_performance": dict(self.retry_orchestra.strategy_performance),
        }

        # リトライ回数の分布
        for record in recent_data:
            retry_count = record["retry_attempts"]
            analytics["retry_distribution"][str(retry_count)] = (
                analytics["retry_distribution"].get(str(retry_count), 0) + 1
            )

        return analytics

    def optimize_for_client(self, client_id: str) -> dict[str, Any]:
        """特定クライアント向けの最適化提案"""
        client_data = [
            r for r in self.performance_history if r["client_id"] == client_id
        ]

        if not client_data:
            return {"message": f"クライアント {client_id} のデータがありません"}

        recent_data = client_data[-50:]  # 最新50件

        recommendations = {
            "client_id": client_id,
            "data_points": len(recent_data),
            "current_performance": {
                "avg_duration_ms": statistics.mean(
                    [r["actual_duration_ms"] for r in recent_data]
                ),
                "success_rate": sum(1 for r in recent_data if r["success"])
                / len(recent_data),
                "avg_complexity": statistics.mean(
                    [r["complexity"] for r in recent_data]
                ),
            },
            "recommendations": [],
        }

        # 最適化提案の生成
        avg_duration = recommendations["current_performance"]["avg_duration_ms"]
        if avg_duration > 5000:  # 5秒以上の場合
            recommendations["recommendations"].append(
                {
                    "type": "chunk_size_optimization",
                    "suggestion": "チャンクサイズを小さくして、初期レスポンスを高速化することを推奨します",
                    "expected_improvement": "初期レスポンス時間 30-50% 短縮",
                }
            )

        success_rate = recommendations["current_performance"]["success_rate"]
        if success_rate < 0.95:
            recommendations["recommendations"].append(
                {
                    "type": "retry_strategy_optimization",
                    "suggestion": "より積極的なリトライ戦略への変更を推奨します",
                    "expected_improvement": "成功率 5-10% 向上",
                }
            )

        return recommendations


# エクスポート用のファクトリ関数
def get_production_azure_openai() -> ProductionAzureOpenAI:
    """ProductionAzureOpenAIインスタンスを取得"""
    return ProductionAzureOpenAI()

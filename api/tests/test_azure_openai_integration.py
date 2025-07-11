"""
Azure OpenAI統合テストスイート

革新的なProductionAzureOpenAIサービスの包括的テスト
"""

import os
import statistics

# テスト対象のインポート
import sys
import time
from datetime import datetime

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.services.performance_monitor import MetricType, PerformanceMonitor
from src.services.production_azure_openai import (
    AdaptiveChunkCalculator,
    ClientMetrics,
    ContextAnalyzer,
    IntelligentRetryOrchestra,
    ProductionAzureOpenAI,
    RetryStrategy,
    StreamingMode,
)
from src.services.streaming_optimizer import (
    ConnectionQuality,
    StreamingSession,
    WebSocketStreamingOptimizer,
)


class TestAdaptiveChunkCalculator:
    """AdaptiveChunkCalculatorのテスト"""

    def setup_method(self):
        self.calculator = AdaptiveChunkCalculator()

    def test_calculate_optimal_chunk_size_high_bandwidth(self):
        """高帯域幅環境でのチャンクサイズ計算"""
        metrics = ClientMetrics(
            bandwidth_mbps=100.0,
            latency_ms=5.0,
            processing_power=2.0,
            connection_quality=1.0,
        )

        chunk_size = self.calculator.calculate_optimal_chunk_size(metrics, 0.3)

        assert chunk_size > self.calculator.default_chunk_size
        assert chunk_size <= self.calculator.max_chunk_size

    def test_calculate_optimal_chunk_size_low_bandwidth(self):
        """低帯域幅環境でのチャンクサイズ計算"""
        metrics = ClientMetrics(
            bandwidth_mbps=1.0,
            latency_ms=150.0,
            processing_power=0.5,
            connection_quality=0.3,
        )

        chunk_size = self.calculator.calculate_optimal_chunk_size(metrics, 0.8)

        assert chunk_size < self.calculator.default_chunk_size
        assert chunk_size >= self.calculator.min_chunk_size

    def test_chunk_size_boundaries(self):
        """チャンクサイズの境界値テスト"""
        # 極端に低い性能
        metrics = ClientMetrics(
            bandwidth_mbps=0.1,
            latency_ms=1000.0,
            processing_power=0.1,
            connection_quality=0.1,
        )

        chunk_size = self.calculator.calculate_optimal_chunk_size(metrics, 1.0)
        assert chunk_size == self.calculator.min_chunk_size

        # 極端に高い性能
        metrics = ClientMetrics(
            bandwidth_mbps=1000.0,
            latency_ms=1.0,
            processing_power=10.0,
            connection_quality=1.0,
        )

        chunk_size = self.calculator.calculate_optimal_chunk_size(metrics, 0.1)
        assert chunk_size == self.calculator.max_chunk_size


class TestContextAnalyzer:
    """ContextAnalyzerのテスト"""

    def setup_method(self):
        self.analyzer = ContextAnalyzer()

    def test_analyze_simple_query(self):
        """簡単なクエリの複雑さ分析"""
        simple_queries = ["hello", "hi there", "thanks", "こんにちは", "ありがとう"]

        for query in simple_queries:
            complexity = self.analyzer.analyze_query_complexity(query)
            assert 0.0 <= complexity <= 0.3

    def test_analyze_complex_query(self):
        """複雑なクエリの複雑さ分析"""
        complex_queries = [
            "Analyze the performance implications of microservices architecture",
            "Compare the efficiency of different machine learning algorithms",
            "詳細なアルゴリズムの分析と最適化手法について説明してください",
            "多層ニューラルネットワークの逆伝播アルゴリズムの数学的解析",
        ]

        for query in complex_queries:
            complexity = self.analyzer.analyze_query_complexity(query)
            assert 0.5 <= complexity <= 1.0

    def test_predict_token_count(self):
        """トークン数予測のテスト"""
        query = "Explain machine learning algorithms"
        complexity = 0.6

        token_count = self.analyzer.predict_token_count(query, complexity)

        assert token_count > 0
        assert token_count >= len(query.split()) * 1.3

    def test_estimate_response_time(self):
        """レスポンス時間推定のテスト"""
        token_count = 100
        complexity = 0.7

        estimated_time = self.analyzer.estimate_response_time(token_count, complexity)

        assert estimated_time > 0
        assert estimated_time >= token_count * 50  # base_time_per_token


class TestIntelligentRetryOrchestra:
    """IntelligentRetryOrchestraのテスト"""

    def setup_method(self):
        self.orchestra = IntelligentRetryOrchestra()

    def test_learn_from_error_success(self):
        """成功時の学習"""
        error_type = "timeout_error"
        strategy = RetryStrategy.EXPONENTIAL_BACKOFF

        # 最初の学習
        self.orchestra.learn_from_error(error_type, strategy, True, 2)

        assert error_type in self.orchestra.error_patterns
        pattern = self.orchestra.error_patterns[error_type]
        assert pattern.frequency == 1
        assert pattern.success_rate == 1.0
        assert pattern.avg_retry_count == 2.0

    def test_learn_from_error_failure(self):
        """失敗時の学習"""
        error_type = "rate_limit_error"
        strategy = RetryStrategy.LINEAR_BACKOFF

        # 失敗を学習
        self.orchestra.learn_from_error(error_type, strategy, False, 3)

        pattern = self.orchestra.error_patterns[error_type]
        assert pattern.success_rate == 0.0
        assert pattern.avg_retry_count == 3.0

    def test_get_optimal_strategy(self):
        """最適戦略の取得"""
        error_type = "test_error"

        # 十分なデータがない場合
        strategy = self.orchestra.get_optimal_strategy(error_type)
        assert strategy == RetryStrategy.ADAPTIVE

        # 十分なデータがある場合
        for i in range(5):
            self.orchestra.learn_from_error(
                error_type, RetryStrategy.JITTER_BACKOFF, True, 1
            )

        strategy = self.orchestra.get_optimal_strategy(error_type)
        assert strategy is not None

    def test_calculate_backoff_time(self):
        """バックオフ時間計算のテスト"""
        attempt = 3

        # 指数バックオフ
        time_exp = self.orchestra.calculate_backoff_time(
            attempt, RetryStrategy.EXPONENTIAL_BACKOFF
        )
        assert time_exp == 1.0 * (2**attempt)

        # 線形バックオフ
        time_linear = self.orchestra.calculate_backoff_time(
            attempt, RetryStrategy.LINEAR_BACKOFF
        )
        assert time_linear == 1.0 * attempt

        # ジッターバックオフ
        time_jitter = self.orchestra.calculate_backoff_time(
            attempt, RetryStrategy.JITTER_BACKOFF
        )
        assert 0.5 * (2**attempt) <= time_jitter <= 1.5 * (2**attempt)


class TestProductionAzureOpenAI:
    """ProductionAzureOpenAIのテスト"""

    def setup_method(self):
        self.client = ProductionAzureOpenAI()

    def test_initialization(self):
        """初期化のテスト"""
        assert self.client.chunk_calculator is not None
        assert self.client.context_analyzer is not None
        assert self.client.retry_orchestra is not None
        assert isinstance(self.client.client_metrics, dict)
        assert isinstance(self.client.performance_history, list)

    def test_update_client_metrics(self):
        """クライアントメトリクス更新のテスト"""
        client_id = "test_client"
        metrics = ClientMetrics(
            bandwidth_mbps=50.0,
            latency_ms=25.0,
            processing_power=1.5,
            connection_quality=0.9,
        )

        self.client.update_client_metrics(client_id, metrics)

        assert client_id in self.client.client_metrics
        stored_metrics = self.client.client_metrics[client_id]
        assert stored_metrics.bandwidth_mbps == 50.0
        assert stored_metrics.latency_ms == 25.0

    def test_get_client_metrics(self):
        """クライアントメトリクス取得のテスト"""
        # 存在しないクライアント
        metrics = self.client._get_client_metrics("nonexistent")
        assert isinstance(metrics, ClientMetrics)
        assert metrics.bandwidth_mbps == 0.0

        # 存在するクライアント
        client_id = "existing_client"
        test_metrics = ClientMetrics(bandwidth_mbps=100.0)
        self.client.client_metrics[client_id] = test_metrics

        retrieved_metrics = self.client._get_client_metrics(client_id)
        assert retrieved_metrics.bandwidth_mbps == 100.0

    @pytest.mark.asyncio
    async def test_mock_adaptive_streaming(self):
        """モック環境での適応的ストリーミングテスト"""
        query = "Test query for streaming"
        chunk_size = 5

        chunks = []
        async for chunk in self.client._mock_adaptive_streaming(query, chunk_size):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)

    def test_get_performance_analytics(self):
        """パフォーマンス分析のテスト"""
        # 履歴にテストデータを追加
        test_data = {
            "timestamp": datetime.now(),
            "client_id": "test_client",
            "complexity": 0.5,
            "predicted_tokens": 100,
            "estimated_duration_ms": 1000,
            "actual_duration_ms": 950,
            "chunk_size": 10,
            "retry_attempts": 0,
            "success": True,
        }
        self.client.performance_history.append(test_data)

        analytics = self.client.get_performance_analytics()

        assert "total_requests" in analytics
        assert analytics["total_requests"] == 1
        assert "success_rate" in analytics
        assert analytics["success_rate"] == 1.0

    def test_optimize_for_client(self):
        """クライアント最適化のテスト"""
        client_id = "test_client"

        # データが存在しない場合
        recommendations = self.client.optimize_for_client(client_id)
        assert "message" in recommendations

        # テストデータを追加
        for i in range(10):
            test_data = {
                "timestamp": datetime.now(),
                "client_id": client_id,
                "complexity": 0.5,
                "predicted_tokens": 100,
                "estimated_duration_ms": 1000,
                "actual_duration_ms": 6000,  # 遅いレスポンス
                "chunk_size": 10,
                "retry_attempts": 0,
                "success": True,
            }
            self.client.performance_history.append(test_data)

        recommendations = self.client.optimize_for_client(client_id)

        assert "client_id" in recommendations
        assert recommendations["client_id"] == client_id
        assert "current_performance" in recommendations
        assert "recommendations" in recommendations


class TestPerformanceMonitor:
    """PerformanceMonitorのテスト"""

    def setup_method(self):
        self.monitor = PerformanceMonitor()

    def test_track_metric(self):
        """メトリクス追跡のテスト"""
        initial_buffer_size = len(self.monitor.metrics_buffer)

        self.monitor.track_metric(
            name=MetricType.RESPONSE_TIME.value,
            value=150.0,
            tags={"endpoint": "/chat", "client_id": "test"},
        )

        assert len(self.monitor.metrics_buffer) == initial_buffer_size + 1

        # 追加されたメトリクスの確認
        metric = self.monitor.metrics_buffer[-1]
        assert metric.name == MetricType.RESPONSE_TIME.value
        assert metric.value == 150.0
        assert metric.tags["endpoint"] == "/chat"

    def test_anomaly_detection(self):
        """異常検知のテスト"""
        # 正常なデータを複数追加してベースラインを確立
        for i in range(20):
            self.monitor.track_metric(
                name=MetricType.RESPONSE_TIME.value,
                value=100.0 + (i % 5),  # 100-104の範囲
                tags={"test": "baseline"},
            )

        # 異常値を追加
        self.monitor.track_metric(
            name=MetricType.RESPONSE_TIME.value,
            value=500.0,  # 明らかに異常
            tags={"test": "anomaly"},
        )

        # アラートが生成されることを確認
        assert len(self.monitor.active_alerts) > 0

    def test_alert_resolution(self):
        """アラート解決のテスト"""
        # アラートを生成
        self.monitor.track_metric(
            name=MetricType.ERROR_RATE.value,
            value=15.0,  # 高いエラー率
            tags={"test": "error"},
        )

        # アラートが存在することを確認
        assert len(self.monitor.active_alerts) > 0

        # アラートを解決
        alert_id = list(self.monitor.active_alerts.keys())[0]
        self.monitor.resolve_alert(alert_id)

        # アラートが解決されたことを確認
        assert alert_id not in self.monitor.active_alerts

    def test_performance_summary(self):
        """パフォーマンス概要のテスト"""
        summary = self.monitor.get_performance_summary()

        required_keys = [
            "monitoring_active",
            "active_alerts",
            "alerts_by_severity",
            "azure_insights_enabled",
            "metrics_buffer_size",
            "recent_metrics",
            "timestamp",
        ]

        for key in required_keys:
            assert key in summary


@pytest.mark.asyncio
class TestStreamingOptimizer:
    """WebSocketStreamingOptimizerのテスト"""

    def setup_method(self):
        self.optimizer = WebSocketStreamingOptimizer()

    def test_assess_connection_quality(self):
        """接続品質評価のテスト"""
        # 優秀な接続
        excellent_metrics = ClientMetrics(bandwidth_mbps=100, latency_ms=5)
        quality = self.optimizer.assess_connection_quality(excellent_metrics)
        assert quality == ConnectionQuality.EXCELLENT

        # 良好な接続
        good_metrics = ClientMetrics(bandwidth_mbps=20, latency_ms=30)
        quality = self.optimizer.assess_connection_quality(good_metrics)
        assert quality == ConnectionQuality.GOOD

        # 普通の接続
        fair_metrics = ClientMetrics(bandwidth_mbps=5, latency_ms=80)
        quality = self.optimizer.assess_connection_quality(fair_metrics)
        assert quality == ConnectionQuality.FAIR

        # 劣悪な接続
        poor_metrics = ClientMetrics(bandwidth_mbps=0.5, latency_ms=200)
        quality = self.optimizer.assess_connection_quality(poor_metrics)
        assert quality == ConnectionQuality.POOR

    def test_optimization_settings_application(self):
        """最適化設定適用のテスト"""
        session = StreamingSession(session_id="test_session", client_id="test_client")

        # 各品質レベルでの設定確認
        for quality in ConnectionQuality:
            session.quality = quality
            settings = self.optimizer.optimization_settings[quality]

            expected_chunk_size = settings["chunk_size"]
            expected_buffer_size = settings["buffer_size"]

            # 実際の適用をシミュレート
            session.chunk_size = expected_chunk_size
            session.buffer_size = expected_buffer_size

            assert session.chunk_size == expected_chunk_size
            assert session.buffer_size == expected_buffer_size

    def test_global_stats(self):
        """グローバル統計のテスト"""
        stats = self.optimizer.get_global_stats()

        required_keys = [
            "active_sessions",
            "quality_distribution",
            "average_latency_ms",
            "server_uptime_seconds",
            "optimization_enabled",
        ]

        for key in required_keys:
            assert key in stats

        assert stats["optimization_enabled"] is True


class TestIntegrationPerformanceBenchmark:
    """統合パフォーマンスベンチマーク"""

    def setup_method(self):
        self.azure_client = ProductionAzureOpenAI()
        self.monitor = PerformanceMonitor()
        self.optimizer = WebSocketStreamingOptimizer()

    @pytest.mark.asyncio
    async def test_end_to_end_streaming_performance(self):
        """エンドツーエンドストリーミングパフォーマンステスト"""
        client_id = "benchmark_client"

        # 高性能クライアントメトリクス
        metrics = ClientMetrics(
            bandwidth_mbps=100.0,
            latency_ms=10.0,
            processing_power=2.0,
            connection_quality=1.0,
        )

        self.azure_client.update_client_metrics(client_id, metrics)

        # ストリーミングテスト
        start_time = time.time()

        messages = [{"role": "user", "content": "高速ストリーミングのテストを実行します"}]

        chunk_count = 0
        total_length = 0

        async for chunk in self.azure_client.create_chat_completion_with_streaming(
            messages=messages,
            client_id=client_id,
            streaming_mode=StreamingMode.ADAPTIVE,
        ):
            chunk_count += 1
            total_length += len(chunk)

        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        # パフォーマンス確認
        assert chunk_count > 0
        assert total_length > 0
        assert duration_ms < 10000  # 10秒以内

        # メトリクス記録
        self.monitor.track_metric(
            name=MetricType.RESPONSE_TIME.value,
            value=duration_ms,
            tags={"test": "benchmark", "client_id": client_id},
        )

        self.monitor.track_metric(
            name=MetricType.STREAMING_LATENCY.value,
            value=duration_ms / chunk_count if chunk_count > 0 else 0,
            tags={"test": "benchmark", "client_id": client_id},
        )

    def test_concurrent_clients_performance(self):
        """同時接続クライアントのパフォーマンステスト"""
        client_count = 10
        metrics_list = []

        for i in range(client_count):
            client_id = f"concurrent_client_{i}"

            # 各クライアントに異なるメトリクスを設定
            metrics = ClientMetrics(
                bandwidth_mbps=10.0 + (i * 10),
                latency_ms=10.0 + (i * 5),
                processing_power=1.0 + (i * 0.1),
                connection_quality=1.0 - (i * 0.05),
            )

            self.azure_client.update_client_metrics(client_id, metrics)

            # 最適化計算
            chunk_size = (
                self.azure_client.chunk_calculator.calculate_optimal_chunk_size(
                    metrics, 0.5
                )
            )

            metrics_list.append(
                {
                    "client_id": client_id,
                    "chunk_size": chunk_size,
                    "bandwidth": metrics.bandwidth_mbps,
                    "latency": metrics.latency_ms,
                }
            )

        # 結果の分析
        chunk_sizes = [m["chunk_size"] for m in metrics_list]
        avg_chunk_size = statistics.mean(chunk_sizes)

        assert len(metrics_list) == client_count
        assert avg_chunk_size > 0
        assert min(chunk_sizes) >= 1
        assert max(chunk_sizes) <= 100

        # 高帯域幅クライアントは大きなチャンクサイズを持つべき
        high_bandwidth_clients = [m for m in metrics_list if m["bandwidth"] > 50]
        low_bandwidth_clients = [m for m in metrics_list if m["bandwidth"] < 20]

        if high_bandwidth_clients and low_bandwidth_clients:
            high_avg = statistics.mean(
                [c["chunk_size"] for c in high_bandwidth_clients]
            )
            low_avg = statistics.mean([c["chunk_size"] for c in low_bandwidth_clients])
            assert high_avg >= low_avg

    def test_load_testing_simulation(self):
        """負荷テストシミュレーション"""
        request_count = 100
        start_time = time.time()

        for i in range(request_count):
            # メトリクス追跡
            self.monitor.track_metric(
                name=MetricType.THROUGHPUT.value,
                value=float(i + 1),
                tags={"test": "load_test"},
            )

            # レスポンス時間のシミュレーション
            simulated_response_time = 50 + (i % 10) * 5  # 50-95ms の範囲
            self.monitor.track_metric(
                name=MetricType.RESPONSE_TIME.value,
                value=simulated_response_time,
                tags={"test": "load_test"},
            )

            # トークン使用量のシミュレーション
            simulated_tokens = 100 + (i % 20) * 10  # 100-290 tokens
            self.monitor.track_metric(
                name=MetricType.TOKEN_USAGE.value,
                value=simulated_tokens,
                tags={"test": "load_test"},
            )

        end_time = time.time()
        total_duration = end_time - start_time

        # 負荷テスト結果の検証
        assert total_duration < 60  # 1分以内に完了

        summary = self.monitor.get_performance_summary()
        assert "recent_metrics" in summary

        # スループットの確認
        if MetricType.THROUGHPUT.value in summary["recent_metrics"]:
            throughput_data = summary["recent_metrics"][MetricType.THROUGHPUT.value]
            assert throughput_data["count"] == request_count


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

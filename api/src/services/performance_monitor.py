"""
Performance Monitor - 革新的パフォーマンスモニタリングシステム

Azure Application Insightsと統合したリアルタイムパフォーマンス監視
機械学習ベースの異常検知とプロアクティブアラート
"""

import asyncio
import json
import logging
import os
import statistics
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
import redis
from opencensus.ext.azure import metrics_exporter
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.trace import config_integration
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer

from src.config.azure_config import get_azure_config

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """アラート重要度"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MetricType(Enum):
    """メトリクス種別"""

    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    TOKEN_USAGE = "token_usage"
    STREAMING_LATENCY = "streaming_latency"
    CONTEXT_COMPLEXITY = "context_complexity"
    CLIENT_SATISFACTION = "client_satisfaction"


@dataclass
class PerformanceMetric:
    """パフォーマンスメトリクス"""

    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class AnomalyDetection:
    """異常検知"""

    metric_name: str
    detected_at: datetime
    severity: AlertSeverity
    threshold: float
    actual_value: float
    description: str
    resolved: bool = False
    resolved_at: datetime | None = None


@dataclass
class PerformanceAlert:
    """パフォーマンスアラート"""

    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    created_at: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AzureInsightsIntegration:
    """Azure Application Insights統合"""

    def __init__(self):
        self.config = get_azure_config()
        self.connection_string = self.config.get("monitoring", {}).get(
            "connection_string"
        )
        self.tracer = None
        self.stats = None
        self.enabled = bool(self.connection_string)

        if self.enabled:
            self._setup_azure_insights()
        else:
            logger.warning("Azure Application Insights接続文字列が設定されていません")

    def _setup_azure_insights(self):
        """Azure Application Insights セットアップ"""
        try:
            # OpenCensus統合の設定
            config_integration.trace_integrations(["requests", "postgresql"])

            # トレーサーの設定
            self.tracer = Tracer(
                exporter=AzureExporter(connection_string=self.connection_string),
                sampler=ProbabilitySampler(1.0),
            )

            # 統計とメトリクスの設定
            self.stats = stats_module.stats
            exporter = metrics_exporter.new_metrics_exporter(
                connection_string=self.connection_string
            )

            # カスタムメトリクスの定義
            self._define_custom_metrics()

            # ログハンドラの設定
            azure_handler = AzureLogHandler(connection_string=self.connection_string)
            logger.addHandler(azure_handler)

            logger.info("Azure Application Insights統合が設定されました")

        except Exception as e:
            logger.error(f"Azure Application Insights設定エラー: {e}")
            self.enabled = False

    def _define_custom_metrics(self):
        """カスタムメトリクスの定義"""
        # レスポンス時間メトリクス
        self.response_time_measure = measure_module.MeasureFloat(
            "response_time", "Response time in milliseconds", "ms"
        )

        # スループットメトリクス
        self.throughput_measure = measure_module.MeasureInt(
            "throughput", "Requests per second", "rps"
        )

        # エラー率メトリクス
        self.error_rate_measure = measure_module.MeasureFloat(
            "error_rate", "Error rate percentage", "%"
        )

        # トークン使用量メトリクス
        self.token_usage_measure = measure_module.MeasureInt(
            "token_usage", "Tokens consumed", "tokens"
        )

    def track_metric(self, metric: PerformanceMetric):
        """メトリクスを追跡"""
        if not self.enabled:
            return

        try:
            # メトリクスタイプに応じて適切なメジャーに記録
            measure_map = self.stats.stats_recorder.new_measurement_map()

            if metric.name == MetricType.RESPONSE_TIME.value:
                measure_map.measure_float_put(self.response_time_measure, metric.value)
            elif metric.name == MetricType.THROUGHPUT.value:
                measure_map.measure_int_put(self.throughput_measure, int(metric.value))
            elif metric.name == MetricType.ERROR_RATE.value:
                measure_map.measure_float_put(self.error_rate_measure, metric.value)
            elif metric.name == MetricType.TOKEN_USAGE.value:
                measure_map.measure_int_put(self.token_usage_measure, int(metric.value))

            # タグを追加
            tag_map = {}
            for key, value in metric.tags.items():
                tag_map[key] = value

            measure_map.record(tag_map)

        except Exception as e:
            logger.error(f"メトリクス追跡エラー: {e}")

    def track_trace(
        self,
        operation_name: str,
        duration_ms: float,
        success: bool,
        metadata: dict[str, Any] = None,
    ):
        """トレースを追跡"""
        if not self.enabled or not self.tracer:
            return

        try:
            with self.tracer.span(name=operation_name) as span:
                span.add_attribute("duration_ms", duration_ms)
                span.add_attribute("success", success)

                if metadata:
                    for key, value in metadata.items():
                        span.add_attribute(key, str(value))

        except Exception as e:
            logger.error(f"トレース追跡エラー: {e}")


class AnomalyDetector:
    """機械学習ベースの異常検知システム"""

    def __init__(self):
        self.history_window = 100  # 履歴データのウィンドウサイズ
        self.metric_history: dict[str, list[float]] = {}
        self.baselines: dict[str, dict[str, float]] = {}
        self.alert_thresholds = {
            MetricType.RESPONSE_TIME: {
                "warning": 2.0,
                "critical": 3.0,
            },  # 標準偏差の倍数
            MetricType.ERROR_RATE: {"warning": 5.0, "critical": 10.0},  # パーセンテージ
            MetricType.THROUGHPUT: {"warning": 0.3, "critical": 0.5},  # 低下率
            MetricType.TOKEN_USAGE: {"warning": 1.5, "critical": 2.0},  # 平均からの倍数
        }

    def add_metric(self, metric_name: str, value: float):
        """メトリクス値を追加"""
        if metric_name not in self.metric_history:
            self.metric_history[metric_name] = []

        self.metric_history[metric_name].append(value)

        # 履歴サイズの制限
        if len(self.metric_history[metric_name]) > self.history_window:
            self.metric_history[metric_name] = self.metric_history[metric_name][
                -self.history_window :
            ]

        # ベースラインの更新
        self._update_baseline(metric_name)

    def _update_baseline(self, metric_name: str):
        """ベースラインを更新"""
        history = self.metric_history[metric_name]

        if len(history) < 10:  # 最低10個のデータポイントが必要
            return

        # 統計的ベースラインの計算
        mean = statistics.mean(history)
        std_dev = statistics.stdev(history) if len(history) > 1 else 0
        median = statistics.median(history)

        # 異常値を除外した平均（IQR法）
        q1 = np.percentile(history, 25)
        q3 = np.percentile(history, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        filtered_history = [v for v in history if lower_bound <= v <= upper_bound]
        robust_mean = statistics.mean(filtered_history) if filtered_history else mean

        self.baselines[metric_name] = {
            "mean": mean,
            "std_dev": std_dev,
            "median": median,
            "robust_mean": robust_mean,
            "q1": q1,
            "q3": q3,
            "iqr": iqr,
        }

    def detect_anomaly(self, metric_name: str, value: float) -> AnomalyDetection | None:
        """異常を検知"""
        if metric_name not in self.baselines:
            return None

        baseline = self.baselines[metric_name]

        # メトリクスタイプに応じた異常検知
        try:
            metric_type = MetricType(metric_name)
        except ValueError:
            metric_type = None

        if metric_type == MetricType.RESPONSE_TIME:
            return self._detect_response_time_anomaly(metric_name, value, baseline)
        elif metric_type == MetricType.ERROR_RATE:
            return self._detect_error_rate_anomaly(metric_name, value, baseline)
        elif metric_type == MetricType.THROUGHPUT:
            return self._detect_throughput_anomaly(metric_name, value, baseline)
        elif metric_type == MetricType.TOKEN_USAGE:
            return self._detect_token_usage_anomaly(metric_name, value, baseline)

        return None

    def _detect_response_time_anomaly(
        self, metric_name: str, value: float, baseline: dict[str, float]
    ) -> AnomalyDetection | None:
        """レスポンス時間の異常検知"""
        mean = baseline["mean"]
        std_dev = baseline["std_dev"]

        if std_dev == 0:
            return None

        z_score = abs(value - mean) / std_dev
        thresholds = self.alert_thresholds[MetricType.RESPONSE_TIME]

        if z_score > thresholds["critical"]:
            return AnomalyDetection(
                metric_name=metric_name,
                detected_at=datetime.now(),
                severity=AlertSeverity.CRITICAL,
                threshold=mean + (thresholds["critical"] * std_dev),
                actual_value=value,
                description=f"レスポンス時間が異常に高い: {value:.2f}ms (平均 + {thresholds['critical']:.1f}σ)",
            )
        elif z_score > thresholds["warning"]:
            return AnomalyDetection(
                metric_name=metric_name,
                detected_at=datetime.now(),
                severity=AlertSeverity.HIGH,
                threshold=mean + (thresholds["warning"] * std_dev),
                actual_value=value,
                description=f"レスポンス時間が警告レベル: {value:.2f}ms (平均 + {thresholds['warning']:.1f}σ)",
            )

        return None

    def _detect_error_rate_anomaly(
        self, metric_name: str, value: float, baseline: dict[str, float]
    ) -> AnomalyDetection | None:
        """エラー率の異常検知"""
        thresholds = self.alert_thresholds[MetricType.ERROR_RATE]

        if value > thresholds["critical"]:
            return AnomalyDetection(
                metric_name=metric_name,
                detected_at=datetime.now(),
                severity=AlertSeverity.CRITICAL,
                threshold=thresholds["critical"],
                actual_value=value,
                description=f"エラー率が危険レベル: {value:.2f}% (閾値: {thresholds['critical']}%)",
            )
        elif value > thresholds["warning"]:
            return AnomalyDetection(
                metric_name=metric_name,
                detected_at=datetime.now(),
                severity=AlertSeverity.HIGH,
                threshold=thresholds["warning"],
                actual_value=value,
                description=f"エラー率が警告レベル: {value:.2f}% (閾値: {thresholds['warning']}%)",
            )

        return None

    def _detect_throughput_anomaly(
        self, metric_name: str, value: float, baseline: dict[str, float]
    ) -> AnomalyDetection | None:
        """スループットの異常検知"""
        mean = baseline["mean"]
        thresholds = self.alert_thresholds[MetricType.THROUGHPUT]

        # スループットの低下を検知
        decline_rate = (mean - value) / mean if mean > 0 else 0

        if decline_rate > thresholds["critical"]:
            return AnomalyDetection(
                metric_name=metric_name,
                detected_at=datetime.now(),
                severity=AlertSeverity.CRITICAL,
                threshold=mean * (1 - thresholds["critical"]),
                actual_value=value,
                description=f"スループットが大幅低下: {value:.2f} (平均比 -{decline_rate*100:.1f}%)",
            )
        elif decline_rate > thresholds["warning"]:
            return AnomalyDetection(
                metric_name=metric_name,
                detected_at=datetime.now(),
                severity=AlertSeverity.HIGH,
                threshold=mean * (1 - thresholds["warning"]),
                actual_value=value,
                description=f"スループットが低下: {value:.2f} (平均比 -{decline_rate*100:.1f}%)",
            )

        return None

    def _detect_token_usage_anomaly(
        self, metric_name: str, value: float, baseline: dict[str, float]
    ) -> AnomalyDetection | None:
        """トークン使用量の異常検知"""
        mean = baseline["mean"]
        thresholds = self.alert_thresholds[MetricType.TOKEN_USAGE]

        usage_ratio = value / mean if mean > 0 else 0

        if usage_ratio > thresholds["critical"]:
            return AnomalyDetection(
                metric_name=metric_name,
                detected_at=datetime.now(),
                severity=AlertSeverity.CRITICAL,
                threshold=mean * thresholds["critical"],
                actual_value=value,
                description=f"トークン使用量が異常に高い: {value} (平均の {usage_ratio:.1f}倍)",
            )
        elif usage_ratio > thresholds["warning"]:
            return AnomalyDetection(
                metric_name=metric_name,
                detected_at=datetime.now(),
                severity=AlertSeverity.HIGH,
                threshold=mean * thresholds["warning"],
                actual_value=value,
                description=f"トークン使用量が警告レベル: {value} (平均の {usage_ratio:.1f}倍)",
            )

        return None


class PerformanceMonitor:
    """統合パフォーマンスモニタリングシステム"""

    def __init__(self):
        self.azure_insights = AzureInsightsIntegration()
        self.anomaly_detector = AnomalyDetector()
        self.active_alerts: dict[str, PerformanceAlert] = {}
        self.alert_history: list[PerformanceAlert] = []
        self.metrics_buffer: list[PerformanceMetric] = []
        self.running = False

        # Redis設定（オプション）
        self.redis_client = None
        try:
            self.redis_client = redis.Redis(
                host=os.environ.get("REDIS_HOST", "localhost"),
                port=int(os.environ.get("REDIS_PORT", 6379)),
                decode_responses=True,
            )
        except:
            logger.warning("Redis接続に失敗しました。メトリクス永続化は無効化されます。")

        # アラート通知設定
        self.alert_callbacks: list[Callable[[PerformanceAlert], None]] = []

    def start_monitoring(self):
        """モニタリング開始"""
        if self.running:
            return

        self.running = True
        logger.info("パフォーマンスモニタリングを開始しました")

        # バックグラウンドタスクを開始
        asyncio.create_task(self.process_metrics_buffer())
        asyncio.create_task(self.alert_cleanup_task())

    def stop_monitoring(self):
        """モニタリング停止"""
        self.running = False
        logger.info("パフォーマンスモニタリングを停止しました")

    def track_metric(
        self,
        name: str,
        value: float,
        tags: dict[str, str] = None,
        metadata: dict[str, Any] = None,
    ):
        """メトリクスを追跡"""
        metric = PerformanceMetric(
            name=name, value=value, tags=tags or {}, metadata=metadata or {}
        )

        # バッファに追加
        self.metrics_buffer.append(metric)

        # 即座に異常検知を実行
        self._check_for_anomalies(metric)

    def _check_for_anomalies(self, metric: PerformanceMetric):
        """異常検知を実行"""
        # 履歴に追加
        self.anomaly_detector.add_metric(metric.name, metric.value)

        # 異常検知
        anomaly = self.anomaly_detector.detect_anomaly(metric.name, metric.value)

        if anomaly:
            # アラートを生成
            alert = PerformanceAlert(
                alert_id=f"alert_{int(time.time() * 1000)}",
                severity=anomaly.severity,
                title=f"パフォーマンス異常検知: {metric.name}",
                description=anomaly.description,
                metadata={
                    "metric_name": metric.name,
                    "threshold": anomaly.threshold,
                    "actual_value": anomaly.actual_value,
                    "metric_tags": metric.tags,
                    "metric_metadata": metric.metadata,
                },
            )

            self._handle_alert(alert)

    def _handle_alert(self, alert: PerformanceAlert):
        """アラートを処理"""
        # アクティブアラートに追加
        self.active_alerts[alert.alert_id] = alert
        self.alert_history.append(alert)

        logger.warning(f"パフォーマンスアラート発生: {alert.title} - {alert.description}")

        # 登録されたコールバックを実行
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"アラートコールバックエラー: {e}")

        # Redisに永続化
        if self.redis_client:
            try:
                self.redis_client.setex(
                    f"alert:{alert.alert_id}",
                    3600,  # 1時間TTL
                    json.dumps(
                        {
                            "alert_id": alert.alert_id,
                            "severity": alert.severity.value,
                            "title": alert.title,
                            "description": alert.description,
                            "created_at": alert.created_at.isoformat(),
                            "metadata": alert.metadata,
                        }
                    ),
                )
            except Exception as e:
                logger.error(f"アラート永続化エラー: {e}")

    def resolve_alert(self, alert_id: str):
        """アラートを解決"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()

            del self.active_alerts[alert_id]
            logger.info(f"アラート解決: {alert_id}")

    def register_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """アラートコールバックを登録"""
        self.alert_callbacks.append(callback)

    async def process_metrics_buffer(self):
        """メトリクスバッファを処理"""
        while self.running:
            try:
                if self.metrics_buffer:
                    # バッファからメトリクスを取得
                    metrics_to_process = self.metrics_buffer.copy()
                    self.metrics_buffer.clear()

                    # Azure Insightsに送信
                    for metric in metrics_to_process:
                        self.azure_insights.track_metric(metric)

                    logger.debug(f"{len(metrics_to_process)}個のメトリクスを処理しました")

            except Exception as e:
                logger.error(f"メトリクス処理エラー: {e}")

            await asyncio.sleep(10)  # 10秒間隔で処理

    async def alert_cleanup_task(self):
        """古いアラートのクリーンアップ"""
        while self.running:
            try:
                current_time = datetime.now()

                # 24時間以上前のアラート履歴を削除
                self.alert_history = [
                    alert
                    for alert in self.alert_history
                    if (current_time - alert.created_at).total_seconds() < 86400
                ]

                # 解決済みアラートを削除
                resolved_alerts = [
                    alert_id
                    for alert_id, alert in self.active_alerts.items()
                    if alert.resolved
                ]

                for alert_id in resolved_alerts:
                    del self.active_alerts[alert_id]

            except Exception as e:
                logger.error(f"アラートクリーンアップエラー: {e}")

            await asyncio.sleep(3600)  # 1時間間隔でクリーンアップ

    def get_performance_summary(self) -> dict[str, Any]:
        """パフォーマンス概要を取得"""
        active_alert_count = len(self.active_alerts)
        alert_by_severity = {}

        for alert in self.active_alerts.values():
            severity = alert.severity.value
            alert_by_severity[severity] = alert_by_severity.get(severity, 0) + 1

        # 最近のメトリクス統計
        recent_metrics = {}
        for metric_name, history in self.anomaly_detector.metric_history.items():
            if history:
                recent_metrics[metric_name] = {
                    "current": history[-1],
                    "average": statistics.mean(history),
                    "min": min(history),
                    "max": max(history),
                    "count": len(history),
                }

        return {
            "monitoring_active": self.running,
            "active_alerts": active_alert_count,
            "alerts_by_severity": alert_by_severity,
            "azure_insights_enabled": self.azure_insights.enabled,
            "metrics_buffer_size": len(self.metrics_buffer),
            "recent_metrics": recent_metrics,
            "timestamp": datetime.now().isoformat(),
        }

    def get_active_alerts(self) -> list[dict[str, Any]]:
        """アクティブアラート一覧を取得"""
        return [
            {
                "alert_id": alert.alert_id,
                "severity": alert.severity.value,
                "title": alert.title,
                "description": alert.description,
                "created_at": alert.created_at.isoformat(),
                "metadata": alert.metadata,
            }
            for alert in self.active_alerts.values()
        ]


# グローバルインスタンス
performance_monitor = PerformanceMonitor()


# エクスポート用の関数
def get_performance_monitor() -> PerformanceMonitor:
    """パフォーマンスモニターインスタンスを取得"""
    return performance_monitor


def start_performance_monitoring():
    """パフォーマンス監視を開始"""
    performance_monitor.start_monitoring()


def stop_performance_monitoring():
    """パフォーマンス監視を停止"""
    performance_monitor.stop_monitoring()


# メトリクス追跡のヘルパー関数
def track_response_time(duration_ms: float, endpoint: str = "", client_id: str = ""):
    """レスポンス時間を追跡"""
    performance_monitor.track_metric(
        name=MetricType.RESPONSE_TIME.value,
        value=duration_ms,
        tags={"endpoint": endpoint, "client_id": client_id},
    )


def track_throughput(requests_per_second: float, endpoint: str = ""):
    """スループットを追跡"""
    performance_monitor.track_metric(
        name=MetricType.THROUGHPUT.value,
        value=requests_per_second,
        tags={"endpoint": endpoint},
    )


def track_error_rate(error_percentage: float, endpoint: str = "", error_type: str = ""):
    """エラー率を追跡"""
    performance_monitor.track_metric(
        name=MetricType.ERROR_RATE.value,
        value=error_percentage,
        tags={"endpoint": endpoint, "error_type": error_type},
    )


def track_token_usage(token_count: int, model: str = "", client_id: str = ""):
    """トークン使用量を追跡"""
    performance_monitor.track_metric(
        name=MetricType.TOKEN_USAGE.value,
        value=token_count,
        tags={"model": model, "client_id": client_id},
    )

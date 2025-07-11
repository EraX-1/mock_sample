"""
Streaming Optimizer - 革新的ストリーミング最適化システム

WebSocketベースの双方向通信により、リアルタイムでストリーミング品質を最適化
"""

import asyncio
import json
import logging
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import websockets

from src.services.azure_openai import ClientMetrics, StreamingMode

logger = logging.getLogger(__name__)


class ConnectionQuality(Enum):
    """接続品質レベル"""

    EXCELLENT = "excellent"  # > 50 Mbps, < 10ms latency
    GOOD = "good"  # 10-50 Mbps, 10-50ms latency
    FAIR = "fair"  # 1-10 Mbps, 50-100ms latency
    POOR = "poor"  # < 1 Mbps, > 100ms latency


@dataclass
class StreamingSession:
    """ストリーミングセッション"""

    session_id: str
    client_id: str
    websocket: Any = None
    start_time: datetime = field(default_factory=datetime.now)
    metrics: ClientMetrics = field(default_factory=ClientMetrics)
    quality: ConnectionQuality = ConnectionQuality.GOOD
    chunk_size: int = 10
    buffer_size: int = 1024
    adaptive_mode: bool = True
    stats: dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamingStats:
    """ストリーミング統計"""

    total_chunks: int = 0
    total_bytes: int = 0
    avg_chunk_latency_ms: float = 0.0
    buffer_underruns: int = 0
    quality_adjustments: int = 0
    last_update: datetime = field(default_factory=datetime.now)


class WebSocketStreamingOptimizer:
    """WebSocketベースのストリーミング最適化システム"""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.sessions: dict[str, StreamingSession] = {}
        self.server = None
        self.running = False

        # 最適化パラメータ
        self.quality_thresholds = {
            ConnectionQuality.EXCELLENT: {"bandwidth_mbps": 50, "latency_ms": 10},
            ConnectionQuality.GOOD: {"bandwidth_mbps": 10, "latency_ms": 50},
            ConnectionQuality.FAIR: {"bandwidth_mbps": 1, "latency_ms": 100},
            ConnectionQuality.POOR: {"bandwidth_mbps": 0, "latency_ms": float("inf")},
        }

        # 品質別最適化設定
        self.optimization_settings = {
            ConnectionQuality.EXCELLENT: {
                "chunk_size": 50,
                "buffer_size": 4096,
                "compression": False,
            },
            ConnectionQuality.GOOD: {
                "chunk_size": 20,
                "buffer_size": 2048,
                "compression": False,
            },
            ConnectionQuality.FAIR: {
                "chunk_size": 10,
                "buffer_size": 1024,
                "compression": True,
            },
            ConnectionQuality.POOR: {
                "chunk_size": 5,
                "buffer_size": 512,
                "compression": True,
            },
        }

    async def start_server(self):
        """WebSocketサーバーを開始"""
        logger.info(f"WebSocket最適化サーバーを開始: {self.host}:{self.port}")

        self.server = await websockets.serve(
            self.handle_client, self.host, self.port, ping_interval=20, ping_timeout=10
        )

        self.running = True

        # バックグラウンドタスクを開始
        asyncio.create_task(self.monitor_sessions())
        asyncio.create_task(self.adaptive_optimizer())

        logger.info("WebSocket最適化サーバーが開始されました")

    async def stop_server(self):
        """WebSocketサーバーを停止"""
        if self.server:
            logger.info("WebSocket最適化サーバーを停止中...")
            self.running = False
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket最適化サーバーが停止されました")

    async def handle_client(self, websocket, path):
        """クライアント接続を処理"""
        session_id = f"session_{int(time.time() * 1000)}"
        client_id = (
            f"client_{websocket.remote_address[0]}_{websocket.remote_address[1]}"
        )

        session = StreamingSession(
            session_id=session_id, client_id=client_id, websocket=websocket
        )

        self.sessions[session_id] = session
        logger.info(f"新しいクライアント接続: {client_id} (セッション: {session_id})")

        try:
            # 初期接続品質テスト
            await self.perform_connection_test(session)

            # クライアントメッセージを処理
            async for message in websocket:
                await self.handle_message(session, message)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"クライアント切断: {client_id}")
        except Exception as e:
            logger.error(f"クライアント処理エラー: {e}")
        finally:
            # セッションをクリーンアップ
            if session_id in self.sessions:
                del self.sessions[session_id]

    async def perform_connection_test(self, session: StreamingSession):
        """接続品質テスト"""
        logger.info(f"接続品質テスト開始: {session.client_id}")

        # 帯域幅テスト
        test_data = "x" * 1024  # 1KB のテストデータ
        start_time = time.time()

        try:
            await session.websocket.send(
                json.dumps(
                    {
                        "type": "bandwidth_test",
                        "data": test_data,
                        "timestamp": start_time,
                    }
                )
            )

            # レスポンス待機（タイムアウト5秒）
            response = await asyncio.wait_for(session.websocket.recv(), timeout=5.0)

            end_time = time.time()
            round_trip_time = (end_time - start_time) * 1000  # ms

            # メトリクス更新
            session.metrics.latency_ms = round_trip_time
            session.metrics.bandwidth_mbps = (
                (len(test_data) * 8) / (round_trip_time / 1000) / 1_000_000
            )
            session.metrics.timestamp = datetime.now()

            # 接続品質を判定
            session.quality = self.assess_connection_quality(session.metrics)

            # 最適化設定を適用
            await self.apply_optimization_settings(session)

            logger.info(
                f"接続品質テスト完了: {session.client_id}, "
                f"品質: {session.quality.value}, "
                f"帯域幅: {session.metrics.bandwidth_mbps:.2f}Mbps, "
                f"レイテンシ: {session.metrics.latency_ms:.2f}ms"
            )

        except TimeoutError:
            logger.warning(f"接続品質テストタイムアウト: {session.client_id}")
            session.quality = ConnectionQuality.POOR
            await self.apply_optimization_settings(session)
        except Exception as e:
            logger.error(f"接続品質テストエラー: {e}")
            session.quality = ConnectionQuality.FAIR
            await self.apply_optimization_settings(session)

    def assess_connection_quality(self, metrics: ClientMetrics) -> ConnectionQuality:
        """接続品質を評価"""
        if metrics.bandwidth_mbps >= 50 and metrics.latency_ms <= 10:
            return ConnectionQuality.EXCELLENT
        elif metrics.bandwidth_mbps >= 10 and metrics.latency_ms <= 50:
            return ConnectionQuality.GOOD
        elif metrics.bandwidth_mbps >= 1 and metrics.latency_ms <= 100:
            return ConnectionQuality.FAIR
        else:
            return ConnectionQuality.POOR

    async def apply_optimization_settings(self, session: StreamingSession):
        """最適化設定を適用"""
        settings = self.optimization_settings[session.quality]

        session.chunk_size = settings["chunk_size"]
        session.buffer_size = settings["buffer_size"]

        # クライアントに最適化設定を送信
        await session.websocket.send(
            json.dumps(
                {
                    "type": "optimization_settings",
                    "session_id": session.session_id,
                    "settings": {
                        "chunk_size": session.chunk_size,
                        "buffer_size": session.buffer_size,
                        "quality": session.quality.value,
                        "compression": settings["compression"],
                    },
                    "timestamp": time.time(),
                }
            )
        )

        logger.info(
            f"最適化設定適用: {session.client_id}, "
            f"チャンクサイズ: {session.chunk_size}, "
            f"バッファサイズ: {session.buffer_size}"
        )

    async def handle_message(self, session: StreamingSession, message: str):
        """クライアントメッセージを処理"""
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "metrics_report":
                await self.handle_metrics_report(session, data)
            elif message_type == "quality_feedback":
                await self.handle_quality_feedback(session, data)
            elif message_type == "streaming_request":
                await self.handle_streaming_request(session, data)
            else:
                logger.warning(f"未知のメッセージタイプ: {message_type}")

        except json.JSONDecodeError:
            logger.error(f"無効なJSONメッセージ: {message}")
        except Exception as e:
            logger.error(f"メッセージ処理エラー: {e}")

    async def handle_metrics_report(
        self, session: StreamingSession, data: dict[str, Any]
    ):
        """メトリクスレポートを処理"""
        metrics_data = data.get("metrics", {})

        # クライアントメトリクスの更新
        session.metrics.bandwidth_mbps = metrics_data.get(
            "bandwidth_mbps", session.metrics.bandwidth_mbps
        )
        session.metrics.latency_ms = metrics_data.get(
            "latency_ms", session.metrics.latency_ms
        )
        session.metrics.processing_power = metrics_data.get(
            "processing_power", session.metrics.processing_power
        )
        session.metrics.connection_quality = metrics_data.get(
            "connection_quality", session.metrics.connection_quality
        )
        session.metrics.timestamp = datetime.now()

        # 品質の再評価
        new_quality = self.assess_connection_quality(session.metrics)
        if new_quality != session.quality:
            logger.info(
                f"品質変更検出: {session.client_id}, "
                f"{session.quality.value} → {new_quality.value}"
            )
            session.quality = new_quality
            await self.apply_optimization_settings(session)

    async def handle_quality_feedback(
        self, session: StreamingSession, data: dict[str, Any]
    ):
        """品質フィードバックを処理"""
        feedback = data.get("feedback", {})

        # ユーザーが品質に不満を感じている場合
        if feedback.get("quality_rating", 5) < 3:
            # より保守的な設定に変更
            session.chunk_size = max(session.chunk_size // 2, 1)
            session.buffer_size = max(session.buffer_size // 2, 256)

            await self.apply_optimization_settings(session)
            logger.info(f"品質フィードバックに基づく調整: {session.client_id}")

    async def handle_streaming_request(
        self, session: StreamingSession, data: dict[str, Any]
    ):
        """ストリーミングリクエストを処理"""
        request_id = data.get("request_id")
        query = data.get("query", "")

        # ProductionAzureOpenAIにストリーミングを依頼
        from src.services.production_azure_openai import get_production_azure_openai

        azure_client = get_production_azure_openai()

        # クライアントメトリクスを更新
        azure_client.update_client_metrics(session.client_id, session.metrics)

        try:
            # ストリーミング開始の通知
            await session.websocket.send(
                json.dumps(
                    {
                        "type": "streaming_start",
                        "request_id": request_id,
                        "timestamp": time.time(),
                    }
                )
            )

            # ストリーミング実行
            messages = [{"role": "user", "content": query}]

            async for chunk in azure_client.create_chat_completion_with_streaming(
                messages=messages,
                client_id=session.client_id,
                streaming_mode=StreamingMode.ADAPTIVE,
            ):
                # 最適化されたチャンクを送信
                await session.websocket.send(
                    json.dumps(
                        {
                            "type": "streaming_chunk",
                            "request_id": request_id,
                            "chunk": chunk,
                            "timestamp": time.time(),
                        }
                    )
                )

                # バックプレッシャー制御
                if session.quality == ConnectionQuality.POOR:
                    await asyncio.sleep(0.05)  # 低品質接続では少し待機

            # ストリーミング完了の通知
            await session.websocket.send(
                json.dumps(
                    {
                        "type": "streaming_complete",
                        "request_id": request_id,
                        "timestamp": time.time(),
                    }
                )
            )

        except Exception as e:
            # エラー通知
            await session.websocket.send(
                json.dumps(
                    {
                        "type": "streaming_error",
                        "request_id": request_id,
                        "error": str(e),
                        "timestamp": time.time(),
                    }
                )
            )

    async def monitor_sessions(self):
        """セッションを監視"""
        while self.running:
            try:
                # 非アクティブセッションの検出
                current_time = datetime.now()
                inactive_sessions = []

                for session_id, session in self.sessions.items():
                    if (
                        current_time - session.start_time
                    ).total_seconds() > 3600:  # 1時間
                        inactive_sessions.append(session_id)

                # 非アクティブセッションの削除
                for session_id in inactive_sessions:
                    if session_id in self.sessions:
                        logger.info(f"非アクティブセッションを削除: {session_id}")
                        del self.sessions[session_id]

                # セッション統計の更新
                await self.update_session_stats()

            except Exception as e:
                logger.error(f"セッション監視エラー: {e}")

            await asyncio.sleep(60)  # 1分間隔で監視

    async def adaptive_optimizer(self):
        """適応的最適化"""
        while self.running:
            try:
                for session in self.sessions.values():
                    if session.adaptive_mode:
                        await self.perform_adaptive_optimization(session)

            except Exception as e:
                logger.error(f"適応的最適化エラー: {e}")

            await asyncio.sleep(30)  # 30秒間隔で最適化

    async def perform_adaptive_optimization(self, session: StreamingSession):
        """セッション個別の適応的最適化"""
        # 最近のパフォーマンス分析
        if len(session.stats.get("latency_history", [])) < 5:
            return  # データ不足

        latency_history = session.stats["latency_history"][-10:]  # 最新10個
        avg_latency = statistics.mean(latency_history)
        latency_variance = (
            statistics.variance(latency_history) if len(latency_history) > 1 else 0
        )

        # 不安定な接続の検出
        if latency_variance > 100:  # 高い分散
            # より小さなチャンクサイズに調整
            new_chunk_size = max(session.chunk_size - 2, 1)
            if new_chunk_size != session.chunk_size:
                session.chunk_size = new_chunk_size
                await self.apply_optimization_settings(session)
                logger.info(f"不安定接続に適応: {session.client_id}, チャンクサイズ: {new_chunk_size}")

        # 安定した高性能接続の検出
        elif avg_latency < 50 and latency_variance < 25:
            # より大きなチャンクサイズに調整
            max_chunk_size = self.optimization_settings[ConnectionQuality.EXCELLENT][
                "chunk_size"
            ]
            new_chunk_size = min(session.chunk_size + 1, max_chunk_size)
            if new_chunk_size != session.chunk_size:
                session.chunk_size = new_chunk_size
                await self.apply_optimization_settings(session)
                logger.info(f"安定接続に適応: {session.client_id}, チャンクサイズ: {new_chunk_size}")

    async def update_session_stats(self):
        """セッション統計を更新"""
        for session in self.sessions.values():
            if "latency_history" not in session.stats:
                session.stats["latency_history"] = []

            # 現在のレイテンシを追加
            session.stats["latency_history"].append(session.metrics.latency_ms)

            # 履歴サイズの制限
            if len(session.stats["latency_history"]) > 100:
                session.stats["latency_history"] = session.stats["latency_history"][
                    -50:
                ]

    def get_global_stats(self) -> dict[str, Any]:
        """グローバル統計を取得"""
        active_sessions = len(self.sessions)
        quality_distribution = {}

        for session in self.sessions.values():
            quality = session.quality.value
            quality_distribution[quality] = quality_distribution.get(quality, 0) + 1

        avg_latency = 0
        if self.sessions:
            avg_latency = statistics.mean(
                [s.metrics.latency_ms for s in self.sessions.values()]
            )

        return {
            "active_sessions": active_sessions,
            "quality_distribution": quality_distribution,
            "average_latency_ms": avg_latency,
            "server_uptime_seconds": (
                datetime.now() - datetime(2024, 1, 1)
            ).total_seconds(),
            "optimization_enabled": True,
        }


# グローバルインスタンス
streaming_optimizer = WebSocketStreamingOptimizer()


# エクスポート用の関数
async def start_streaming_optimization_server():
    """ストリーミング最適化サーバーを開始"""
    await streaming_optimizer.start_server()


async def stop_streaming_optimization_server():
    """ストリーミング最適化サーバーを停止"""
    await streaming_optimizer.stop_server()


def get_streaming_optimizer() -> WebSocketStreamingOptimizer:
    """ストリーミング最適化インスタンスを取得"""
    return streaming_optimizer

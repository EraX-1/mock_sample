# パフォーマンステストとベンチマーク - Production Load Testing

import pytest
import asyncio
import time
import statistics
import json
import psutil
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass
import numpy as np
import os

# テスト対象のimports
from api.services.chat_service import ChatService
from tests.integration.test_azure_services_integration import AdvancedAzureOpenAIMock

# ========================================
# パフォーマンステスト用データクラス
# ========================================


@dataclass
class LoadTestResult:
    """負荷テスト結果"""

    test_name: str
    concurrent_users: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_duration: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    throughput: float  # requests per second
    error_rate: float
    cpu_usage_avg: float
    memory_usage_avg: float
    memory_peak: float


@dataclass
class BenchmarkTarget:
    """ベンチマーク目標値"""

    max_avg_response_time: float = 3.0  # 3秒
    max_p95_response_time: float = 5.0  # 5秒
    max_p99_response_time: float = 8.0  # 8秒
    min_throughput: float = 10.0  # 10 req/sec
    max_error_rate: float = 0.05  # 5%
    max_cpu_usage: float = 80.0  # 80%
    max_memory_usage: float = 2048.0  # 2GB


class SystemResourceMonitor:
    """システムリソース監視"""

    def __init__(self, interval: float = 0.5):
        self.interval = interval
        self.monitoring = False
        self.cpu_readings = []
        self.memory_readings = []
        self.monitor_thread = None

    def start_monitoring(self):
        """監視開始"""
        self.monitoring = True
        self.cpu_readings = []
        self.memory_readings = []
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()

    def stop_monitoring(self) -> Dict[str, float]:
        """監視停止と結果取得"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()

        if not self.cpu_readings or not self.memory_readings:
            return {"cpu_avg": 0.0, "memory_avg": 0.0, "memory_peak": 0.0}

        return {
            "cpu_avg": statistics.mean(self.cpu_readings),
            "memory_avg": statistics.mean(self.memory_readings),
            "memory_peak": max(self.memory_readings),
        }

    def _monitor_loop(self):
        """監視ループ"""
        process = psutil.Process()

        while self.monitoring:
            try:
                # CPU使用率
                cpu_percent = process.cpu_percent()
                self.cpu_readings.append(cpu_percent)

                # メモリ使用量（MB）
                memory_mb = process.memory_info().rss / 1024 / 1024
                self.memory_readings.append(memory_mb)

                time.sleep(self.interval)
            except Exception as e:
                print(f"監視エラー: {e}")
                break


class LoadTestScenario:
    """負荷テストシナリオ"""

    def __init__(
        self, name: str, queries: List[str], concurrent_users: int, duration: int
    ):
        self.name = name
        self.queries = queries
        self.concurrent_users = concurrent_users
        self.duration = duration  # 秒
        self.results = []
        self.errors = []


# ========================================
# 負荷テストスイート
# ========================================


class TestLoadPerformance:
    """負荷テストとパフォーマンステスト"""

    @pytest.fixture
    def chat_service_with_mock(self):
        """モック付きチャットサービス"""
        service = ChatService()
        mock_openai = AdvancedAzureOpenAIMock()
        mock_openai.enable_latency_simulation(0.5)  # 500ms base latency
        service.openai_service = mock_openai
        return service, mock_openai

    @pytest.fixture
    def load_test_scenarios(self):
        """負荷テストシナリオの定義"""
        return [
            LoadTestScenario(
                name="light_load",
                queries=[
                    "Azure OpenAIの基本的な使い方は？",
                    "RAGシステムの概要を教えて",
                    "機械学習の基礎について",
                    "クラウドサービスのメリットは？",
                ],
                concurrent_users=5,
                duration=30,
            ),
            LoadTestScenario(
                name="medium_load",
                queries=[
                    "Azure OpenAIの詳細な設定方法",
                    "RAGシステムの実装で注意すべき点",
                    "データベース設計のベストプラクティス",
                    "セキュリティ対策の具体的な方法",
                    "パフォーマンスチューニングのテクニック",
                ],
                concurrent_users=15,
                duration=60,
            ),
            LoadTestScenario(
                name="heavy_load",
                queries=[
                    "複雑なシステム統合における課題と解決策",
                    "大規模データ処理のアーキテクチャ設計",
                    "マイクロサービス間の通信最適化",
                    "分散システムでの一貫性保証",
                    "リアルタイム分析システムの構築方法",
                    "機械学習パイプラインの運用監視",
                    "セキュリティインシデント対応プロセス",
                ],
                concurrent_users=30,
                duration=90,
            ),
        ]

    @pytest.mark.load
    async def test_progressive_load_testing(
        self, chat_service_with_mock, load_test_scenarios
    ):
        """段階的負荷テスト"""
        chat_service, mock_openai = chat_service_with_mock
        benchmark = BenchmarkTarget()

        results = []

        for scenario in load_test_scenarios:
            print(f"\n=== {scenario.name.upper()} 負荷テスト開始 ===")
            print(f"並行ユーザー数: {scenario.concurrent_users}")
            print(f"テスト期間: {scenario.duration}秒")

            # システムリソース監視開始
            monitor = SystemResourceMonitor()
            monitor.start_monitoring()

            # 負荷テスト実行
            result = await self._execute_load_test(chat_service, scenario)

            # 監視停止
            resource_metrics = monitor.stop_monitoring()
            result.cpu_usage_avg = resource_metrics["cpu_avg"]
            result.memory_usage_avg = resource_metrics["memory_avg"]
            result.memory_peak = resource_metrics["memory_peak"]

            results.append(result)

            # 結果の表示と検証
            self._print_load_test_results(result)
            self._verify_performance_targets(result, benchmark)

            # 次のテストまでの回復時間
            print("システム回復待機中...")
            await asyncio.sleep(10)

        # 全体結果の分析
        self._analyze_progressive_results(results)

        return results

    async def _execute_load_test(
        self, chat_service: ChatService, scenario: LoadTestScenario
    ) -> LoadTestResult:
        """負荷テスト実行"""

        # ワーカータスクの作成
        async def worker_task(worker_id: int):
            """個別ワーカーのタスク"""
            worker_results = []
            worker_errors = []

            end_time = time.time() + scenario.duration

            while time.time() < end_time:
                for query in scenario.queries:
                    if time.time() >= end_time:
                        break

                    try:
                        start_time = time.time()
                        response = await chat_service.process_message(
                            f"{query} (Worker {worker_id})"
                        )
                        response_time = time.time() - start_time

                        worker_results.append(
                            {
                                "response_time": response_time,
                                "success": response.success
                                if hasattr(response, "success")
                                else True,
                                "worker_id": worker_id,
                            }
                        )

                    except Exception as e:
                        worker_errors.append(
                            {
                                "error": str(e),
                                "worker_id": worker_id,
                                "timestamp": time.time(),
                            }
                        )

                # 短い間隔でのリクエスト間隔
                await asyncio.sleep(0.1)

            return worker_results, worker_errors

        # 全ワーカーの実行
        start_time = time.time()
        tasks = [worker_task(i) for i in range(scenario.concurrent_users)]
        worker_results = await asyncio.gather(*tasks, return_exceptions=True)
        total_duration = time.time() - start_time

        # 結果の集計
        all_results = []
        all_errors = []

        for worker_result in worker_results:
            if isinstance(worker_result, Exception):
                all_errors.append({"error": str(worker_result), "worker_id": "unknown"})
            else:
                results, errors = worker_result
                all_results.extend(results)
                all_errors.extend(errors)

        # 統計計算
        response_times = [r["response_time"] for r in all_results]
        successful_requests = sum(1 for r in all_results if r["success"])
        failed_requests = len(all_results) - successful_requests + len(all_errors)

        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p50_response_time = np.percentile(response_times, 50)
            p95_response_time = np.percentile(response_times, 95)
            p99_response_time = np.percentile(response_times, 99)
        else:
            avg_response_time = min_response_time = max_response_time = 0
            p50_response_time = p95_response_time = p99_response_time = 0

        total_requests = len(all_results) + len(all_errors)
        throughput = total_requests / total_duration if total_duration > 0 else 0
        error_rate = failed_requests / total_requests if total_requests > 0 else 0

        return LoadTestResult(
            test_name=scenario.name,
            concurrent_users=scenario.concurrent_users,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_duration=total_duration,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p50_response_time=p50_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            throughput=throughput,
            error_rate=error_rate,
            cpu_usage_avg=0.0,  # 後で設定
            memory_usage_avg=0.0,  # 後で設定
            memory_peak=0.0,  # 後で設定
        )

    def _print_load_test_results(self, result: LoadTestResult):
        """負荷テスト結果の表示"""
        print(f"\n📊 {result.test_name} 結果:")
        print(f"   総リクエスト数: {result.total_requests}")
        print(f"   成功: {result.successful_requests}, 失敗: {result.failed_requests}")
        print(f"   成功率: {(1-result.error_rate)*100:.1f}%")
        print(f"   スループット: {result.throughput:.1f} req/sec")
        print(f"   レスポンス時間 (平均): {result.avg_response_time:.2f}s")
        print(f"   レスポンス時間 (P95): {result.p95_response_time:.2f}s")
        print(f"   レスポンス時間 (P99): {result.p99_response_time:.2f}s")
        print(f"   CPU使用率 (平均): {result.cpu_usage_avg:.1f}%")
        print(f"   メモリ使用量 (平均): {result.memory_usage_avg:.1f}MB")
        print(f"   メモリ使用量 (ピーク): {result.memory_peak:.1f}MB")

    def _verify_performance_targets(
        self, result: LoadTestResult, benchmark: BenchmarkTarget
    ):
        """パフォーマンス目標の検証"""
        issues = []

        if result.avg_response_time > benchmark.max_avg_response_time:
            issues.append(
                f"平均レスポンス時間が目標を超過: {result.avg_response_time:.2f}s > {benchmark.max_avg_response_time}s"
            )

        if result.p95_response_time > benchmark.max_p95_response_time:
            issues.append(
                f"P95レスポンス時間が目標を超過: {result.p95_response_time:.2f}s > {benchmark.max_p95_response_time}s"
            )

        if result.p99_response_time > benchmark.max_p99_response_time:
            issues.append(
                f"P99レスポンス時間が目標を超過: {result.p99_response_time:.2f}s > {benchmark.max_p99_response_time}s"
            )

        if result.throughput < benchmark.min_throughput:
            issues.append(
                f"スループットが目標を下回る: {result.throughput:.1f} < {benchmark.min_throughput} req/sec"
            )

        if result.error_rate > benchmark.max_error_rate:
            issues.append(
                f"エラー率が目標を超過: {result.error_rate*100:.1f}% > {benchmark.max_error_rate*100}%"
            )

        if result.cpu_usage_avg > benchmark.max_cpu_usage:
            issues.append(
                f"CPU使用率が目標を超過: {result.cpu_usage_avg:.1f}% > {benchmark.max_cpu_usage}%"
            )

        if result.memory_peak > benchmark.max_memory_usage:
            issues.append(
                f"メモリ使用量が目標を超過: {result.memory_peak:.1f}MB > {benchmark.max_memory_usage}MB"
            )

        if issues:
            print("\n⚠️  パフォーマンス課題:")
            for issue in issues:
                print(f"   - {issue}")

            # テスト失敗（軽負荷以外）
            if result.test_name != "light_load":
                pytest.fail(f"パフォーマンス目標未達: {', '.join(issues)}")
        else:
            print(f"\n✅ {result.test_name}: 全パフォーマンス目標をクリア")

    def _analyze_progressive_results(self, results: List[LoadTestResult]):
        """段階的結果の分析"""
        print("\n📈 段階的負荷テスト総合分析:")
        print(
            f"{'テスト名':<15} {'ユーザー数':<8} {'スループット':<12} {'P95時間':<10} {'エラー率':<8} {'CPU%':<8}"
        )
        print("-" * 70)

        for result in results:
            print(
                f"{result.test_name:<15} {result.concurrent_users:<8} "
                f"{result.throughput:<12.1f} {result.p95_response_time:<10.2f} "
                f"{result.error_rate*100:<8.1f} {result.cpu_usage_avg:<8.1f}"
            )

        # スケーラビリティ分析
        if len(results) >= 2:
            throughput_improvement = results[-1].throughput / results[0].throughput
            response_degradation = (
                results[-1].p95_response_time / results[0].p95_response_time
            )

            print("\nスケーラビリティ分析:")
            print(f"  スループット向上率: {throughput_improvement:.2f}x")
            print(f"  レスポンス劣化率: {response_degradation:.2f}x")

            if throughput_improvement > 2.0 and response_degradation < 3.0:
                print("  ✅ 良好なスケーラビリティ")
            else:
                print("  ⚠️  スケーラビリティに課題あり")


# ========================================
# メモリリークテスト
# ========================================


class TestMemoryLeakDetection:
    """メモリリークの検出テスト"""

    @pytest.mark.memory
    async def test_memory_leak_detection(self, chat_service_with_mock):
        """長時間実行によるメモリリーク検出"""
        chat_service, mock_openai = chat_service_with_mock

        # 初期メモリ使用量
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        memory_readings = [initial_memory]
        test_queries = [
            "メモリリークテスト質問1",
            "メモリリークテスト質問2",
            "メモリリークテスト質問3",
        ]

        # 500回のリクエストを実行
        for i in range(500):
            query = test_queries[i % len(test_queries)]
            await chat_service.process_message(f"{query} - Iteration {i}")

            # 50回ごとにメモリ使用量を記録
            if i % 50 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_readings.append(current_memory)
                print(f"Iteration {i}: Memory usage {current_memory:.1f}MB")

                # ガベージコレクション
                import gc

                gc.collect()

        # 最終メモリ使用量
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_readings.append(final_memory)

        # メモリ増加の分析
        memory_increase = final_memory - initial_memory
        max_memory = max(memory_readings)

        print("\nメモリリーク分析:")
        print(f"  初期メモリ: {initial_memory:.1f}MB")
        print(f"  最終メモリ: {final_memory:.1f}MB")
        print(f"  最大メモリ: {max_memory:.1f}MB")
        print(f"  メモリ増加: {memory_increase:.1f}MB")

        # メモリリークの判定
        # 基準: 500リクエスト後のメモリ増加が200MB以下
        assert memory_increase < 200, f"メモリリーク検出: {memory_increase:.1f}MB増加"

        # 線形的なメモリ増加がないことを確認
        if len(memory_readings) > 3:
            # 最後の3つの読み取り値の傾向を分析
            recent_readings = memory_readings[-3:]
            trend = (recent_readings[-1] - recent_readings[0]) / len(recent_readings)

            assert trend < 10, f"継続的なメモリ増加傾向を検出: {trend:.1f}MB/reading"

        print("✅ メモリリークテスト合格")


# ========================================
# ストレステスト
# ========================================


class TestStressTesting:
    """ストレステストとエラー回復力テスト"""

    @pytest.mark.stress
    async def test_extreme_load_stress(self, chat_service_with_mock):
        """極限負荷ストレステスト"""
        chat_service, mock_openai = chat_service_with_mock

        # 高エラー率とレイテンシを設定
        mock_openai.set_error_rate(0.3)  # 30%エラー率
        mock_openai.enable_latency_simulation(2.0)  # 2秒ベースレイテンシ

        # 100並行リクエストで5分間
        concurrent_requests = 100
        test_duration = 300  # 5分間

        print(f"極限ストレステスト開始: {concurrent_requests}並行, {test_duration}秒間")

        async def stress_worker(worker_id: int):
            """ストレステスト用ワーカー"""
            requests_count = 0
            errors_count = 0
            end_time = time.time() + test_duration

            while time.time() < end_time:
                try:
                    await chat_service.process_message(
                        f"ストレステスト質問 Worker {worker_id}"
                    )
                    requests_count += 1
                except Exception:
                    errors_count += 1

                # リクエスト間隔なし（最大負荷）

            return requests_count, errors_count

        # ストレステスト実行
        start_time = time.time()
        tasks = [stress_worker(i) for i in range(concurrent_requests)]

        # システムリソース監視
        monitor = SystemResourceMonitor(interval=1.0)
        monitor.start_monitoring()

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            resource_metrics = monitor.stop_monitoring()

        execution_time = time.time() - start_time

        # 結果集計
        total_requests = 0
        total_errors = 0

        for result in results:
            if isinstance(result, Exception):
                total_errors += 1
            else:
                requests, errors = result
                total_requests += requests
                total_errors += errors

        # ストレステスト結果
        error_rate = (
            total_errors / (total_requests + total_errors)
            if (total_requests + total_errors) > 0
            else 1.0
        )
        throughput = total_requests / execution_time

        print("\n🔥 ストレステスト結果:")
        print(f"   実行時間: {execution_time:.1f}秒")
        print(f"   総リクエスト: {total_requests}")
        print(f"   総エラー: {total_errors}")
        print(f"   エラー率: {error_rate*100:.1f}%")
        print(f"   スループット: {throughput:.1f} req/sec")
        print(f"   CPU平均使用率: {resource_metrics['cpu_avg']:.1f}%")
        print(f"   メモリピーク: {resource_metrics['memory_peak']:.1f}MB")

        # ストレステスト基準
        # システムが完全にクラッシュしないことが重要
        assert total_requests > 0, "システムが完全に応答不能"
        assert error_rate < 0.8, f"エラー率が過度に高い: {error_rate*100:.1f}%"
        assert resource_metrics["cpu_avg"] < 100, "CPU使用率が100%を超過"

        print("✅ ストレステスト合格: システムは極限負荷下でも動作継続")


# ========================================
# ベンチマーク比較テスト
# ========================================


class TestBenchmarkComparison:
    """ベンチマーク比較とリグレッション検出"""

    BENCHMARK_FILE = "tests/benchmarks/performance_baseline.json"

    @pytest.mark.benchmark
    async def test_performance_regression(self, chat_service_with_mock):
        """パフォーマンス回帰テスト"""
        chat_service, mock_openai = chat_service_with_mock

        # 標準ベンチマーククエリ
        benchmark_queries = [
            "Azure OpenAIの基本的な使い方",
            "RAGシステムの概要説明",
            "データベース設計原則",
            "セキュリティベストプラクティス",
            "パフォーマンス最適化手法",
        ]

        # 現在のパフォーマンス測定
        current_results = []

        for query in benchmark_queries:
            times = []
            for _ in range(10):  # 各クエリを10回実行
                start_time = time.time()
                await chat_service.process_message(query)
                response_time = time.time() - start_time
                times.append(response_time)

            current_results.append(
                {
                    "query": query,
                    "avg_time": statistics.mean(times),
                    "p95_time": np.percentile(times, 95),
                    "min_time": min(times),
                    "max_time": max(times),
                }
            )

        # ベースライン比較
        baseline = self._load_baseline()
        regression_detected = False

        print("\n📊 パフォーマンス回帰分析:")
        print(f"{'クエリ':<30} {'現在':<10} {'ベース':<10} {'変化':<10} {'判定'}")
        print("-" * 70)

        for i, result in enumerate(current_results):
            current_time = result["avg_time"]

            if baseline and i < len(baseline):
                baseline_time = baseline[i]["avg_time"]
                change_percent = ((current_time - baseline_time) / baseline_time) * 100

                if change_percent > 20:  # 20%以上の劣化
                    status = "❌ 回帰"
                    regression_detected = True
                elif change_percent < -10:  # 10%以上の改善
                    status = "✅ 改善"
                else:
                    status = "➖ 変化なし"

                print(
                    f"{result['query'][:30]:<30} {current_time:<10.2f} {baseline_time:<10.2f} "
                    f"{change_percent:<10.1f}% {status}"
                )
            else:
                print(
                    f"{result['query'][:30]:<30} {current_time:<10.2f} {'N/A':<10} {'N/A':<10} {'新規'}"
                )

        # 新しいベースラインとして保存
        self._save_baseline(current_results)

        # 回帰検出時はテスト失敗
        if regression_detected:
            pytest.fail("パフォーマンス回帰が検出されました")
        else:
            print("\n✅ パフォーマンス回帰なし")

    def _load_baseline(self) -> Optional[List[Dict]]:
        """ベースライン結果の読み込み"""
        try:
            os.makedirs(os.path.dirname(self.BENCHMARK_FILE), exist_ok=True)
            with open(self.BENCHMARK_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"ベースライン読み込みエラー: {e}")
            return None

    def _save_baseline(self, results: List[Dict]):
        """ベースライン結果の保存"""
        try:
            os.makedirs(os.path.dirname(self.BENCHMARK_FILE), exist_ok=True)
            with open(self.BENCHMARK_FILE, "w") as f:
                json.dump(results, f, indent=2)
        except Exception as e:
            print(f"ベースライン保存エラー: {e}")


# ========================================
# テスト実行設定
# ========================================

if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--tb=short",
            "-m",
            "load or performance or memory or stress or benchmark",
        ]
    )

import logging
import os
import sys
import traceback

from opentelemetry import trace
from pythonjsonlogger import jsonlogger

# OpenTelemetry トレーサーを取得
tracer = trace.get_tracer(__name__)

# 環境変数から Application Insights 接続文字列を取得
APPINSIGHTS_CONNECTION_STRING = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")

# ログレベルを設定
LOG_LEVEL_STR = os.environ.get("LOG_LEVEL", "DEBUG").upper()
LOG_LEVEL = getattr(logging, LOG_LEVEL_STR, logging.DEBUG)

# ルートロガーのレベル設定
logging.getLogger().setLevel(LOG_LEVEL)

# --- ロガー設定 ---
log_handler = None
log_formatter = None

if APPINSIGHTS_CONNECTION_STRING:
    # Application Insights が有効な場合
    # OpenTelemetryのロギングエクスポーターが自動的に設定されるため、
    # 特別なハンドラ設定は不要
    print(
        "Logger: Application Insights is configured. Using OpenTelemetry logging exporter."
    )
else:
    # Application Insights が無効な場合 (ローカル開発など)
    # 標準出力にJSON形式でログを出力するハンドラを設定
    log_handler = logging.StreamHandler(sys.stdout)
    # フォーマット定義 (OpenTelemetry の Semantic Conventions を参考に)
    supported_keys = [
        "asctime",
        "levelname",
        "name",
        "message",  # 標準属性
        "trace_id",
        "span_id",
        "service.name",
        "enduser.id",  # トレース関連
        "http.request.method",
        "url.path",
        "http.response.status_code",  # HTTP関連
        "error.type",
        "error.message",
        "error.stacktrace",  # エラー関連
    ]
    format_str = " ".join([f"%({key})s" for key in supported_keys if key != "asctime"])
    format_str = f"%(asctime)s {format_str}"

    log_formatter = jsonlogger.JsonFormatter(
        format_str,
        rename_fields={
            "levelname": "level",
            "name": "logger_name",
            "asctime": "timestamp",
        },
        datefmt="%Y-%m-%dT%H:%M:%S.%fZ",
    )
    log_handler.setFormatter(log_formatter)
    log_handler.setLevel(LOG_LEVEL)

    # ルートロガーに設定済みのハンドラがあれば削除してから追加 (重複防止)
    root_logger = logging.getLogger()
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    root_logger.addHandler(log_handler)
    print(
        f"Logger: Application Insights not configured. Logging to stdout in JSON format (Level: {LOG_LEVEL_STR})."
    )


def get_logger(name: str) -> logging.Logger:
    """
    設定済みのロガーインスタンスを取得
    Application Insights が有効な場合は Azure Monitor Exporter と連携し、
    無効な場合は標準出力にJSON形式で出力

    Args:
        name: ロガーの名前。通常は呼び出し元モジュールの __name__ を指定

    Returns:
        設定済みの Logger インスタンス。
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    # 環境変数から環境情報を取得（ローカルテスト識別用）
    environment = os.environ.get("ENVIRONMENT", "local")

    # オリジナルのメソッドを保存
    original_info = logger.info
    original_warning = logger.warning
    original_error = logger.error
    original_debug = logger.debug
    original_critical = logger.critical

    # 各ログレベルのメソッドをオーバーライド
    def enhanced_info(msg, *args, **kwargs):
        return enhanced_log(logging.INFO, msg, args, kwargs)

    def enhanced_warning(msg, *args, **kwargs):
        return enhanced_log(logging.WARNING, msg, args, kwargs)

    def enhanced_error(msg, *args, **kwargs):
        return enhanced_log(logging.ERROR, msg, args, kwargs)

    def enhanced_debug(msg, *args, **kwargs):
        return enhanced_log(logging.DEBUG, msg, args, kwargs)

    def enhanced_critical(msg, *args, **kwargs):
        return enhanced_log(logging.CRITICAL, msg, args, kwargs)

    def enhanced_log(level, msg, args, kwargs):
        # extra情報を取得または初期化
        extra = kwargs.get("extra", {})
        if extra is None:
            extra = {}

        # 環境情報を追加
        extra["environment"] = environment

        # 現在のトレース情報を取得
        current_span = trace.get_current_span()
        if current_span:
            span_context = current_span.get_span_context()
            if span_context.is_valid:
                # ApplicationInsightsのcustomDimensionsに反映される形式で設定
                extra["trace_id"] = format(span_context.trace_id, "032x")
                extra["span_id"] = format(span_context.span_id, "016x")

        # ApplicationInsightsの形式に合わせて設定
        kwargs["extra"] = extra

        # 元のメソッドを呼び出し
        if level == logging.INFO:
            return original_info(msg, *args, **kwargs)
        elif level == logging.WARNING:
            return original_warning(msg, *args, **kwargs)
        elif level == logging.ERROR:
            return original_error(msg, *args, **kwargs)
        elif level == logging.DEBUG:
            return original_debug(msg, *args, **kwargs)
        elif level == logging.CRITICAL:
            return original_critical(msg, *args, **kwargs)

    # ロガーメソッドを上書き
    logger.info = enhanced_info
    logger.warning = enhanced_warning
    logger.error = enhanced_error
    logger.debug = enhanced_debug
    logger.critical = enhanced_critical

    return logger


def log_exception(
    logger_instance: logging.Logger,
    exc: Exception,
    message: str = "Unhandled exception",
    **kwargs,
):
    """
    例外情報をERRORレベルでログ出力するヘルパー関数
    スタックトレースを含む

    Args:
        logger_instance: ロガーインスタンス
        exc: 発生した例外
        message: ログメッセージ
        **kwargs: customDimensionsに追加する任意のキーと値
    """
    # 例外情報を取得（exc_infoはTrue/Falseまたはタプルが指定可能）
    exc_type, exc_value, exc_traceback = sys.exc_info()

    # スタックトレースの文字列を取得
    stack_trace = traceback.format_exc()

    # ApplicationInsightsのcustomDimensionsに反映されるようにextraを設定
    # キー名はApplication Insightsの規約に合わせる
    extra_data = {
        "errorType": type(exc).__name__,
        "errorMessage": str(exc),
        "stackTrace": stack_trace,
        "exceptionHandled": True,  # エラーハンドリングされたことを示す
    }

    # ユーザー指定の追加属性をマージ
    if kwargs:
        extra_data.update(kwargs)

    # enhanced_errorメソッドを通して直接エラーを記録
    # exc_info=Trueを指定してトレースバックも記録
    logger_instance.error(
        f"{message}: {type(exc).__name__}: {str(exc)}", extra=extra_data
    )

# init.py
import os

import toml


def load_config():
    """
    config.tomlのenvブロックから設定を読み込み、環境変数として設定します
    """
    config_path = "/app/config.toml"

    with open(config_path) as f:
        config = toml.load(f)

    # envブロックの設定のみを環境変数として設定
    env_config = config.get("env", {})
    for key, value in env_config.items():
        if value is not None:
            os.environ[key.upper()] = str(value)


# 環境変数設定の実行
load_config()

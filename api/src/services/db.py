import os
from contextlib import contextmanager

import toml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

CONFIG_PATH = "/app/config.toml"

config = toml.load(CONFIG_PATH)
db_config = config.get("db", {})

# 環境変数を優先、config.tomlをフォールバックとして使用
user = os.getenv("DB_USER") or db_config.get("DB_USER")
password = os.getenv("DB_PASSWORD") or db_config.get("DB_PASSWORD")
host = os.getenv("DB_HOST") or db_config.get("DB_HOST")
port = os.getenv("DB_PORT") or db_config.get("DB_PORT")
dbname = os.getenv("DB_NAME") or db_config.get("DB_NAME")

DATABASE_URL = f"mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}"
ENGINE = create_engine(DATABASE_URL)
SESSION_LOCAL = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)


@contextmanager
def get_session():
    session = SESSION_LOCAL()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

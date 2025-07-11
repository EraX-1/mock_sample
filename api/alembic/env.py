from logging.config import fileConfig

import toml
from sqlalchemy import engine_from_config, pool

from alembic import context
from src.schemas.base import Base


# Load .toml configuration
def get_db_url_from_toml(config_path: str) -> str:
    """
    Load database configuration from a .toml file and construct the SQLAlchemy URL.
    """
    config = toml.load(config_path)
    db_config = config.get("db", {})

    # Construct the database URL
    db_user = db_config.get("DB_USER", "root")
    db_password = db_config.get("DB_PASSWORD", "")
    db_host = db_config.get("DB_HOST", "127.0.0.1")
    db_port = db_config.get("DB_PORT", 3306)
    db_name = db_config.get("DB_NAME", "default_db")

    return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


# Database configuration file path (change if necessary)
TOML_CONFIG_PATH = "config.toml"
db_url = get_db_url_from_toml(TOML_CONFIG_PATH)
print("db_url", db_url)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
config.set_main_option("sqlalchemy.url", db_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {"url": db_url}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # # 一時的な別のバージョン管理テーブルを使用
            # version_table='alembic_version_new',
            # # 既存のマイグレーション履歴を無視
            # compare_type=True,
            # compare_server_default=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add app directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import your models' metadata
from db import Base

# Alembic config object
config = context.config

# Override URL if DATABASE_URL is set (e.g., from .env)
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# If the driver is async (like asyncpg or aiosqlite), convert to sync version
raw_url = config.get_main_option("sqlalchemy.url")
if raw_url and raw_url.startswith("postgresql+asyncpg://"):
    config.set_main_option(
        "sqlalchemy.url", raw_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    )
elif raw_url and raw_url.startswith("sqlite+aiosqlite://"):
    config.set_main_option(
        "sqlalchemy.url", raw_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    )

# Print final connection string
print("\n>>> Alembic database configuration loaded.\n")

# Set up logging
fileConfig(config.config_file_name)

# Target metadata
target_metadata = Base.metadata


def run_migrations_offline():
    """Run migrations in offline mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in online mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

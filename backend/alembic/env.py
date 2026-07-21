import os
import sys
from logging.config import fileConfig
from pathlib import Path
from dotenv import load_dotenv

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make `backend/` importable so `from models import Base` works
# regardless of where `alembic` is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models import Base  # noqa: E402  (this also imports User/Subject/Document)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

load_dotenv()

# Override the ini's sqlalchemy.url with the real DATABASE_URL from env,
# so credentials never get hardcoded into alembic.ini.
config.set_main_option(
    "sqlalchemy.url",
    os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/studysage"),
)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:



    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
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
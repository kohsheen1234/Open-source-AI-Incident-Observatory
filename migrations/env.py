from alembic import context
from sqlalchemy import engine_from_config, pool

from agentwatch.config import get_settings
from agentwatch.db import models  # noqa: F401 - register tables
from agentwatch.db.base import Base
from agentwatch.db.session import normalize_database_url

config = context.config
# Normalise provider URLs (e.g. Render's postgresql://) to the psycopg3 driver,
# matching the application engine.
config.set_main_option("sqlalchemy.url", normalize_database_url(get_settings().database_url))
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

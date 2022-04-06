from __future__ import with_statement

import logging
from logging.config import fileConfig

from alembic import context

from sqlalchemy import engine_from_config

from config import PG_USER, PG_PASSWD, PG_DATABASE, PG_HOST, PG_PORT
from server import DB_URL, db

config = context.config

fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

config.set_main_option('sqlalchemy.url', DB_URL)
section = config.config_ini_section
config.set_section_option(section, 'DB_USER', PG_USER)
config.set_section_option(section, 'DB_PASS', PG_PASSWD)
config.set_section_option(section, 'DB_NAME', PG_DATABASE)
config.set_section_option(section, 'DB_HOST', PG_HOST)
config.set_section_option(section, 'DB_PORT', str(PG_PORT))
config.set_section_option(section, 'alembic_table_schema', db.metadata.schema)
target_metadata = db.metadata


def include_object(object, name, type_, reflected, compare_to):
    if object.schema != db.metadata.schema:
        return False
    else:
        return True


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy."
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=target_metadata.schema,
            include_schemas=True,
            include_object=include_object
        )
        connection.execute(f"CREATE SCHEMA IF NOT EXISTS \"{target_metadata.schema}\"")

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

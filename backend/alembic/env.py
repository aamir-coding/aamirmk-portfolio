import asyncio
import os

from alembic import context
from pydantic import SecretStr
from sqlalchemy.engine import Connection

from app.db.models import SCHEMA, Base
from app.db.session import create_database_engine


def include_name(name: str | None, type_: str, parent_names: dict[str, str]) -> bool:
    if type_ == "schema":
        return name == SCHEMA
    return True


def run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        version_table="portfolio_alembic_version",
        target_metadata=Base.metadata,
        include_schemas=True,
        include_name=include_name,
    )
    with context.begin_transaction():
        context.run_migrations()


async def migrate_online(url: SecretStr) -> None:
    engine = create_database_engine(url, pooled=False)
    try:
        async with engine.connect() as connection:
            await connection.run_sync(run_migrations)
    finally:
        await engine.dispose()


if context.is_offline_mode():
    context.configure(
        dialect_name="postgresql",
        literal_binds=True,
        version_table="portfolio_alembic_version",
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    raw_url = os.environ.get("MIGRATION_DATABASE_URL")
    if not raw_url:
        raise SystemExit("Set MIGRATION_DATABASE_URL to run online migrations.")
    asyncio.run(migrate_online(SecretStr(raw_url)))

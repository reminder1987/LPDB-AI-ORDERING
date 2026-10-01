from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text

from app.core import database as database_module


@dataclass(frozen=True)
class DatabaseHealth:
    healthy: bool
    schema_ready: bool = False


def _expected_schema_heads() -> set[str]:
    project_root = Path(__file__).resolve().parents[2]
    alembic_config = Config(str(project_root / "alembic.ini"))
    script = ScriptDirectory.from_config(alembic_config)

    return set(script.get_heads())


def _current_schema_heads(session) -> set[str]:
    rows = session.execute(
        text("SELECT version_num FROM alembic_version")
    )

    return {str(row[0]) for row in rows}


def check_database() -> DatabaseHealth:
    session = database_module.SessionLocal()

    try:
        try:
            session.execute(text("SELECT 1"))
        except Exception:
            return DatabaseHealth(
                healthy=False,
                schema_ready=False,
            )

        try:
            expected_heads = _expected_schema_heads()
            current_heads = _current_schema_heads(session)
        except Exception:
            return DatabaseHealth(
                healthy=True,
                schema_ready=False,
            )

        return DatabaseHealth(
            healthy=True,
            schema_ready=(
                bool(expected_heads)
                and current_heads == expected_heads
            ),
        )

    finally:
        session.close()

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text

from app.core import database as database_module


@dataclass(frozen=True)
class DatabaseHealth:
    healthy: bool


def check_database() -> DatabaseHealth:
    session = database_module.SessionLocal()

    try:
        session.execute(text("SELECT 1"))

        return DatabaseHealth(
            healthy=True,
        )

    except Exception:
        return DatabaseHealth(
            healthy=False,
        )

    finally:
        session.close()

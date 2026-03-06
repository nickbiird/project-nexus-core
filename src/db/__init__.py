"""
Project Nexus — Database Session Factory
==========================================

Provides the SQLAlchemy engine and session factory for all database access.
The connection URL is read from ``NexusSettings.database_url``, ensuring that
both the application runtime and Alembic migrations share a single source of
truth for database configuration.

Usage::

    from src.db import get_session

    with get_session() as session:
        session.add(some_model)
        # commits on clean exit, rolls back on exception
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.common.config.settings import get_settings

_settings = get_settings()

_connect_args: dict[str, bool] = {}
if _settings.database_url.startswith("sqlite"):
    _connect_args["check_same_thread"] = False

engine = create_engine(_settings.database_url, connect_args=_connect_args)

SessionLocal: sessionmaker[Session] = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Yield a transactional database session.

    Commits on clean exit, rolls back on exception, and always closes the
    session when the context manager exits.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

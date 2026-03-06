"""Integration test fixtures — temporary SQLite database and demo data."""

from __future__ import annotations

import io
from collections.abc import Generator
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.db.models import Base
from src.services.demo_service import generate_demo_data


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a temporary SQLite database with all tables."""
    db_path = tmp_path_factory.mktemp("db") / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    engine.dispose()
    return db_path


@pytest.fixture()
def db_session(test_db_path: Path) -> Generator[Session, None, None]:
    """Yield a session with rollback after each test for isolation."""
    engine = create_engine(f"sqlite:///{test_db_path}")
    session_factory: sessionmaker[Session] = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="session")
def demo_excel_bytes() -> bytes:
    """Generate demo data and return it as Excel bytes."""
    df: pd.DataFrame = generate_demo_data()
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()

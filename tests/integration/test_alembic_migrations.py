"""Integration test — Alembic migration roundtrip."""

from __future__ import annotations

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

# Expected table names from src/db/models.py
EXPECTED_TABLES = {
    "clients",
    "audits",
    "audit_findings",
    "audit_column_profiles",
    "audit_anomalies",
}


def _alembic_cfg(db_url: str) -> Config:
    """Build an Alembic Config pointing to the given database."""
    project_root = Path(__file__).resolve().parent.parent.parent
    cfg = Config(str(project_root / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    cfg.set_main_option("script_location", str(project_root / "src" / "db" / "migrations"))
    return cfg


class TestAlembicRoundtrip:
    """Upgrade → verify → downgrade → verify → upgrade again."""

    def test_migration_roundtrip(self, tmp_path: Path) -> None:
        db_path = tmp_path / "roundtrip.db"
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url)
        cfg = _alembic_cfg(db_url)

        # Override DATABASE_URL so env.py's get_settings() picks up the
        # test SQLite database instead of the production/Docker URL.
        old_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = db_url

        # Clear the lru_cache so get_settings() re-reads the env var
        from src.common.config.settings import get_settings
        get_settings.cache_clear()

        try:
            # 1. Upgrade to head
            command.upgrade(cfg, "head")
            tables = set(inspect(engine).get_table_names())
            assert EXPECTED_TABLES.issubset(tables), (
                f"Missing tables after upgrade: {EXPECTED_TABLES - tables}"
            )

            # 2. Downgrade to base
            command.downgrade(cfg, "base")
            tables = set(inspect(engine).get_table_names())
            remaining = EXPECTED_TABLES & tables
            assert len(remaining) == 0, f"Tables remain after downgrade: {remaining}"

            # 3. Upgrade again
            command.upgrade(cfg, "head")
            tables = set(inspect(engine).get_table_names())
            assert EXPECTED_TABLES.issubset(tables), (
                f"Missing tables after re-upgrade: {EXPECTED_TABLES - tables}"
            )
        finally:
            # Restore original env var and clear settings cache
            if old_url is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = old_url
            get_settings.cache_clear()
            engine.dispose()

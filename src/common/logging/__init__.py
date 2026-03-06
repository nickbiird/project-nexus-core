"""
Yellowbird Telemetry — Structured Logging Configuration
========================================================

Single configuration point for all ``src/`` and ``app/`` modules.
Wraps ``structlog`` over Python's stdlib ``logging`` so third-party
libraries coexist without conflicts.

Usage::

    from src.common.logging import configure_logging, get_logger

    configure_logging()          # call once at startup
    logger = get_logger(__name__)
    logger.info("audit.started", file_name="test.xlsx")
"""

from __future__ import annotations

import logging
import sys
from typing import cast

import structlog

_configured = False


def configure_logging() -> None:
    """Configure structlog with environment-aware rendering.

    - ``APP_ENV=production`` → JSON output (machine-readable).
    - All other values → coloured console output (human-readable).

    Calling this function multiple times is a no-op.
    """
    global _configured
    if _configured:
        return

    from src.common.config.settings import get_settings

    settings = get_settings()
    is_production = settings.app_env == "production"

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if is_production:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, settings.app_log_level.upper(), logging.INFO))

    _configured = True


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """Return a structlog bound logger, optionally named."""
    return cast(structlog.BoundLogger, structlog.get_logger(name))

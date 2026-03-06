"""
Yellowbird Telemetry — Typed Exception Hierarchy
=================================================

Base exception classes for the three primary failure domains:
ingestion, profiling, and export.  Each domain has a single base
class; downstream code catches the base to handle an entire
domain uniformly.
"""

from __future__ import annotations


class IngestionError(Exception):
    """Raised when raw file ingestion fails.

    Subtypes cover unsupported formats, encoding issues, and
    size-limit violations.
    """


class ProfilingError(Exception):
    """Raised when the profiling engine encounters an unrecoverable error.

    Subtypes cover schema detection failures, anomaly-detection
    crashes, and entity-clustering timeouts.
    """


class ExportError(Exception):
    """Raised when report generation or serialisation fails.

    Subtypes cover HTML rendering errors, JSON serialisation
    failures, and file-system write errors.
    """

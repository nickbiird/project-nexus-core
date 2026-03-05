"""
Custom exceptions for the Lead Generation Pipeline.
"""


class InvalidSABIFormatError(ValueError):
    """Raised when a SABI XLSX file cannot be parsed or has too few recognised columns."""


class EmptyExportError(RuntimeError):
    """Raised when a SABI export parses successfully but yields zero leads after filtering."""

"""
Project Nexus — Repository Package
=====================================

Public surface for the repository layer.  Consumers should import
from this package rather than reaching into sub-modules::

    from src.db.repositories import AuditRepository, ClientRepository
"""

from __future__ import annotations

from src.db.repositories.audit_repo import AuditRepository
from src.db.repositories.base import BaseRepository
from src.db.repositories.client_repo import ClientRepository

__all__ = ["AuditRepository", "BaseRepository", "ClientRepository"]

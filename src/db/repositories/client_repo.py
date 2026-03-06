"""
Project Nexus — Client Repository
====================================

Database operations for the ``Client`` entity.  All methods use the
SQLAlchemy 2.0 ``select()`` API and receive a session via ``BaseRepository``.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select

from src.common.exceptions import PersistenceError
from src.db.models import Client
from src.db.repositories.base import BaseRepository


class ClientRepository(BaseRepository):
    """CRUD operations for ``Client`` entities."""

    def get_by_id(self, client_id: uuid.UUID) -> Client | None:
        """Return the client with the given primary key, or ``None``.

        Uses ``session.get()`` for efficient identity-map lookup.
        """
        return self._session.get(Client, client_id)

    def get_by_company_name(self, company_name: str) -> Client | None:
        """Return the client matching *company_name*, or ``None``.

        Performs a case-sensitive equality match on
        ``Client.company_name``.
        """
        stmt = select(Client).where(Client.company_name == company_name)
        return self._session.execute(stmt).scalar_one_or_none()

    def create_client(
        self,
        company_name: str,
        nif: str | None = None,
        contact_email: str | None = None,
        vertical: str | None = None,
    ) -> Client:
        """Create and persist a new ``Client``.

        Args:
            company_name: Legal company name (required).
            nif: Spanish tax identifier.
            contact_email: Primary contact email.
            vertical: Industry vertical code.

        Returns:
            The persisted ``Client`` instance with its UUID and
            ``created_at`` populated.

        Raises:
            PersistenceError: If the database write fails.
        """
        client = Client(
            company_name=company_name,
            nif=nif,
            contact_email=contact_email,
            vertical=vertical,
        )
        try:
            self._session.add(client)
            self._session.commit()
            self._session.refresh(client)
        except Exception as exc:
            self._session.rollback()
            raise PersistenceError(f"Failed to create client {company_name!r}") from exc
        return client

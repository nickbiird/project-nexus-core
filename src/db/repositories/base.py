"""
Project Nexus — Base Repository
=================================

Provides the shared foundation for all repository classes.  A repository
receives a SQLAlchemy ``Session`` at construction time and uses it for all
database operations.  It never creates or closes sessions — that lifecycle
is owned by the caller.
"""

from __future__ import annotations

from sqlalchemy.orm import Session


class BaseRepository:
    """Thin base class that holds the injected database session.

    Every concrete repository inherits from this class and accesses
    ``self._session`` for all ORM operations.
    """

    def __init__(self, session: Session) -> None:
        """Initialise the repository with a database session.

        Args:
            session: An active SQLAlchemy ``Session`` instance.  The caller
                owns the session lifecycle; the repository only uses it.
        """
        self._session = session

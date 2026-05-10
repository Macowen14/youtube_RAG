"""SQLAlchemy ORM models for persistent user data.

These models map directly to database tables managed by Alembic migrations.
Every table enforces ``user_id`` scoping so that queries always filter by the
authenticated user — see :mod:`src.infrastructure.auth.security` for how the
user identity is resolved from Supabase JWTs.

Provider
--------
Tables live in **Neon PostgreSQL**.  Authentication is handled externally by
**Supabase Auth**; the ``user_id`` column stores the Supabase ``sub`` claim
(a UUID string) but has no foreign-key relationship to Supabase tables.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, Text

from src.infrastructure.database.db import Base


class DBNote(Base):
    """A user-created note attached to a specific YouTube video."""

    __tablename__ = "notes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True, nullable=False)
    video_id = Column(String, index=True, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DBSummary(Base):
    """An AI-generated or user-curated summary for a YouTube video."""

    __tablename__ = "summaries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True, nullable=False)
    video_id = Column(String, index=True, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

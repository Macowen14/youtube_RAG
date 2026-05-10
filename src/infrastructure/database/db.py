"""SQLAlchemy engine, session factory, and declarative base.

This module is the single point of database connectivity for the application.
It reads ``DATABASE_URL`` from :class:`~src.infrastructure.config.Settings`,
validates it, and exposes:

* ``engine``       – the SQLAlchemy :class:`~sqlalchemy.engine.Engine`.
* ``SessionLocal`` – a :func:`~sqlalchemy.orm.sessionmaker` bound to the engine.
* ``Base``         – the declarative base class all ORM models inherit from.
* ``get_db()``     – a FastAPI-compatible dependency that yields a session.

Provider
--------
The production database is **Neon PostgreSQL** (serverless, connection-pooled).
SSL is enforced via the ``?sslmode=require`` query parameter in the DSN.
"""

from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from src.infrastructure.config import Settings

# ---------------------------------------------------------------------------
# Engine initialisation
# ---------------------------------------------------------------------------

settings = Settings()

if not settings.database_url:
    raise ValueError(
        "DATABASE_URL is not set. Provide a PostgreSQL connection string, "
        "e.g. postgresql://user:pass@host:5432/dbname?sslmode=require"
    )

_url = make_url(settings.database_url)
if _url.drivername in {"http", "https"}:
    raise ValueError(
        f"DATABASE_URL has scheme '{_url.drivername}', but a PostgreSQL DSN is "
        "required.  Use the connection string from your Neon dashboard, not "
        "an HTTP API URL."
    )

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """Yield a transactional database session and close it on exit.

    Usage::

        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

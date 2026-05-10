"""FastAPI application factory.

Creates and configures the ASGI application with middleware, routers, and
lifecycle hooks.  Database migrations are applied automatically on startup
via Alembic so that the schema is always up-to-date when the server begins
accepting traffic.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.api.routers import notes, rag, summaries
from src.infrastructure.config import Settings
from src.infrastructure.logging import setup_logger

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


def create_app() -> FastAPI:
    """Build and return a fully-configured :class:`FastAPI` instance."""
    settings = Settings()
    app_logger = setup_logger("api", settings.log_file)

    app = FastAPI(
        title="YouTube RAG API",
        version="1.0.0",
        description=(
            "Retrieval-Augmented Generation API for YouTube video transcripts.  "
            "Ingest videos, ask questions, and generate notes & summaries."
        ),
    )

    # ── Rate-limiting ────────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ── CORS ─────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ──────────────────────────────────────────────────────────
    app.include_router(rag.router)
    app.include_router(notes.router)
    app.include_router(summaries.router)

    # ── Lifecycle hooks ──────────────────────────────────────────────────

    @app.on_event("startup")
    async def _run_migrations() -> None:
        """Apply pending Alembic migrations so the DB schema is current."""
        try:
            from alembic import command
            from alembic.config import Config

            alembic_cfg = Config("alembic.ini")
            command.upgrade(alembic_cfg, "head")
            app_logger.info("Database migrations applied successfully.")
        except Exception as exc:
            app_logger.error("Failed to run database migrations: %s", exc)

    return app

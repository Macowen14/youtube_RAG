"""Application-wide settings loaded from environment variables.

This module provides a single, immutable ``Settings`` dataclass that is the
canonical source of runtime configuration for the backend.  Values are read
from a ``.env`` file (via *python-dotenv*) and fall back to sensible defaults
so the application can start in a minimal development mode.

Architecture note
-----------------
The backend uses a **split-provider** strategy:

* **Neon PostgreSQL**  — primary relational data store (notes, summaries).
* **Supabase Auth**    — JWT-based user authentication only; no Supabase DB.
* **OpenAI**           — LLM inference for RAG queries & note generation.
* **Pinecone**         — serverless vector store with integrated inference.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Immutable container for environment-sourced application settings."""

    # ── Database (Neon PostgreSQL) ────────────────────────────────────────
    database_url: str = field(
        default_factory=lambda: os.getenv("DATABASE_URL", ""),
    )

    # ── Authentication (Supabase Auth) ───────────────────────────────────
    supabase_url: str = field(
        default_factory=lambda: os.getenv("SUPABASE_URL", ""),
    )
    supabase_key: str = field(
        default_factory=lambda: os.getenv("SUPABASE_KEY", ""),
    )
    supabase_jwt_secret: str = field(
        default_factory=lambda: os.getenv("SUPABASE_JWT_SECRET", ""),
    )

    # ── OpenAI / LLM ────────────────────────────────────────────────────
    openai_api_key: str = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", ""),
    )
    openai_model_name: str = field(
        default_factory=lambda: os.getenv("MODEL_NAME", "gpt-5.4-mini"),
    )

    # ── Vector Store (Pinecone) ──────────────────────────────────────────
    pinecone_api_key: str = field(
        default_factory=lambda: os.getenv("PINECONE_API_KEY", ""),
    )
    pinecone_index_name: str = field(
        default_factory=lambda: os.getenv("PINECONE_INDEX_NAME", "youtube-rag"),
    )

    # ── Observability ────────────────────────────────────────────────────
    log_file: str = field(
        default_factory=lambda: os.getenv("APP_LOG_FILE", "logs/app.log"),
    )

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.api.routers import rag, notes, summaries
from src.infrastructure.config import Settings
from src.infrastructure.logging import setup_logger

limiter = Limiter(key_func=get_remote_address)

def create_app() -> FastAPI:
    settings = Settings()
    logger = setup_logger("api", settings.log_file)

    app = FastAPI(title="YouTube RAG API", version="1.0.0")
    
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(rag.router)
    app.include_router(notes.router)
    app.include_router(summaries.router)

    @app.on_event("startup")
    async def startup_event():
        logger.info("Application starting up...")

        # Run Alembic migrations on startup
        try:
            from alembic.config import Config
            from alembic import command

            alembic_cfg = Config("alembic.ini")
            command.upgrade(alembic_cfg, "head")
            logger.info("Database migrations applied successfully.")
        except Exception as exc:
            logger.error("Failed to run database migrations: %s", exc)

    return app


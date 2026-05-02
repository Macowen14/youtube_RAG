from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.infrastructure.config import Settings
from src.infrastructure.logging import setup_logger


def create_app() -> FastAPI:
    settings = Settings()
    logger = setup_logger("api", settings.log_file)

    app = FastAPI(title="YouTube RAG API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    @app.on_event("startup")
    async def startup_event():
        logger.info("Application starting up...")

    return app


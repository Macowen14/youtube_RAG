import os

import uvicorn

from src.api.app import create_app
from src.infrastructure.config import Settings
from src.infrastructure.logging import setup_logger


settings = Settings()
logger = setup_logger("api", settings.log_file)
app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8060))
    logger.info("Starting server on port: %s", port)
    uvicorn.run("main:app", host="0.0.0.0", port=port)


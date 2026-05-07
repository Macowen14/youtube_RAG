import os

import uvicorn

from src.api.app import create_app
from src.infrastructure.config import Settings
from src.infrastructure.logging import setup_logger


settings = Settings()
if not settings.database_url:
    raise ValueError("DATABASE_URL environment variable is not set. Please set it to your database connection string.")

if not settings.supabase_jwt_secret:
    raise ValueError("SUPABASE_JWT_SECRET environment variable is not set. Please set it to your Supabase JWT secret.")
    
if not settings.openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it to your OpenAI API key.")

logger = setup_logger("api", settings.log_file)
app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8060))
    logger.info("Starting server on port: %s", port)
    uvicorn.run("main:app", host="0.0.0.0", port=port)


import os
import sys

import uvicorn

from src.api.app import create_app
from src.infrastructure.config import Settings
from src.infrastructure.logging import setup_logger

# Set environment variables for OpenAI-only mode
os.environ["LLM_PROVIDER"] = "openai"
os.environ["PORT"] = os.getenv("PORT", "8080")

# Now initialize settings after env vars are set
settings = Settings()
if not settings.database_url:
    raise ValueError(
        "DATABASE_URL environment variable is not set. Please set it to your database connection string."
    )

if not settings.supabase_url:
    raise ValueError(
        "SUPABASE_URL environment variable is not set. Please set it to your Supabase project URL."
    )

if not settings.supabase_key:
    raise ValueError(
        "SUPABASE_KEY environment variable is not set. Please set it to your Supabase publishable or anon key."
    )

if not settings.openai_api_key:
    raise ValueError(
        "OPENAI_API_KEY environment variable is not set. Please set it to your OpenAI API key."
    )

logger = setup_logger("api", settings.log_file)

# Print status information
port = int(os.environ.get("PORT", 8080))
print(f"Starting YouTube RAG Backend on port {port}...")
print(f"Using Python: {sys.executable} ({sys.version.split()[0]})")
print(f"Using LLM model: {settings.openai_model_name}")

app = create_app()

if __name__ == "__main__":
    logger.info("Starting server on port: %s", port)
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

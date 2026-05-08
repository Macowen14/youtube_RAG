import argparse
import os
import sys

import uvicorn

from src.api.app import create_app
from src.infrastructure.config import Settings
from src.infrastructure.logging import setup_logger

# Parse command-line arguments
parser = argparse.ArgumentParser(description='YouTube RAG Backend')
parser.add_argument('--provider', choices=['ollama', 'openai'], default='ollama', help='LLM provider (default: ollama)')
parser.add_argument('--model', help='Model name (optional)')
parser.add_argument('--port', type=int, default=8080, help='Port to run on (default: 8080)')
args = parser.parse_args()

# Set environment variables based on arguments
os.environ['LLM_PROVIDER'] = args.provider
if args.model:
    if args.provider == 'openai':
        os.environ['MODEL_NAME'] = args.model
    else:
        os.environ['OLLAMA_MODEL_NAME'] = args.model
os.environ['PORT'] = str(args.port)

# Now initialize settings after env vars are set
settings = Settings()
if not settings.database_url:
    raise ValueError("DATABASE_URL environment variable is not set. Please set it to your database connection string.")

if not settings.supabase_url:
    raise ValueError("SUPABASE_URL environment variable is not set. Please set it to your Supabase project URL.")

if not settings.supabase_key:
    raise ValueError("SUPABASE_KEY environment variable is not set. Please set it to your Supabase publishable or anon key.")

if settings.llm_provider not in {"ollama", "openai"}:
    raise ValueError("LLM_PROVIDER must be either 'ollama' or 'openai'.")

if settings.llm_provider == "openai" and not settings.openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it to your OpenAI API key.")

logger = setup_logger("api", settings.log_file)

# Print status information
port = args.port
print(f"Starting YouTube RAG Backend on port {port}...")
print(f"Using Python: {sys.executable} ({sys.version.split()[0]})")
print(f"Using LLM provider: {settings.llm_provider}")
if settings.llm_provider == "openai":
    print(f"Using LLM model: {os.environ.get('MODEL_NAME', 'gpt-5.4-mini')}")
else:
    print(f"Using LLM model: {os.environ.get('OLLAMA_MODEL_NAME', 'deepseek-v3.1:671b-cloud')}")

app = create_app()

if __name__ == "__main__":
    logger.info("Starting server on port: %s", port)
    uvicorn.run("main:app", host="0.0.0.0", port=port)
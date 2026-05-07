import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    persist_directory: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "db")
    log_file: str = os.getenv("APP_LOG_FILE", "logs/app.log")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model_name: str = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
    ollama_model_name: str = os.getenv("OLLAMA_MODEL_NAME", "deepseek-v3.1:671b-cloud")
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
    supabase_jwt_secret: str = os.getenv("SUPABASE_JWT_SECRET", "your-super-secret-jwt-token-with-at-least-32-characters-long")


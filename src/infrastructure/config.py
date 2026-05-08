import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    ollama_host: str = field(default_factory=lambda: os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    persist_directory: str = field(default_factory=lambda: os.getenv("CHROMA_PERSIST_DIRECTORY", "db"))
    log_file: str = field(default_factory=lambda: os.getenv("APP_LOG_FILE", "logs/app.log"))
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "ollama").lower())
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model_name: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "gpt-5.4-mini"))
    ollama_model_name: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL_NAME", "deepseek-v3.1:671b-cloud"))
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    supabase_url: str = field(default_factory=lambda: os.getenv("SUPABASE_URL", ""))
    supabase_key: str = field(default_factory=lambda: os.getenv("SUPABASE_KEY", ""))
    supabase_jwt_secret: str = field(default_factory=lambda: os.getenv("SUPABASE_JWT_SECRET", ""))

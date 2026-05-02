import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    persist_directory: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "db")
    log_file: str = os.getenv("APP_LOG_FILE", "logs/app.log")


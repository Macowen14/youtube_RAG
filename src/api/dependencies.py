from functools import lru_cache

from src.application.services import YouTubeRAGService
from src.bootstrap import create_rag_service


@lru_cache
def get_rag_service() -> YouTubeRAGService:
    return create_rag_service()


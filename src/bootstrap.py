"""Composition root — wires infrastructure adapters into application services.

This is the only module that knows about concrete implementations.  Every
other layer depends on abstractions (protocols) defined in ``src.domain.ports``.
"""

from __future__ import annotations

from src.application.services import YouTubeRAGService
from src.infrastructure.config import Settings
from src.infrastructure.llm.openai import OpenAIRAGGenerator
from src.infrastructure.logging import setup_logger
from src.infrastructure.text_splitter import LangChainTextChunker
from src.infrastructure.transcripts.ytdlp import YtDlpTranscriptProvider
from src.infrastructure.vectorstores.pinecone import PineconeVideoKnowledgeBase


def create_rag_service(settings: Settings | None = None) -> YouTubeRAGService:
    """Assemble and return a fully-configured :class:`YouTubeRAGService`."""
    settings = settings or Settings()
    logger = setup_logger("rag_service", settings.log_file)

    return YouTubeRAGService(
        transcript_provider=YtDlpTranscriptProvider(
            logger=setup_logger("transcript_service", settings.log_file),
        ),
        chunker=LangChainTextChunker(),
        knowledge_base=PineconeVideoKnowledgeBase(
            api_key=settings.pinecone_api_key,
            index_name=settings.pinecone_index_name,
        ),
        generator=OpenAIRAGGenerator(api_key=settings.openai_api_key),
        default_model=settings.openai_model_name,
        logger=logger,
    )

from src.application.services import YouTubeRAGService
from src.infrastructure.config import Settings
from src.infrastructure.llm.ollama import OllamaRAGGenerator
from src.infrastructure.logging import setup_logger
from src.infrastructure.text_splitter import LangChainTextChunker
from src.infrastructure.transcripts.ytdlp import YtDlpTranscriptProvider
from src.infrastructure.vectorstores.chroma import ChromaVideoKnowledgeBase


def create_rag_service(settings: Settings | None = None) -> YouTubeRAGService:
    settings = settings or Settings()
    logger = setup_logger("rag_service", settings.log_file)

    return YouTubeRAGService(
        transcript_provider=YtDlpTranscriptProvider(logger=setup_logger("transcript_service", settings.log_file)),
        chunker=LangChainTextChunker(),
        knowledge_base=ChromaVideoKnowledgeBase(persist_directory=settings.persist_directory),
        generator=OllamaRAGGenerator(base_url=settings.ollama_host),
        logger=logger,
    )


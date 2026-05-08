from src.application.services import YouTubeRAGService
from src.infrastructure.config import Settings
from src.infrastructure.llm.ollama import OllamaRAGGenerator
from src.infrastructure.llm.openai import OpenAIRAGGenerator
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
        generators={
            "ollama": OllamaRAGGenerator(base_url=settings.ollama_host),
            "openai": OpenAIRAGGenerator(api_key=settings.openai_api_key),
        },
        default_provider=settings.llm_provider,
        default_models={
            "ollama": settings.ollama_model_name,
            "openai": settings.openai_model_name,
        },
        logger=logger,
    )

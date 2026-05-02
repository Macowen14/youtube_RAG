import logging

from src.domain.models import RAGResult
from src.domain.ports import RAGGenerator, TextChunker, TranscriptProvider, VideoKnowledgeBase


class YouTubeRAGService:
    """Application use cases for ingesting and querying YouTube transcript knowledge."""

    def __init__(
        self,
        *,
        transcript_provider: TranscriptProvider,
        chunker: TextChunker,
        knowledge_base: VideoKnowledgeBase,
        generator: RAGGenerator,
        logger: logging.Logger,
    ) -> None:
        self._transcript_provider = transcript_provider
        self._chunker = chunker
        self._knowledge_base = knowledge_base
        self._generator = generator
        self._logger = logger

    def ingest_video(self, video_id: str) -> None:
        if self._knowledge_base.has_video(video_id):
            self._logger.info("Video %s already ingested. Skipping.", video_id)
            return

        transcript = self._transcript_provider.fetch_transcript(video_id)
        chunks = self._chunker.split(transcript)
        self._knowledge_base.add_video_chunks(video_id, chunks)
        self._logger.info("Successfully ingested video %s with %s chunks.", video_id, len(chunks))

    def ask_question(
        self,
        *,
        video_id: str,
        question: str,
        model_name: str = "mistral-large-3:675b-cloud",
    ) -> RAGResult:
        try:
            chunks = self._knowledge_base.search(video_id, question, k=5, fetch_k=20)
            context = self._format_context(chunks)

            return self._generator.answer_question(
                context=context,
                question=question,
                model_name=model_name,
            )
        except Exception as exc:
            self._logger.error("Error answering question for video %s: %s", video_id, exc)
            return RAGResult(
                answer="An error occurred while processing your request.",
                source="Internal Knowledge",
            )

    def generate_notes(
        self,
        *,
        video_id: str,
        topic: str,
        model_name: str = "mistral-large-3:675b-cloud",
    ) -> RAGResult:
        chunks = self._knowledge_base.search(video_id, topic, k=10, fetch_k=30)
        context = self._format_context(chunks)

        return self._generator.generate_notes(
            context=context,
            topic=topic,
            model_name=model_name,
        )

    @staticmethod
    def _format_context(chunks: list) -> str:
        context = "\n\n".join(chunk.content for chunk in chunks)
        return context or "No relevant video context found."

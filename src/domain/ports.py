import logging
from typing import Protocol

from src.domain.models import RAGResult, RetrievedChunk


class TranscriptProvider(Protocol):
    def fetch_transcript(self, video_id: str) -> str:
        """Return the plain-text transcript for a YouTube video."""


class TextChunker(Protocol):
    def split(self, text: str) -> list[str]:
        """Split text into chunks suitable for embedding."""


class VideoKnowledgeBase(Protocol):
    def has_video(self, video_id: str) -> bool:
        """Return whether chunks already exist for the video."""

    def add_video_chunks(
        self,
        video_id: str,
        chunks: list[str],
        *,
        logger: logging.Logger | None = None,
    ) -> None:
        """Persist chunks associated with a video."""

    def search(self, video_id: str, query: str, *, k: int, fetch_k: int) -> list[RetrievedChunk]:
        """Return relevant chunks for a video and query."""


class RAGGenerator(Protocol):
    def answer_question(self, *, context: str, question: str, model_name: str) -> RAGResult:
        """Generate a structured answer for a question."""

    def generate_notes(self, *, context: str, topic: str, model_name: str) -> RAGResult:
        """Generate structured notes for a topic."""

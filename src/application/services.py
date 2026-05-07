import logging

from src.domain.models import Note, RAGResult, Summary
from src.domain.ports import RAGGenerator, TextChunker, TranscriptProvider, VideoKnowledgeBase
from src.infrastructure.database.db_models import DBNote, DBSummary
from sqlalchemy.orm import Session


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

    def generate_summary(
        self,
        *,
        video_id: str,
        topic: str = "General summary of the video",
        model_name: str = "mistral-large-3:675b-cloud",
    ) -> RAGResult:
        chunks = self._knowledge_base.search(video_id, topic, k=10, fetch_k=30)
        context = self._format_context(chunks)

        # Assuming generator.generate_notes can be repurposed for summary, or we should add a generate_summary to generator.
        # But wait, we can just use answer_question with a prompt to summarize.
        return self._generator.answer_question(
            context=context,
            question=f"Provide a comprehensive summary for the topic: {topic}",
            model_name=model_name,
        )


    @staticmethod
    def _format_context(chunks: list) -> str:
        context = "\n\n".join(chunk.content for chunk in chunks)
        return context or "No relevant video context found."


class NoteService:
    def __init__(self, db: Session):
        self.db = db

    def create_note(self, user_id: str, video_id: str, content: str) -> Note:
        db_note = DBNote(user_id=user_id, video_id=video_id, content=content)
        self.db.add(db_note)
        self.db.commit()
        self.db.refresh(db_note)
        return Note(
            id=db_note.id,
            user_id=db_note.user_id,
            video_id=db_note.video_id,
            content=db_note.content,
            created_at=db_note.created_at.isoformat(),
        )

    def get_notes(self, user_id: str, video_id: str | None = None) -> list[Note]:
        query = self.db.query(DBNote).filter(DBNote.user_id == user_id)
        if video_id:
            query = query.filter(DBNote.video_id == video_id)
        db_notes = query.all()
        return [
            Note(
                id=n.id,
                user_id=n.user_id,
                video_id=n.video_id,
                content=n.content,
                created_at=n.created_at.isoformat(),
            )
            for n in db_notes
        ]

    def get_note_by_id(self, user_id: str, note_id: str) -> Note | None:
        db_note = self.db.query(DBNote).filter(DBNote.user_id == user_id, DBNote.id == note_id).first()
        if not db_note:
            return None
        return Note(
            id=db_note.id,
            user_id=db_note.user_id,
            video_id=db_note.video_id,
            content=db_note.content,
            created_at=db_note.created_at.isoformat(),
        )

class SummaryService:
    def __init__(self, db: Session):
        self.db = db

    def create_summary(self, user_id: str, video_id: str, content: str) -> Summary:
        db_summary = DBSummary(user_id=user_id, video_id=video_id, content=content)
        self.db.add(db_summary)
        self.db.commit()
        self.db.refresh(db_summary)
        return Summary(
            id=db_summary.id,
            user_id=db_summary.user_id,
            video_id=db_summary.video_id,
            content=db_summary.content,
            created_at=db_summary.created_at.isoformat(),
        )

    def get_summaries(self, user_id: str, video_id: str | None = None) -> list[Summary]:
        query = self.db.query(DBSummary).filter(DBSummary.user_id == user_id)
        if video_id:
            query = query.filter(DBSummary.video_id == video_id)
        db_summaries = query.all()
        return [
            Summary(
                id=s.id,
                user_id=s.user_id,
                video_id=s.video_id,
                content=s.content,
                created_at=s.created_at.isoformat(),
            )
            for s in db_summaries
        ]

    def get_summary_by_id(self, user_id: str, summary_id: str) -> Summary | None:
        db_summary = self.db.query(DBSummary).filter(DBSummary.user_id == user_id, DBSummary.id == summary_id).first()
        if not db_summary:
            return None
        return Summary(
            id=db_summary.id,
            user_id=db_summary.user_id,
            video_id=db_summary.video_id,
            content=db_summary.content,
            created_at=db_summary.created_at.isoformat(),
        )

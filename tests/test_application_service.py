import logging
import unittest

from src.application.services import YouTubeRAGService
from src.domain.models import RAGResult, RetrievedChunk


def make_test_logger() -> logging.Logger:
    logger = logging.getLogger("src_test")
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


class FakeTranscriptProvider:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def fetch_transcript(self, video_id: str) -> str:
        self.calls.append(video_id)
        return "first part second part"


class FakeChunker:
    def split(self, text: str) -> list[str]:
        return text.split()


class FakeKnowledgeBase:
    def __init__(self) -> None:
        self.existing_videos: set[str] = set()
        self.saved_chunks: dict[str, list[str]] = {}
        self.search_calls: list[dict] = []

    def has_video(self, video_id: str) -> bool:
        return video_id in self.existing_videos

    def add_video_chunks(self, video_id: str, chunks: list[str]) -> None:
        self.saved_chunks[video_id] = chunks

    def search(self, video_id: str, query: str, *, k: int, fetch_k: int) -> list[RetrievedChunk]:
        self.search_calls.append({"video_id": video_id, "query": query, "k": k, "fetch_k": fetch_k})
        return [
            RetrievedChunk(content="chunk one", video_id=video_id),
            RetrievedChunk(content="chunk two", video_id=video_id),
        ]


class FakeGenerator:
    def __init__(self) -> None:
        self.question_context: str | None = None
        self.notes_context: str | None = None

    def answer_question(self, *, context: str, question: str, model_name: str) -> RAGResult:
        self.question_context = context
        return RAGResult(answer=f"answer: {question}", source="Context")

    def generate_notes(self, *, context: str, topic: str, model_name: str) -> RAGResult:
        self.notes_context = context
        return RAGResult(answer=f"notes: {topic}", source="Context")


class FailingGenerator(FakeGenerator):
    def answer_question(self, *, context: str, question: str, model_name: str) -> RAGResult:
        raise RuntimeError("LLM unavailable")


class YouTubeRAGServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.transcripts = FakeTranscriptProvider()
        self.knowledge_base = FakeKnowledgeBase()
        self.generator = FakeGenerator()
        self.service = YouTubeRAGService(
            transcript_provider=self.transcripts,
            chunker=FakeChunker(),
            knowledge_base=self.knowledge_base,
            generator=self.generator,
            logger=make_test_logger(),
        )

    def test_ingest_video_fetches_and_stores_chunks(self) -> None:
        self.service.ingest_video("abc123")

        self.assertEqual(self.transcripts.calls, ["abc123"])
        self.assertEqual(self.knowledge_base.saved_chunks["abc123"], ["first", "part", "second", "part"])

    def test_ingest_video_skips_existing_video(self) -> None:
        self.knowledge_base.existing_videos.add("abc123")

        self.service.ingest_video("abc123")

        self.assertEqual(self.transcripts.calls, [])
        self.assertEqual(self.knowledge_base.saved_chunks, {})

    def test_query_formats_retrieved_context_for_generator(self) -> None:
        result = self.service.ask_question(video_id="abc123", question="What happened?", model_name="model")

        self.assertEqual(result.answer, "answer: What happened?")
        self.assertEqual(self.generator.question_context, "chunk one\n\nchunk two")
        self.assertEqual(self.knowledge_base.search_calls[0]["k"], 5)

    def test_notes_use_larger_retrieval_window(self) -> None:
        result = self.service.generate_notes(video_id="abc123", topic="Topic", model_name="model")

        self.assertEqual(result.answer, "notes: Topic")
        self.assertEqual(self.generator.notes_context, "chunk one\n\nchunk two")
        self.assertEqual(self.knowledge_base.search_calls[0]["k"], 10)

    def test_query_preserves_legacy_fallback_response_on_errors(self) -> None:
        service = YouTubeRAGService(
            transcript_provider=self.transcripts,
            chunker=FakeChunker(),
            knowledge_base=self.knowledge_base,
            generator=FailingGenerator(),
            logger=make_test_logger(),
        )

        result = service.ask_question(video_id="abc123", question="What happened?", model_name="model")

        self.assertEqual(result.answer, "An error occurred while processing your request.")
        self.assertEqual(result.source, "Internal Knowledge")


if __name__ == "__main__":
    unittest.main()

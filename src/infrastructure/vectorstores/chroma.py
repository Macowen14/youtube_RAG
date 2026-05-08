import logging

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from src.domain.models import RetrievedChunk


class ChromaVideoKnowledgeBase:
    def __init__(
        self,
        *,
        persist_directory: str = "db",
        embedding_model: str = "qwen3-embedding:0.6b",
    ) -> None:
        self._embeddings = OllamaEmbeddings(model=embedding_model)
        self._vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=self._embeddings,
        )

    def has_video(self, video_id: str) -> bool:
        existing_docs = self._vector_store.get(where={"video_id": video_id})
        return bool(existing_docs.get("ids"))

    def add_video_chunks(
        self,
        video_id: str,
        chunks: list[str],
        *,
        logger: logging.Logger | None = None,
        batch_size: int = 8,
    ) -> None:
        documents = [
            Document(page_content=chunk, metadata={"video_id": video_id})
            for chunk in chunks
        ]
        for start in range(0, len(documents), batch_size):
            batch = documents[start : start + batch_size]
            if logger:
                logger.info(
                    "Embedding chunks %s-%s of %s for video %s.",
                    start + 1,
                    start + len(batch),
                    len(documents),
                    video_id,
                )
            self._vector_store.add_documents(batch)

    def search(self, video_id: str, query: str, *, k: int, fetch_k: int) -> list[RetrievedChunk]:
        retriever = self._vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={"k": k, "fetch_k": fetch_k, "filter": {"video_id": video_id}},
        )
        documents = retriever.invoke(query)
        return [
            RetrievedChunk(content=document.page_content, video_id=str(document.metadata.get("video_id", video_id)))
            for document in documents
        ]

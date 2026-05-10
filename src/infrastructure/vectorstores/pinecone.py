"""Pinecone-backed video knowledge base with local Ollama embeddings.

This module implements the :class:`~src.domain.ports.VideoKnowledgeBase`
protocol using **Pinecone serverless** for vector storage and **Ollama** for
local embedding generation (no external embedding API calls required).

Architecture
------------
* **Embedding** — ``qwen3-embedding:0.6b`` via Ollama (1024-dim, runs locally).
* **Storage**   — Pinecone serverless index (cosine similarity, 1024-dim).
* **Namespacing** — each ``video_id`` maps to a Pinecone namespace, providing
  natural data isolation and efficient per-video queries.

Environment
-----------
* ``PINECONE_API_KEY``    — API key for authenticating with Pinecone.
* ``PINECONE_INDEX_NAME`` — name of the pre-created serverless index.
"""

from __future__ import annotations

import logging
import uuid

from langchain_ollama import OllamaEmbeddings
from pinecone import Pinecone

from src.domain.models import RetrievedChunk


class PineconeVideoKnowledgeBase:
    """Video knowledge base backed by Pinecone + local Ollama embeddings.

    Each YouTube video's chunks are stored in a **namespace** equal to the
    ``video_id``, providing natural data isolation and efficient per-video
    queries.
    """

    def __init__(
        self,
        *,
        api_key: str,
        index_name: str,
        embedding_model: str = "qwen3-embedding:0.6b",
    ) -> None:
        self._embeddings = OllamaEmbeddings(model=embedding_model)
        self._client = Pinecone(api_key=api_key)
        self._index = self._client.Index(index_name)

    # ------------------------------------------------------------------
    # VideoKnowledgeBase protocol
    # ------------------------------------------------------------------

    def has_video(self, video_id: str) -> bool:
        """Check whether any chunks have been indexed for *video_id*."""
        stats = self._index.describe_index_stats()
        namespaces = stats.get("namespaces", {})
        ns = namespaces.get(video_id, {})
        return ns.get("vector_count", 0) > 0

    def add_video_chunks(
        self,
        video_id: str,
        chunks: list[str],
        *,
        logger: logging.Logger | None = None,
        batch_size: int = 32,
    ) -> None:
        """Embed *chunks* locally via Ollama and upsert into Pinecone.

        Vectors are stored under the *video_id* namespace with the original
        text preserved in metadata for retrieval.
        """
        for start in range(0, len(chunks), batch_size):
            batch_texts = chunks[start : start + batch_size]
            if logger:
                logger.info(
                    "Embedding & upserting chunks %s–%s of %s for video %s.",
                    start + 1,
                    start + len(batch_texts),
                    len(chunks),
                    video_id,
                )

            # Generate embeddings locally via Ollama.
            vectors = self._embeddings.embed_documents(batch_texts)

            # Build Pinecone upsert payload.
            records = [
                {
                    "id": str(uuid.uuid4()),
                    "values": vec,
                    "metadata": {"chunk_text": text, "video_id": video_id},
                }
                for text, vec in zip(batch_texts, vectors)
            ]
            self._index.upsert(vectors=records, namespace=video_id)

        if logger:
            logger.info(
                "Successfully indexed %s chunks for video %s.",
                len(chunks),
                video_id,
            )

    def search(
        self,
        video_id: str,
        query: str,
        *,
        k: int,
        fetch_k: int = 0,
    ) -> list[RetrievedChunk]:
        """Retrieve the top-*k* chunks most relevant to *query* for a video.

        The query is embedded locally via Ollama before being sent to
        Pinecone for similarity search.  The ``fetch_k`` parameter is
        accepted for interface compatibility but is not used by Pinecone.
        """
        query_vector = self._embeddings.embed_query(query)

        results = self._index.query(
            namespace=video_id,
            vector=query_vector,
            top_k=k,
            include_metadata=True,
        )

        return [
            RetrievedChunk(
                content=match.get("metadata", {}).get("chunk_text", ""),
                video_id=video_id,
            )
            for match in results.get("matches", [])
        ]

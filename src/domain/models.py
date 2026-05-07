from dataclasses import dataclass
from typing import Literal


SourceType = Literal["Context", "Internal Knowledge", "Context & Internal Knowledge"]


@dataclass(frozen=True)
class RAGResult:
    answer: str
    source: SourceType


@dataclass(frozen=True)
class RetrievedChunk:
    content: str
    video_id: str


@dataclass(frozen=True)
class Note:
    id: str
    user_id: str
    video_id: str
    content: str
    created_at: str


@dataclass(frozen=True)
class Summary:
    id: str
    user_id: str
    video_id: str
    content: str
    created_at: str


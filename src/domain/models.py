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


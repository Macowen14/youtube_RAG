from typing import Literal, Optional

from pydantic import BaseModel, Field


LLMProvider = Literal["ollama", "openai"]


class VideoIngestRequest(BaseModel):
    video_id: str = Field(..., description="The YouTube video ID to ingest.")
    url: Optional[str] = Field(None, description="Optional URL if video ID is not directly provided.")


class QueryRequest(BaseModel):
    video_id: str = Field(..., description="The YouTube video ID to query.")
    question: str = Field(..., description="The question to ask about the video.")
    provider: Optional[LLMProvider] = Field(None, description="LLM provider to use. Defaults to the server provider.")
    model_name: Optional[str] = Field(None, description="The LLM model to use. Defaults by provider.")


class NotesRequest(BaseModel):
    video_id: str = Field(..., description="The YouTube video ID to generate notes for.")
    topic: str = Field(..., description="The specific topic to focus the notes on.")
    provider: Optional[LLMProvider] = Field(None, description="LLM provider to use. Defaults to the server provider.")
    model_name: Optional[str] = Field(None, description="The LLM model to use. Defaults by provider.")


class ResponseModel(BaseModel):
    answer: str = Field(..., description="The answer or generated notes.")
    source: str = Field(..., description="Source of the information.")


class CreateNoteRequest(BaseModel):
    video_id: str
    content: str


class NoteResponse(BaseModel):
    id: str
    user_id: str
    video_id: str
    content: str
    created_at: str


class CreateSummaryRequest(BaseModel):
    video_id: str
    content: str


class SummaryResponse(BaseModel):
    id: str
    user_id: str
    video_id: str
    content: str
    created_at: str

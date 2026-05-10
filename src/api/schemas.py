from typing import Optional

from pydantic import BaseModel, Field


class VideoIngestRequest(BaseModel):
    video_id: str = Field(..., description="The YouTube video ID to ingest.")
    url: Optional[str] = Field(None, description="Optional URL if video ID is not directly provided.")


class QueryRequest(BaseModel):
    video_id: str = Field(..., description="The YouTube video ID to query.")
    question: str = Field(..., description="The question to ask about the video.")
    model_name: Optional[str] = Field(None, description="The OpenAI model to use. Defaults to server default.")


class NotesRequest(BaseModel):
    video_id: str = Field(..., description="The YouTube video ID to generate notes for.")
    topic: str = Field(..., description="The specific topic to focus the notes on.")
    model_name: Optional[str] = Field(None, description="The OpenAI model to use. Defaults to server default.")


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

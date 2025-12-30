from pydantic import BaseModel, Field
from typing import Optional, Dict

class VideoIngestRequest(BaseModel):
    video_id: str = Field(..., description="The YouTube video ID to ingest.")
    url: Optional[str] = Field(None, description="Optional URL if video ID is not directly provided.")

class QueryRequest(BaseModel):
    video_id: str = Field(..., description="The YouTube video ID to query.")
    question: str = Field(..., description="The question to ask about the video.")
    model_name: Optional[str] = Field("mistral-large-3:675b-cloud", description="The LLM model to use.")

class NotesRequest(BaseModel):
    video_id: str = Field(..., description="The YouTube video ID to generate notes for.")
    topic: str = Field(..., description="The specific topic to focus the notes on.")
    model_name: Optional[str] = Field("mistral-large-3:675b-cloud", description="The LLM model to use.")

class ResponseModel(BaseModel):
    answer: str = Field(..., description="The answer or generated notes.")
    source: str = Field(..., description="Source of the information (Context or Internal Knowledge).")

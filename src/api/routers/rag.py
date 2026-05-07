import os
import shutil

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from src.api.dependencies import get_rag_service
from src.api.schemas import NotesRequest, QueryRequest, ResponseModel, VideoIngestRequest
from src.application.services import YouTubeRAGService
from src.infrastructure.config import Settings
from src.infrastructure.logging import setup_logger
from src.infrastructure.auth.security import get_current_user


router = APIRouter(prefix="/rag", tags=["RAG"])
settings = Settings()
logger = setup_logger("api_rag", settings.log_file)


@router.post("/ingest", response_model=dict)
async def ingest_video(
    request: VideoIngestRequest,
    rag_service: YouTubeRAGService = Depends(get_rag_service),
    user_id: str = Depends(get_current_user),
):
    logger.info("Received ingest request for video_id: %s by user: %s", request.video_id, user_id)
    try:
        rag_service.ingest_video(request.video_id)
        return {"message": f"Successfully ingested video {request.video_id}"}
    except Exception as exc:
        logger.exception("Ingestion failed.")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/query", response_model=ResponseModel)
async def query_video(
    request: QueryRequest,
    rag_service: YouTubeRAGService = Depends(get_rag_service),
    user_id: str = Depends(get_current_user),
):
    logger.info("Received query for video_id: %s by user: %s", request.video_id, user_id)
    try:
        response = rag_service.ask_question(
            video_id=request.video_id,
            question=request.question,
            model_name=request.model_name or "mistral-large-3:675b-cloud",
        )
        return ResponseModel(answer=response.answer, source=response.source)
    except Exception as exc:
        logger.exception("Query failed.")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/generate-notes", response_model=ResponseModel)
async def generate_notes(
    request: NotesRequest,
    rag_service: YouTubeRAGService = Depends(get_rag_service),
    user_id: str = Depends(get_current_user),
):
    logger.info(
        "Received notes generation request for video_id: %s, topic: %s by user: %s",
        request.video_id,
        request.topic,
        user_id
    )
    try:
        response = rag_service.generate_notes(
            video_id=request.video_id,
            topic=request.topic,
            model_name=request.model_name or "mistral-large-3:675b-cloud",
        )
        return ResponseModel(answer=response.answer, source=response.source)
    except Exception as exc:
        logger.exception("Notes generation failed.")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/generate-summary", response_model=ResponseModel)
async def generate_summary(
    request: NotesRequest,
    rag_service: YouTubeRAGService = Depends(get_rag_service),
    user_id: str = Depends(get_current_user),
):
    logger.info(
        "Received summary generation request for video_id: %s, topic: %s by user: %s",
        request.video_id,
        request.topic,
        user_id
    )
    try:
        response = rag_service.generate_summary(
            video_id=request.video_id,
            topic=request.topic,
            model_name=request.model_name or "mistral-large-3:675b-cloud",
        )
        return ResponseModel(answer=response.answer, source=response.source)
    except Exception as exc:
        logger.exception("Summary generation failed.")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

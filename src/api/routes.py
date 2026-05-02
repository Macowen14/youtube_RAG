import os
import shutil

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse

from src.api.dependencies import get_rag_service
from src.api.schemas import NotesRequest, QueryRequest, ResponseModel, VideoIngestRequest
from src.application.services import YouTubeRAGService
from src.infrastructure.config import Settings
from src.infrastructure.logging import setup_logger


router = APIRouter()
settings = Settings()
logger = setup_logger("api", settings.log_file)


@router.get("/")
async def root():
    return {"status": "live", "message": "YouTube RAG API is running"}


@router.get("/logs/download")
async def download_logs(background_tasks: BackgroundTasks):
    log_dir = "logs"
    zip_filename = "logs_archive.zip"

    if not os.path.exists(log_dir):
        raise HTTPException(status_code=404, detail="Logs directory not found")

    shutil.make_archive(zip_filename.replace(".zip", ""), "zip", log_dir)
    background_tasks.add_task(os.remove, zip_filename)

    return FileResponse(
        path=zip_filename,
        filename=zip_filename,
        media_type="application/zip",
    )


@router.post("/ingest", response_model=dict)
async def ingest_video(
    request: VideoIngestRequest,
    rag_service: YouTubeRAGService = Depends(get_rag_service),
):
    logger.info("Received ingest request for video_id: %s", request.video_id)
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
):
    logger.info("Received query for video_id: %s", request.video_id)
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


@router.post("/notes", response_model=ResponseModel)
async def generate_notes(
    request: NotesRequest,
    rag_service: YouTubeRAGService = Depends(get_rag_service),
):
    logger.info(
        "Received notes generation request for video_id: %s, topic: %s",
        request.video_id,
        request.topic,
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


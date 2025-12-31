from fastapi import FastAPI, HTTPException
from logger import setup_logger
from models import VideoIngestRequest, QueryRequest, NotesRequest, ResponseModel
from rag_service import RAGService
import uvicorn
import shutil
import os
from fastapi.responses import FileResponse
from fastapi import BackgroundTasks

# Setup logger
logger = setup_logger("api", "logs/app.log")

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="YouTube RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG Service
# In a real app, this might be better as a dependency with @lru_cache or lifespan
rag_service = RAGService()

@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up...")

@app.get("/logs/download")
async def download_logs(background_tasks: BackgroundTasks):
    """
    Downloads the logs directory as a zip file.
    """
    log_dir = "logs"
    zip_filename = "logs_archive.zip"
    
    if not os.path.exists(log_dir):
        # Create logs dir if it checks for it but it's empty/missing, though setup_logger should handle it
        raise HTTPException(status_code=404, detail="Logs directory not found")

    # Create zip file. make_archive adds .zip extension automatically
    shutil.make_archive(zip_filename.replace('.zip', ''), 'zip', log_dir)
    
    # Clean up zip file after sending
    background_tasks.add_task(os.remove, zip_filename)
    
    return FileResponse(
        path=zip_filename, 
        filename=zip_filename, 
        media_type='application/zip'
    )

@app.post("/ingest", response_model=dict)
async def ingest_video(request: VideoIngestRequest):
    """
    Ingests a YouTube video by fetching its transcript and storing it in the vector database.
    """
    logger.info(f"Received ingest request for video_id: {request.video_id}")
    try:
        rag_service.ingest_video(request.video_id)
        return {"message": f"Successfully ingested video {request.video_id}"}
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=ResponseModel)
async def query_video(request: QueryRequest):
    """
    Asks a question about a specific video.
    """
    logger.info(f"Received query for video_id: {request.video_id}")
    try:
        response = rag_service.ask_question(
            video_id=request.video_id, 
            question=request.question, 
            model_name=request.model_name
        )
        return ResponseModel(**response)
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/notes", response_model=ResponseModel)
async def generate_notes(request: NotesRequest):
    """
    Generates detailed notes about a topic from a video.
    """
    logger.info(f"Received notes generation request for video_id: {request.video_id}, topic: {request.topic}")
    try:
        response = rag_service.generate_notes(
            video_id=request.video_id, 
            topic=request.topic, 
            model_name=request.model_name
        )
        return ResponseModel(**response)
    except Exception as e:
        logger.error(f"Notes generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

from fastapi import FastAPI, HTTPException
from logger import setup_logger
from models import VideoIngestRequest, QueryRequest, NotesRequest, ResponseModel
from rag_service import RAGService
import uvicorn

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

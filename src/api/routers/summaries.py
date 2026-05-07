from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.schemas import CreateSummaryRequest, SummaryResponse
from src.application.services import SummaryService
from src.infrastructure.auth.security import get_current_user
from src.infrastructure.database.db import get_db

router = APIRouter(prefix="/summaries", tags=["Summaries"])

def get_summary_service(db: Session = Depends(get_db)) -> SummaryService:
    return SummaryService(db)

@router.post("/", response_model=SummaryResponse)
async def create_summary(
    request: CreateSummaryRequest,
    user_id: str = Depends(get_current_user),
    service: SummaryService = Depends(get_summary_service)
):
    try:
        return service.create_summary(
            user_id=user_id,
            video_id=request.video_id,
            content=request.content
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.get("/", response_model=list[SummaryResponse])
async def get_summaries(
    video_id: str | None = None,
    user_id: str = Depends(get_current_user),
    service: SummaryService = Depends(get_summary_service)
):
    try:
        return service.get_summaries(user_id=user_id, video_id=video_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.get("/{summary_id}", response_model=SummaryResponse)
async def get_summary(
    summary_id: str,
    user_id: str = Depends(get_current_user),
    service: SummaryService = Depends(get_summary_service)
):
    summary = service.get_summary_by_id(user_id=user_id, summary_id=summary_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    return summary

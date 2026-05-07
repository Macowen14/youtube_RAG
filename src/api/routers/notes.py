from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.schemas import CreateNoteRequest, NoteResponse
from src.application.services import NoteService
from src.infrastructure.auth.security import get_current_user
from src.infrastructure.database.db import get_db

router = APIRouter(prefix="/notes", tags=["Notes"])

def get_note_service(db: Session = Depends(get_db)) -> NoteService:
    return NoteService(db)

@router.post("/", response_model=NoteResponse)
async def create_note(
    request: CreateNoteRequest,
    user_id: str = Depends(get_current_user),
    service: NoteService = Depends(get_note_service)
):
    try:
        return service.create_note(
            user_id=user_id,
            video_id=request.video_id,
            content=request.content
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.get("/", response_model=list[NoteResponse])
async def get_notes(
    video_id: str | None = None,
    user_id: str = Depends(get_current_user),
    service: NoteService = Depends(get_note_service)
):
    try:
        return service.get_notes(user_id=user_id, video_id=video_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    user_id: str = Depends(get_current_user),
    service: NoteService = Depends(get_note_service)
):
    note = service.get_note_by_id(user_id=user_id, note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

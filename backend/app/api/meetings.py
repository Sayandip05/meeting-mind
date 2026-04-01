import os
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List
from app.models.base import get_db
from app.services.meeting_service import MeetingService
from app.schemas.meeting import MeetingResponse, MeetingCreate
from app.api.auth import get_current_user_id
from app.core.exceptions import MeetingNotFoundError, ProcessingError

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".mp4", ".mp3", ".wav"}


@router.post("/upload", response_model=MeetingResponse)
async def upload_meeting(
    file: UploadFile = File(...),
    name: str = Form(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Upload a new meeting file"""
    
    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {', '.join(ALLOWED_EXTENSIONS)} files are allowed"
        )
    
    meeting_service = MeetingService(db)
    
    # Save file
    meeting = meeting_service.create_meeting(
        user_id=user_id,
        name=name,
        original_filename=file.filename,
        file_path=""  # Will update after saving
    )
    
    file_path = UPLOAD_DIR / f"{meeting.id}{ext}"
    
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Update meeting with file path
    from app.repositories.meeting_repository import MeetingRepository
    MeetingRepository(db).update_status(meeting.id, "uploaded")
    
    # Update the audio path
    meeting = MeetingRepository(db).get_by_id(meeting.id)
    meeting.audio_path = str(file_path)
    db.commit()
    db.refresh(meeting)
    
    return MeetingResponse.model_validate(meeting)


@router.get("/", response_model=List[MeetingResponse])
def get_meetings(
    skip: int = 0,
    limit: int = 100,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get all meetings for current user"""
    meeting_service = MeetingService(db)
    return meeting_service.get_user_meetings(user_id, skip, limit)


@router.get("/{meeting_id}", response_model=MeetingResponse)
def get_meeting(
    meeting_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get a specific meeting"""
    meeting_service = MeetingService(db)
    try:
        return meeting_service.get_meeting(meeting_id, user_id)
    except MeetingNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")


@router.post("/{meeting_id}/process", response_model=MeetingResponse)
def process_meeting(
    meeting_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Process a meeting (transcribe, chunk, embed)"""
    meeting_service = MeetingService(db)
    try:
        return meeting_service.process_meeting(meeting_id, user_id)
    except MeetingNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    except ProcessingError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{meeting_id}")
def delete_meeting(
    meeting_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Delete a meeting"""
    meeting_service = MeetingService(db)
    try:
        success = meeting_service.delete_meeting(meeting_id, user_id)
        if success:
            return {"message": "Meeting deleted successfully"}
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete meeting")
    except MeetingNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

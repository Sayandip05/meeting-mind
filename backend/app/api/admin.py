from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.models.base import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.meeting_repository import MeetingRepository
from app.schemas.auth import UserResponse
from app.schemas.meeting import MeetingResponse
from app.api.auth import get_current_user_id

router = APIRouter()


def get_superadmin_user(user_id: int, db: Session):
    """Verify user is superadmin"""
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    
    if not user or not user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin access required"
        )
    return user


@router.get("/dashboard")
def get_admin_dashboard(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get admin dashboard stats"""
    get_superadmin_user(user_id, db)
    
    user_repo = UserRepository(db)
    meeting_repo = MeetingRepository(db)
    
    return {
        "total_users": user_repo.count(),
        "total_meetings": meeting_repo.count(),
        "recent_users": [UserResponse.model_validate(u) for u in user_repo.get_all(limit=5)],
        "recent_meetings": [MeetingResponse.model_validate(m) for m in meeting_repo.get_all(limit=5)]
    }


@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    skip: int = 0,
    limit: int = 100,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get all users (superadmin only)"""
    get_superadmin_user(user_id, db)
    
    user_repo = UserRepository(db)
    users = user_repo.get_all(skip, limit)
    return [UserResponse.model_validate(u) for u in users]


@router.get("/meetings", response_model=List[MeetingResponse])
def get_all_meetings(
    skip: int = 0,
    limit: int = 100,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get all meetings (superadmin only)"""
    get_superadmin_user(user_id, db)
    
    meeting_repo = MeetingRepository(db)
    meetings = meeting_repo.get_all(skip, limit)
    return [MeetingResponse.model_validate(m) for m in meetings]


@router.post("/users/{user_id}/deactivate")
def deactivate_user(
    target_user_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Deactivate a user account (superadmin only)"""
    get_superadmin_user(user_id, db)
    
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(target_user_id)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user.is_active = False
    db.commit()
    
    return {"message": "User deactivated successfully"}

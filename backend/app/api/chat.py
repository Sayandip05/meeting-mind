from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.models.base import get_db
from app.services.ai_agent_service import AIAgentService
from app.api.auth import get_current_user_id
from app.repositories.meeting_repository import MeetingRepository
from app.core.exceptions import MeetingNotFoundError

router = APIRouter()

# In-memory chat history store (replace with Redis in production)
chat_histories = {}


class ChatMessage(BaseModel):
    content: str
    is_user: bool


class ChatRequest(BaseModel):
    question: str
    meeting_id: int


class ChatResponse(BaseModel):
    answer: str


@router.post("/ask", response_model=ChatResponse)
def ask_question(
    request: ChatRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Ask a question about a meeting"""
    
    # Verify meeting belongs to user
    meeting_repo = MeetingRepository(db)
    meeting = meeting_repo.get_by_id(request.meeting_id)
    
    if not meeting or meeting.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    
    if meeting.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meeting is still being processed"
        )
    
    # Get chat history
    history_key = f"{user_id}:{request.meeting_id}"
    chat_history = chat_histories.get(history_key, [])
    
    # Get answer
    ai_service = AIAgentService()
    answer = ai_service.ask_question(
        meeting_id=request.meeting_id,
        question=request.question,
        chat_history=chat_history
    )
    
    # Update history
    chat_history.append({"content": request.question, "is_user": True})
    chat_history.append({"content": answer, "is_user": False})
    chat_histories[history_key] = chat_history[-10:]  # Keep last 10 messages
    
    return ChatResponse(answer=answer)


@router.get("/history/{meeting_id}", response_model=List[ChatMessage])
def get_chat_history(
    meeting_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """Get chat history for a meeting"""
    history_key = f"{user_id}:{meeting_id}"
    history = chat_histories.get(history_key, [])
    return [ChatMessage(content=h["content"], is_user=h["is_user"]) for h in history]


@router.delete("/history/{meeting_id}")
def clear_chat_history(
    meeting_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """Clear chat history for a meeting"""
    history_key = f"{user_id}:{meeting_id}"
    if history_key in chat_histories:
        del chat_histories[history_key]
    return {"message": "Chat history cleared"}

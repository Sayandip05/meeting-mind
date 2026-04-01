from fastapi import APIRouter
from app.api import auth, meetings, chat, highlights, admin

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(meetings.router, prefix="/meetings", tags=["meetings"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(highlights.router, prefix="/highlights", tags=["highlights"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

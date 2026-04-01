from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MeetingBase(BaseModel):
    name: str


class MeetingCreate(MeetingBase):
    pass


class MeetingUpdate(BaseModel):
    name: Optional[str] = None


class MeetingResponse(MeetingBase):
    id: int
    user_id: int
    original_filename: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

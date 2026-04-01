from sqlalchemy.orm import Session
from app.models.meeting import Meeting
from typing import List, Optional


class MeetingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, meeting_id: int) -> Meeting | None:
        return self.db.query(Meeting).filter(Meeting.id == meeting_id).first()

    def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Meeting]:
        return (
            self.db.query(Meeting)
            .filter(Meeting.user_id == user_id)
            .order_by(Meeting.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(
        self,
        user_id: int,
        name: str,
        original_filename: str,
        audio_path: Optional[str] = None
    ) -> Meeting:
        db_meeting = Meeting(
            user_id=user_id,
            name=name,
            original_filename=original_filename,
            audio_path=audio_path,
            status="uploaded"
        )
        self.db.add(db_meeting)
        self.db.commit()
        self.db.refresh(db_meeting)
        return db_meeting

    def update_status(self, meeting_id: int, status: str) -> Meeting | None:
        meeting = self.get_by_id(meeting_id)
        if meeting:
            meeting.status = status
            self.db.commit()
            self.db.refresh(meeting)
        return meeting

    def update_transcript_path(self, meeting_id: int, transcript_path: str) -> Meeting | None:
        meeting = self.get_by_id(meeting_id)
        if meeting:
            meeting.transcript_path = transcript_path
            self.db.commit()
            self.db.refresh(meeting)
        return meeting

    def update_highlights_path(self, meeting_id: int, highlights_path: str) -> Meeting | None:
        meeting = self.get_by_id(meeting_id)
        if meeting:
            meeting.highlights_path = highlights_path
            self.db.commit()
            self.db.refresh(meeting)
        return meeting

    def delete(self, meeting_id: int) -> bool:
        meeting = self.get_by_id(meeting_id)
        if meeting:
            self.db.delete(meeting)
            self.db.commit()
            return True
        return False

    def get_all(self, skip: int = 0, limit: int = 100):
        return self.db.query(Meeting).offset(skip).limit(limit).all()

    def count(self) -> int:
        return self.db.query(Meeting).count()

    def count_by_user(self, user_id: int) -> int:
        return self.db.query(Meeting).filter(Meeting.user_id == user_id).count()

import os
import subprocess
import whisper
from pathlib import Path
from sqlalchemy.orm import Session
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.vector_repository import VectorRepository
from app.core.exceptions import MeetingNotFoundError, ProcessingError
from app.schemas.meeting import MeetingCreate, MeetingResponse
from typing import List

# Load Whisper model once
whisper_model = whisper.load_model("small")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
INTERMEDIATE_DIR = BASE_DIR / "data" / "intermediate"


class MeetingService:
    def __init__(self, db: Session):
        self.meeting_repo = MeetingRepository(db)
        self.vector_repo = VectorRepository()

    def create_meeting(
        self,
        user_id: int,
        name: str,
        original_filename: str,
        file_path: str
    ) -> MeetingResponse:
        """Create a new meeting record"""
        meeting = self.meeting_repo.create(
            user_id=user_id,
            name=name,
            original_filename=original_filename,
            audio_path=file_path
        )
        return MeetingResponse.model_validate(meeting)

    def get_user_meetings(self, user_id: int, skip: int = 0, limit: int = 100) -> List[MeetingResponse]:
        """Get all meetings for a user"""
        meetings = self.meeting_repo.get_by_user(user_id, skip, limit)
        return [MeetingResponse.model_validate(m) for m in meetings]

    def get_meeting(self, meeting_id: int, user_id: int) -> MeetingResponse:
        """Get a specific meeting"""
        meeting = self.meeting_repo.get_by_id(meeting_id)
        if not meeting or meeting.user_id != user_id:
            raise MeetingNotFoundError("Meeting not found")
        return MeetingResponse.model_validate(meeting)

    def process_meeting(self, meeting_id: int, user_id: int) -> MeetingResponse:
        """Process a meeting: transcribe, chunk, embed"""
        meeting = self.meeting_repo.get_by_id(meeting_id)
        if not meeting or meeting.user_id != user_id:
            raise MeetingNotFoundError("Meeting not found")

        try:
            # Update status to processing
            self.meeting_repo.update_status(meeting_id, "processing")

            # Step 1: Extract audio if video
            file_path = meeting.audio_path
            if file_path.endswith('.mp4'):
                file_path = self._extract_audio(file_path)

            # Step 2: Transcribe
            transcript_path = self._transcribe(file_path, meeting_id)
            self.meeting_repo.update_transcript_path(meeting_id, transcript_path)

            # Step 3: Chunk
            chunks = self._chunk_text(transcript_path)

            # Step 4: Store embeddings
            self.vector_repo.store_chunks(meeting_id, chunks)

            # Update status to completed
            self.meeting_repo.update_status(meeting_id, "completed")

            return MeetingResponse.model_validate(
                self.meeting_repo.get_by_id(meeting_id)
            )

        except Exception as e:
            self.meeting_repo.update_status(meeting_id, "failed")
            raise ProcessingError(f"Failed to process meeting: {str(e)}")

    def _extract_audio(self, video_path: str) -> str:
        """Extract audio from video using ffmpeg"""
        INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
        output_path = INTERMEDIATE_DIR / "clean_meeting_audio.wav"

        command = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-ar", "16000",
            "-ac", "1",
            "-af", "loudnorm,afftdn",
            str(output_path)
        ]

        subprocess.run(command, check=True)
        return str(output_path)

    def _transcribe(self, audio_path: str, meeting_id: int) -> str:
        """Transcribe audio using Whisper"""
        INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
        
        result = whisper_model.transcribe(audio_path, task="translate")
        
        output_path = INTERMEDIATE_DIR / f"transcript_{meeting_id}.txt"
        
        with open(output_path, "w", encoding="utf-8") as f:
            for seg in result["segments"]:
                f.write(seg["text"].strip() + "\n")

        return str(output_path)

    def _chunk_text(self, transcript_path: str) -> List[str]:
        """Split transcript into chunks"""
        with open(transcript_path, "r", encoding="utf-8") as f:
            text = f.read()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=150,
            chunk_overlap=30
        )

        return splitter.split_text(text)

    def delete_meeting(self, meeting_id: int, user_id: int) -> bool:
        """Delete a meeting and its data"""
        meeting = self.meeting_repo.get_by_id(meeting_id)
        if not meeting or meeting.user_id != user_id:
            raise MeetingNotFoundError("Meeting not found")

        # Delete vector collection
        self.vector_repo.delete_collection(meeting_id)

        # Delete meeting record
        return self.meeting_repo.delete(meeting_id)

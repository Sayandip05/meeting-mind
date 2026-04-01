"""Agent responsible for audio transcription using Whisper"""
import whisper
from pathlib import Path
from typing import Dict
from app.agents.base_agent import BaseAgent

# Load model once globally
_whisper_model = None


def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = whisper.load_model("small")
    return _whisper_model


class TranscriptionAgent(BaseAgent):
    """
    Agent: Transcription Agent
    Task: Convert audio to text using OpenAI Whisper
    Optimization: Indian accent optimized
    """
    
    def __init__(self):
        super().__init__("TranscriptionAgent")
        self.model = get_whisper_model()
    
    def _run(self, audio_path: str, meeting_id: int, output_dir: Path) -> Dict:
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to audio file
            meeting_id: Meeting identifier
            output_dir: Directory to save transcript
            
        Returns:
            Dict with transcript_path and segments
        """
        # Transcribe with translation for multilingual support
        result = self.model.transcribe(
            audio_path,
            task="translate",
            fp16=False  # CPU-friendly
        )
        
        # Save transcript
        output_dir.mkdir(parents=True, exist_ok=True)
        transcript_path = output_dir / f"transcript_{meeting_id}.txt"
        
        with open(transcript_path, "w", encoding="utf-8") as f:
            for seg in result["segments"]:
                f.write(seg["text"].strip() + "\n")
        
        return {
            "transcript_path": str(transcript_path),
            "segments": result["segments"],
            "language": result.get("language", "en"),
            "duration": result.get("duration", 0)
        }

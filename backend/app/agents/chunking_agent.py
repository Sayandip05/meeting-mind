"""Agent responsible for semantic text chunking"""
from pathlib import Path
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.agents.base_agent import BaseAgent


class ChunkingAgent(BaseAgent):
    """
    Agent: Chunking Agent
    Task: Split transcript into semantic chunks
    Strategy: Recursive character splitting with overlap
    """
    
    def __init__(self, chunk_size: int = 150, chunk_overlap: int = 30):
        super().__init__("ChunkingAgent")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def _run(self, transcript_path: str, meeting_id: int) -> Dict:
        """
        Split transcript into chunks
        
        Args:
            transcript_path: Path to transcript file
            meeting_id: Meeting identifier
            
        Returns:
            Dict with chunks list and metadata
        """
        # Read transcript
        with open(transcript_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        # Split into chunks
        chunks = self.splitter.split_text(text)
        
        return {
            "chunks": chunks,
            "total_chunks": len(chunks),
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "original_length": len(text)
        }
    
    def chunk_with_metadata(self, text: str, source: str = "") -> List[Dict]:
        """
        Chunk text and return with metadata
        
        Args:
            text: Text to chunk
            source: Source identifier
            
        Returns:
            List of chunks with metadata
        """
        chunks = self.splitter.split_text(text)
        return [
            {
                "content": chunk,
                "index": i,
                "source": source,
                "char_count": len(chunk)
            }
            for i, chunk in enumerate(chunks)
        ]

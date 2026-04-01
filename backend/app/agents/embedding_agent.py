"""Agent responsible for generating embeddings and storing in vector DB"""
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from app.agents.base_agent import BaseAgent
from app.repositories.vector_repository import VectorRepository

# Load model once globally
_embedding_model = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    return _embedding_model


class EmbeddingAgent(BaseAgent):
    """
    Agent: Embedding Agent
    Task: Generate embeddings and store in Qdrant
    Model: paraphrase-multilingual-MiniLM-L12-v2
    """
    
    def __init__(self):
        super().__init__("EmbeddingAgent")
        self.model = get_embedding_model()
        self.vector_repo = VectorRepository()
    
    def _run(self, chunks: List[str], meeting_id: int) -> Dict:
        """
        Generate embeddings and store in vector DB
        
        Args:
            chunks: List of text chunks
            meeting_id: Meeting identifier
            
        Returns:
            Dict with storage status
        """
        # Store chunks with embeddings
        num_stored = self.vector_repo.store_chunks(meeting_id, chunks)
        
        return {
            "meeting_id": meeting_id,
            "chunks_stored": num_stored,
            "embedding_dim": 384,
            "model": "paraphrase-multilingual-MiniLM-L12-v2",
            "status": "success"
        }
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        return self.model.encode(text).tolist()
    
    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        return self.model.encode(texts).tolist()

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from app.config import get_settings
from typing import List, Dict, Optional
import uuid

settings = get_settings()

# Load embedding model once
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


class VectorRepository:
    def __init__(self):
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port
        )
        self.embedding_dim = 384  # MiniLM-L12-v2 dimension

    def _get_collection_name(self, meeting_id: int) -> str:
        return f"meeting_{meeting_id}"

    def create_collection(self, meeting_id: int):
        """Create a new collection for a meeting"""
        collection_name = self._get_collection_name(meeting_id)
        
        # Check if collection exists
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if collection_name not in collection_names:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )
        return collection_name

    def store_chunks(self, meeting_id: int, chunks: List[str]):
        """Store chunks with embeddings for a meeting"""
        collection_name = self.create_collection(meeting_id)
        
        # Generate embeddings
        embeddings = embedding_model.encode(chunks).tolist()
        
        # Prepare points
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            points.append(
                PointStruct(
                    id=i,
                    vector=embedding,
                    payload={"text": chunk, "chunk_index": i}
                )
            )
        
        # Upload points
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )
        
        return len(points)

    def search(self, meeting_id: int, query: str, limit: int = 7) -> List[Dict]:
        """Search for relevant chunks"""
        collection_name = self._get_collection_name(meeting_id)
        
        # Generate query embedding
        query_embedding = embedding_model.encode([query]).tolist()[0]
        
        # Search
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=limit
        )
        
        return [
            {
                "text": r.payload["text"],
                "score": r.score,
                "chunk_index": r.payload.get("chunk_index", 0)
            }
            for r in results
        ]

    def multi_query_search(
        self,
        meeting_id: int,
        queries: List[str],
        limit_per_query: int = 6
    ) -> List[Dict]:
        """Search with multiple queries and deduplicate results"""
        all_results = []
        seen_texts = set()
        
        for query in queries:
            results = self.search(meeting_id, query, limit=limit_per_query)
            for r in results:
                # Deduplicate by text content
                text_key = r["text"][:100]  # Use first 100 chars as key
                if text_key not in seen_texts:
                    seen_texts.add(text_key)
                    all_results.append(r)
        
        return all_results

    def delete_collection(self, meeting_id: int):
        """Delete a meeting's collection"""
        collection_name = self._get_collection_name(meeting_id)
        try:
            self.client.delete_collection(collection_name)
            return True
        except Exception:
            return False

    def collection_exists(self, meeting_id: int) -> bool:
        """Check if collection exists"""
        collection_name = self._get_collection_name(meeting_id)
        collections = self.client.get_collections().collections
        return collection_name in [c.name for c in collections]

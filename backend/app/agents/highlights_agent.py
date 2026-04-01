"""Agent responsible for generating meeting highlights"""
from typing import List, Dict, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from app.agents.base_agent import BaseAgent
from app.repositories.vector_repository import VectorRepository
from app.config import get_settings
from pathlib import Path

settings = get_settings()


class HighlightsAgent(BaseAgent):
    """
    Agent: Highlights Agent
    Task: Extract key decisions, action items, deadlines
    Strategy: Multi-query retrieval + LLM summarization
    """
    
    def __init__(self):
        super().__init__("HighlightsAgent")
        self.llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            temperature=0,
            api_key=settings.groq_api_key
        )
        self.vector_repo = VectorRepository()
        
        # Multi-query strategy for comprehensive coverage
        self.highlight_queries = [
            "important topics discussed",
            "key decisions made",
            "tasks assigned or action items",
            "deadlines or commitments",
            "critical points or conclusions"
        ]
    
    def _run(self, meeting_id: int, output_dir: Optional[Path] = None) -> Dict:
        """
        Generate meeting highlights
        
        Args:
            meeting_id: Meeting identifier
            output_dir: Optional directory to save highlights
            
        Returns:
            Dict with highlights and metadata
        """
        # Multi-query retrieval
        results = self.vector_repo.multi_query_search(
            meeting_id,
            self.highlight_queries,
            limit_per_query=6
        )
        
        if not results:
            return {"highlights": "No highlights could be generated.", "sources": 0}
        
        # Build context (max 12 unique chunks)
        context = "\n\n".join([r["text"] for r in results[:12]])
        
        # Generate highlights
        prompt = ChatPromptTemplate.from_template("""
You are an expert meeting analyst.

Extract only the MOST IMPORTANT highlights from the meeting.

Rules:
- Only include decisions, action items, deadlines, or key conclusions
- Ignore filler conversation or casual talk
- Each highlight must be one concise sentence
- Do NOT repeat similar points
- Maximum 8 highlights

Format:
• Highlight

Meeting Text:
{text}
""")
        
        chain = prompt | self.llm
        result = chain.invoke({"text": context})
        highlights = result.content
        
        # Save to file if output_dir provided
        if output_dir:
            output_dir.mkdir(exist_ok=True)
            highlights_path = output_dir / f"highlights_{meeting_id}.txt"
            with open(highlights_path, "w", encoding="utf-8") as f:
                f.write(highlights)
        
        return {
            "highlights": highlights,
            "sources": len(results),
            "queries_used": len(self.highlight_queries)
        }
    
    def generate_custom_highlights(self, meeting_id: int, focus_areas: List[str]) -> Dict:
        """Generate highlights focusing on specific areas"""
        queries = focus_areas + self.highlight_queries[:2]
        results = self.vector_repo.multi_query_search(meeting_id, queries, limit_per_query=5)
        context = "\n\n".join([r["text"] for r in results[:10]])
        
        prompt = ChatPromptTemplate.from_template("""
Focus on these areas: {focus_areas}

Extract relevant highlights:

{text}
""")
        
        chain = prompt | self.llm
        result = chain.invoke({"text": context, "focus_areas": ", ".join(focus_areas)})
        
        return {"highlights": result.content, "focus_areas": focus_areas}

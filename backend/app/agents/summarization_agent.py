"""Agent responsible for comprehensive meeting summarization"""
from typing import Dict, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from app.agents.base_agent import BaseAgent
from app.repositories.vector_repository import VectorRepository
from app.config import get_settings
from pathlib import Path

settings = get_settings()


class SummarizationAgent(BaseAgent):
    """
    Agent: Summarization Agent
    Task: Generate comprehensive meeting summary
    Output: Structured summary with sections
    """
    
    def __init__(self):
        super().__init__("SummarizationAgent")
        self.llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            temperature=0.1,  # Slightly higher for more natural summary
            api_key=settings.groq_api_key
        )
        self.vector_repo = VectorRepository()
    
    def _run(self, meeting_id: int, output_dir: Optional[Path] = None) -> Dict:
        """
        Generate comprehensive meeting summary
        
        Args:
            meeting_id: Meeting identifier
            output_dir: Optional directory to save summary
            
        Returns:
            Dict with summary sections and metadata
        """
        # Retrieve broad context
        results = self.vector_repo.search(
            meeting_id,
            "comprehensive meeting content overview",
            limit=15
        )
        
        if not results:
            return {"summary": "Could not generate summary.", "sections": {}}
        
        context = "\n\n".join([r["text"] for r in results])
        
        # Generate structured summary
        prompt = ChatPromptTemplate.from_template("""
You are an expert meeting summarizer.

Provide a comprehensive summary of the meeting with the following sections:

1. **Overview**: Brief summary of what the meeting was about (2-3 sentences)
2. **Key Discussion Points**: Main topics discussed (bullet points)
3. **Decisions Made**: Any decisions or conclusions reached
4. **Action Items**: Tasks assigned with owners if mentioned
5. **Next Steps**: Follow-up items or future meetings mentioned

Keep it professional and concise.

Meeting Text:
{text}
""")
        
        chain = prompt | self.llm
        result = chain.invoke({"text": context})
        summary = result.content
        
        # Save to file if output_dir provided
        if output_dir:
            output_dir.mkdir(exist_ok=True)
            summary_path = output_dir / f"summary_{meeting_id}.txt"
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(summary)
        
        return {
            "summary": summary,
            "sources": len(results),
            "sections": ["Overview", "Key Discussion Points", "Decisions Made", "Action Items", "Next Steps"]
        }
    
    def generate_brief_summary(self, meeting_id: int, max_sentences: int = 3) -> Dict:
        """Generate a brief executive summary"""
        results = self.vector_repo.search(meeting_id, "meeting overview", limit=8)
        context = "\n\n".join([r["text"] for r in results])
        
        prompt = ChatPromptTemplate.from_template("""
Provide a brief executive summary in {max_sentences} sentences maximum.

Meeting Text:
{text}
""")
        
        chain = prompt | self.llm
        result = chain.invoke({"text": context, "max_sentences": max_sentences})
        
        return {
            "brief_summary": result.content,
            "max_sentences": max_sentences
        }

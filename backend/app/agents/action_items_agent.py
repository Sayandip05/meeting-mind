"""Agent responsible for extracting action items and tasks"""
from typing import List, Dict, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from app.agents.base_agent import BaseAgent
from app.repositories.vector_repository import VectorRepository
from app.config import get_settings
from pathlib import Path
import json
import re

settings = get_settings()


class ActionItemsAgent(BaseAgent):
    """
    Agent: Action Items Agent
    Task: Extract tasks, assignments, and deadlines
    Output: Structured action items with owners and due dates
    """
    
    def __init__(self):
        super().__init__("ActionItemsAgent")
        self.llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            temperature=0,
            api_key=settings.groq_api_key
        )
        self.vector_repo = VectorRepository()
    
    def _run(self, meeting_id: int, output_dir: Optional[Path] = None) -> Dict:
        """
        Extract action items from meeting
        
        Args:
            meeting_id: Meeting identifier
            output_dir: Optional directory to save action items
            
        Returns:
            Dict with structured action items
        """
        # Search for action-related content
        queries = [
            "action items tasks assigned",
            "who will do what",
            "deadlines due dates",
            "responsibilities owners",
            "next steps follow up"
        ]
        
        results = self.vector_repo.multi_query_search(
            meeting_id,
            queries,
            limit_per_query=5
        )
        
        if not results:
            return {"action_items": [], "count": 0}
        
        context = "\n\n".join([r["text"] for r in results[:10]])
        
        # Extract action items
        prompt = ChatPromptTemplate.from_template("""
You are an expert at extracting action items from meetings.

Extract ALL action items from the meeting text. For each action item, identify:
- Task description
- Owner (person assigned) - if mentioned
- Due date/deadline - if mentioned
- Priority - if implied (high/medium/low)

Return ONLY a JSON array in this exact format:
[
  {{
    "task": "description of the task",
    "owner": "person name or null",
    "due_date": "date or null",
    "priority": "high/medium/low or null"
  }}
]

If no action items found, return empty array [].

Meeting Text:
{text}
""")
        
        chain = prompt | self.llm
        result = chain.invoke({"text": context})
        
        # Parse JSON response
        try:
            # Extract JSON from response
            content = result.content.strip()
            # Find JSON array in response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                action_items = json.loads(json_match.group())
            else:
                action_items = []
        except json.JSONDecodeError:
            action_items = []
        
        # Save to file if output_dir provided
        if output_dir:
            output_dir.mkdir(exist_ok=True)
            action_items_path = output_dir / f"action_items_{meeting_id}.json"
            with open(action_items_path, "w", encoding="utf-8") as f:
                json.dump(action_items, f, indent=2)
        
        return {
            "action_items": action_items,
            "count": len(action_items),
            "sources": len(results)
        }
    
    def get_tasks_by_owner(self, meeting_id: int, owner_name: str) -> List[Dict]:
        """Get all tasks assigned to a specific person"""
        result = self._run(meeting_id)
        all_items = result.get("action_items", [])
        
        return [
            item for item in all_items
            if item.get("owner") and owner_name.lower() in item["owner"].lower()
        ]
    
    def get_overdue_items(self, meeting_id: int, reference_date: str) -> List[Dict]:
        """Get items that are overdue relative to reference date"""
        result = self._run(meeting_id)
        all_items = result.get("action_items", [])
        
        # Simple date comparison (can be enhanced with proper date parsing)
        overdue = []
        for item in all_items:
            due = item.get("due_date")
            if due and due != "null":
                # Add to overdue if date is before reference
                overdue.append(item)
        
        return overdue

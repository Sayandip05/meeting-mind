import os
from pathlib import Path
from typing import List, Dict, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langsmith import traceable
from app.config import get_settings
from app.repositories.vector_repository import VectorRepository

settings = get_settings()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
NOTES_DIR = BASE_DIR / "Notes"

# Initialize LLM
llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0,
    api_key=settings.groq_api_key
)


class AIAgentService:
    def __init__(self):
        self.vector_repo = VectorRepository()
        self.llm = llm

    @traceable(project_name=settings.langsmith_project)
    def generate_highlights(self, meeting_id: int) -> str:
        """Generate meeting highlights using multi-query retrieval"""
        
        # Multi-query retrieval
        queries = [
            "important topics discussed",
            "key decisions made",
            "tasks assigned or action items",
            "deadlines or commitments",
            "critical points or conclusions"
        ]
        
        results = self.vector_repo.multi_query_search(meeting_id, queries, limit_per_query=6)
        
        if not results:
            return "No highlights could be generated from this meeting."
        
        # Build context
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
        
        # Save highlights
        NOTES_DIR.mkdir(exist_ok=True)
        highlights_path = NOTES_DIR / f"highlights_{meeting_id}.txt"
        with open(highlights_path, "w", encoding="utf-8") as f:
            f.write(highlights)
        
        return highlights

    @traceable(project_name=settings.langsmith_project)
    def ask_question(self, meeting_id: int, question: str, chat_history: Optional[List[Dict]] = None) -> str:
        """Answer a question about a meeting"""
        
        # Retrieve relevant chunks
        results = self.vector_repo.search(meeting_id, question, limit=7)
        
        if not results:
            return "Not found in the meeting transcript"
        
        # Build context
        context = "\n\n".join([r["text"] for r in results])
        
        # Format chat history
        history_text = ""
        if chat_history:
            for msg in chat_history[-5:]:  # Last 5 messages
                role = "Human" if msg.get("is_user") else "Assistant"
                history_text += f"{role}: {msg.get('content', '')}\n"
        
        # Generate answer
        prompt = ChatPromptTemplate.from_template("""
You are an expert meeting assistant.

STRICT RULES:
- Answer ONLY from the provided context
- Do NOT guess or hallucinate
- If answer not present in context, say: "Not found in the meeting transcript"
- Keep answer concise but complete
- Prefer bullet points if multiple items
- Preserve numbers, dates, and names exactly
- Respond in the SAME language as the question

Previous Conversation:
{history}

Context from Meeting:
{context}

Question:
{question}

Answer:
""")
        
        chain = prompt | self.llm
        result = chain.invoke({
            "history": history_text,
            "context": context,
            "question": question
        })
        
        answer = result.content.strip()
        
        if not answer:
            return "Not found in the meeting transcript"
        
        return answer

    @traceable(project_name=settings.langsmith_project)
    def summarize_meeting(self, meeting_id: int) -> str:
        """Generate a comprehensive meeting summary"""
        
        # Retrieve broad context
        results = self.vector_repo.search(meeting_id, "meeting summary overview", limit=15)
        
        if not results:
            return "Could not generate summary for this meeting."
        
        context = "\n\n".join([r["text"] for r in results])
        
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
        
        return result.content


# LangGraph State for complex workflows
class MeetingAnalysisState:
    """State for LangGraph meeting analysis workflow"""
    meeting_id: int
    transcript_chunks: List[str]
    highlights: Optional[str]
    summary: Optional[str]
    action_items: Optional[List[str]]
    current_step: str


class MeetingAnalysisGraph:
    """LangGraph workflow for comprehensive meeting analysis"""
    
    def __init__(self):
        self.vector_repo = VectorRepository()
        self.llm = llm
        self.workflow = self._build_workflow()
    
    def _build_workflow(self):
        """Build the LangGraph workflow"""
        
        # Define nodes
        def retrieve_chunks(state: MeetingAnalysisState):
            """Retrieve all chunks for analysis"""
            results = self.vector_repo.search(
                state.meeting_id,
                "comprehensive meeting content",
                limit=20
            )
            state.transcript_chunks = [r["text"] for r in results]
            state.current_step = "chunks_retrieved"
            return state
        
        def generate_highlights_node(state: MeetingAnalysisState):
            """Generate highlights"""
            context = "\n\n".join(state.transcript_chunks[:12])
            
            prompt = ChatPromptTemplate.from_template("""
Extract key highlights from this meeting. Focus on decisions and action items.

{text}
""")
            chain = prompt | self.llm
            result = chain.invoke({"text": context})
            state.highlights = result.content
            state.current_step = "highlights_generated"
            return state
        
        def generate_summary_node(state: MeetingAnalysisState):
            """Generate summary"""
            context = "\n\n".join(state.transcript_chunks)
            
            prompt = ChatPromptTemplate.from_template("""
Provide a comprehensive meeting summary.

{text}
""")
            chain = prompt | self.llm
            result = chain.invoke({"text": context})
            state.summary = result.content
            state.current_step = "summary_generated"
            return state
        
        def extract_action_items_node(state: MeetingAnalysisState):
            """Extract action items"""
            context = "\n\n".join(state.transcript_chunks[:10])
            
            prompt = ChatPromptTemplate.from_template("""
Extract all action items from this meeting. List each on a new line with format:
- [Owner if mentioned]: [Action item]

{text}
""")
            chain = prompt | self.llm
            result = chain.invoke({"text": context})
            state.action_items = [line.strip() for line in result.content.split('\n') if line.strip().startswith('-')]
            state.current_step = "action_items_extracted"
            return state
        
        # Build graph
        workflow = StateGraph(MeetingAnalysisState)
        
        workflow.add_node("retrieve", retrieve_chunks)
        workflow.add_node("highlights", generate_highlights_node)
        workflow.add_node("summary", generate_summary_node)
        workflow.add_node("action_items", extract_action_items_node)
        
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "highlights")
        workflow.add_edge("highlights", "summary")
        workflow.add_edge("summary", "action_items")
        workflow.add_edge("action_items", END)
        
        return workflow.compile()
    
    def analyze(self, meeting_id: int) -> Dict:
        """Run full analysis on a meeting"""
        initial_state = MeetingAnalysisState(
            meeting_id=meeting_id,
            transcript_chunks=[],
            highlights=None,
            summary=None,
            action_items=None,
            current_step="started"
        )
        
        result = self.workflow.invoke(initial_state)
        return {
            "highlights": result.highlights,
            "summary": result.summary,
            "action_items": result.action_items
        }

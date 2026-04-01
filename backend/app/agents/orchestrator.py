"""Orchestrator for coordinating multiple agents"""
from typing import Dict, List, Optional, Any
from langgraph.graph import StateGraph, END
from langsmith import traceable
from app.config import get_settings
from app.agents.transcription_agent import TranscriptionAgent
from app.agents.chunking_agent import ChunkingAgent
from app.agents.embedding_agent import EmbeddingAgent
from app.agents.highlights_agent import HighlightsAgent
from app.agents.chat_agent import ChatAgent
from app.agents.summarization_agent import SummarizationAgent
from app.agents.action_items_agent import ActionItemsAgent
from pathlib import Path

settings = get_settings()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
INTERMEDIATE_DIR = BASE_DIR / "data" / "intermediate"
NOTES_DIR = BASE_DIR / "Notes"


class AgentState:
    """State for the agent workflow"""
    def __init__(self):
        self.meeting_id: int = 0
        self.audio_path: str = ""
        self.transcript_path: str = ""
        self.chunks: List[str] = []
        self.status: str = "idle"
        self.results: Dict[str, Any] = {}
        self.errors: List[str] = []


class AgentOrchestrator:
    """
    Orchestrator: Coordinates all agents for meeting processing
    
    Agents:
    1. TranscriptionAgent - Audio → Text
    2. ChunkingAgent - Text → Chunks
    3. EmbeddingAgent - Chunks → Vector DB
    4. HighlightsAgent - Generate highlights
    5. SummarizationAgent - Generate summary
    6. ActionItemsAgent - Extract tasks
    7. ChatAgent - Answer questions
    """
    
    def __init__(self):
        self.transcription_agent = TranscriptionAgent()
        self.chunking_agent = ChunkingAgent()
        self.embedding_agent = EmbeddingAgent()
        self.highlights_agent = HighlightsAgent()
        self.chat_agent = ChatAgent()
        self.summarization_agent = SummarizationAgent()
        self.action_items_agent = ActionItemsAgent()
        
        # Build LangGraph workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self):
        """Build the LangGraph workflow for meeting processing"""
        
        def transcribe_step(state: AgentState):
            """Step 1: Transcribe audio"""
            try:
                result = self.transcription_agent.execute(
                    audio_path=state.audio_path,
                    meeting_id=state.meeting_id,
                    output_dir=INTERMEDIATE_DIR
                )
                state.transcript_path = result["transcript_path"]
                state.results["transcription"] = result
                state.status = "transcribed"
            except Exception as e:
                state.errors.append(f"Transcription failed: {str(e)}")
                state.status = "failed"
            return state
        
        def chunk_step(state: AgentState):
            """Step 2: Chunk transcript"""
            try:
                result = self.chunking_agent.execute(
                    transcript_path=state.transcript_path,
                    meeting_id=state.meeting_id
                )
                state.chunks = result["chunks"]
                state.results["chunking"] = result
                state.status = "chunked"
            except Exception as e:
                state.errors.append(f"Chunking failed: {str(e)}")
                state.status = "failed"
            return state
        
        def embed_step(state: AgentState):
            """Step 3: Generate embeddings"""
            try:
                result = self.embedding_agent.execute(
                    chunks=state.chunks,
                    meeting_id=state.meeting_id
                )
                state.results["embedding"] = result
                state.status = "embedded"
            except Exception as e:
                state.errors.append(f"Embedding failed: {str(e)}")
                state.status = "failed"
            return state
        
        def analyze_step(state: AgentState):
            """Step 4: Run analysis agents in parallel"""
            try:
                # Run highlights, summary, and action items
                highlights_result = self.highlights_agent.execute(
                    meeting_id=state.meeting_id,
                    output_dir=NOTES_DIR
                )
                summary_result = self.summarization_agent.execute(
                    meeting_id=state.meeting_id,
                    output_dir=NOTES_DIR
                )
                action_items_result = self.action_items_agent.execute(
                    meeting_id=state.meeting_id,
                    output_dir=NOTES_DIR
                )
                
                state.results["highlights"] = highlights_result
                state.results["summary"] = summary_result
                state.results["action_items"] = action_items_result
                state.status = "completed"
            except Exception as e:
                state.errors.append(f"Analysis failed: {str(e)}")
                state.status = "failed"
            return state
        
        # Build graph
        workflow = StateGraph(AgentState)
        
        workflow.add_node("transcribe", transcribe_step)
        workflow.add_node("chunk", chunk_step)
        workflow.add_node("embed", embed_step)
        workflow.add_node("analyze", analyze_step)
        
        workflow.set_entry_point("transcribe")
        workflow.add_edge("transcribe", "chunk")
        workflow.add_edge("chunk", "embed")
        workflow.add_edge("embed", "analyze")
        workflow.add_edge("analyze", END)
        
        return workflow.compile()
    
    @traceable(project_name=settings.langsmith_project)
    def process_meeting(self, meeting_id: int, audio_path: str) -> Dict:
        """
        Process a meeting through all agents
        
        Args:
            meeting_id: Meeting identifier
            audio_path: Path to audio file
            
        Returns:
            Dict with all processing results
        """
        # Initialize state
        initial_state = AgentState()
        initial_state.meeting_id = meeting_id
        initial_state.audio_path = audio_path
        
        # Run workflow
        final_state = self.workflow.invoke(initial_state)
        
        return {
            "meeting_id": meeting_id,
            "status": final_state.status,
            "results": final_state.results,
            "errors": final_state.errors
        }
    
    def ask_question(self, meeting_id: int, question: str, chat_history: Optional[List] = None) -> Dict:
        """Ask a question about a meeting"""
        return self.chat_agent.execute(
            meeting_id=meeting_id,
            question=question,
            chat_history=chat_history
        )
    
    def get_highlights(self, meeting_id: int) -> Dict:
        """Get meeting highlights"""
        return self.highlights_agent.execute(meeting_id=meeting_id)
    
    def get_summary(self, meeting_id: int) -> Dict:
        """Get meeting summary"""
        return self.summarization_agent.execute(meeting_id=meeting_id)
    
    def get_action_items(self, meeting_id: int) -> Dict:
        """Get action items"""
        return self.action_items_agent.execute(meeting_id=meeting_id)
    
    def get_all_agents(self) -> List[str]:
        """List all available agents"""
        return [
            "TranscriptionAgent - Audio to text",
            "ChunkingAgent - Text segmentation",
            "EmbeddingAgent - Vector storage",
            "HighlightsAgent - Key points extraction",
            "ChatAgent - Q&A assistant",
            "SummarizationAgent - Meeting summary",
            "ActionItemsAgent - Task extraction"
        ]

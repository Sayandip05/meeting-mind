"""Agent responsible for conversational Q&A"""
from typing import List, Dict, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from app.agents.base_agent import BaseAgent
from app.repositories.vector_repository import VectorRepository
from app.config import get_settings

settings = get_settings()


class ChatAgent(BaseAgent):
    """
    Agent: Chat Agent
    Task: Answer questions about meeting content
    Features: Context-only answers, chat history, multi-language
    """
    
    def __init__(self):
        super().__init__("ChatAgent")
        self.llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            temperature=0,
            api_key=settings.groq_api_key
        )
        self.vector_repo = VectorRepository()
    
    def _run(
        self,
        meeting_id: int,
        question: str,
        chat_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Answer a question about the meeting
        
        Args:
            meeting_id: Meeting identifier
            question: User question
            chat_history: Optional previous messages
            
        Returns:
            Dict with answer and metadata
        """
        # Retrieve relevant chunks
        results = self.vector_repo.search(meeting_id, question, limit=7)
        
        if not results:
            return {
                "answer": "Not found in the meeting transcript",
                "sources": 0,
                "confidence": 0.0
            }
        
        # Build context
        context = "\n\n".join([r["text"] for r in results])
        avg_score = sum(r["score"] for r in results) / len(results)
        
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
            answer = "Not found in the meeting transcript"
        
        return {
            "answer": answer,
            "sources": len(results),
            "confidence": avg_score,
            "retrieved_chunks": [r["text"][:200] + "..." for r in results[:3]]
        }
    
    def follow_up_suggestions(self, meeting_id: int, last_question: str) -> List[str]:
        """Generate follow-up question suggestions"""
        suggestions = [
            "What were the main decisions?",
            "Who was assigned what tasks?",
            "What are the next steps?",
            "Were there any deadlines mentioned?"
        ]
        return suggestions

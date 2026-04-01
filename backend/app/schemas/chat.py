from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    meeting_id: int


class ChatResponse(BaseModel):
    answer: str


class HighlightsRequest(BaseModel):
    meeting_id: int


class HighlightsResponse(BaseModel):
    highlights: str

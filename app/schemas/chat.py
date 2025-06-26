from typing import List, Dict, Optional
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    max_results: Optional[int] = 5

class SourceInfo(BaseModel):
    source: str
    category: str
    tool_name: str
    certainty: float
    distance: float

class ChatResponse(BaseModel):
    response: str
    sources: List[SourceInfo]
    confidence: float
    processing_time: float

class HealthResponse(BaseModel):
    status: str
    weaviate_ready: bool
    model_ready: bool
    document_count: int
    last_updated: Optional[str] = None

from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    prompt: str
    model: Optional[str] = "llama3"
    temperature: Optional[float] = 0.7
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    response: str
    model: str
    latency_ms: int
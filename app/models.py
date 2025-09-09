from pydantic import BaseModel, Field
from typing import List, Optional


class ChatRequest(BaseModel):
    query: str = Field(..., description="User message (natural language)")


class ChatResponse(BaseModel):
    answer: str
    confidence: float
    topic_ok: bool
    truncated: bool


class KeywordsResponse(BaseModel):
    keywords: List[str]
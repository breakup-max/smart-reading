from typing import List, Optional

from pydantic import BaseModel


class UploadResponse(BaseModel):
    file_hash: str
    message: str


class EvidenceItem(BaseModel):
    content: str
    source: str
    page: Optional[int] = None
    score: float
    vector_score: float
    hybrid_score: float
    llm_score: Optional[float] = None


class ChatRequest(BaseModel):
    file_hash: str
    question: str


class ChatResponse(BaseModel):
    answer: str
    search_query: str
    rewritten: bool
    evidence: List[EvidenceItem]


class ErrorResponse(BaseModel):
    detail: str
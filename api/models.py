"""Pydantic request and response models for the Second Brain API."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class IngestURLRequest(BaseModel):
    url: str
    source_type: Optional[str] = "web"
    tags: Optional[List[str]] = []


class IngestFileRequest(BaseModel):
    source_type: Optional[str] = "file"
    tags: Optional[List[str]] = []


class IngestVoiceRequest(BaseModel):
    tags: Optional[List[str]] = []


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    include_metadata: bool = True


class SearchResult(BaseModel):
    doc_id: str
    title: str
    excerpt: str
    relevance_score: float
    source_type: str
    metadata: Optional[dict] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int
    execution_time_ms: float


class SynthesisRequest(BaseModel):
    query: str
    context_mode: Optional[str] = "cross_domain"


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class DocumentResult(BaseModel):
    doc_id: str
    title: str
    snippet: str
    relevance_score: float
    entities: List[str]
    source: str


class HealthResponse(BaseModel):
    status: str
    version: str
    documents_indexed: int
    entities_count: int
    timestamp: datetime


class IngestResponse(BaseModel):
    success: bool
    document_id: str
    message: str

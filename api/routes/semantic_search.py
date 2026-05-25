"""Enhanced semantic and hybrid search API endpoints."""

import time
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from api.hybrid_search_service import HybridSearchService
from api.cache import cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/semantic-search", tags=["semantic-search"])


# ─────────────────────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────────────────────


class SearchResult(BaseModel):
    """Single search result."""
    doc_id: str
    title: str
    content: str
    slug: Optional[str] = None
    score: float
    search_type: str  # "semantic", "keyword", or "hybrid"


class HybridSearchRequest(BaseModel):
    """Hybrid search request."""
    query: str
    top_k: int = 10
    semantic_weight: float = 0.7
    keyword_weight: float = 0.3


class HybridSearchResponse(BaseModel):
    """Hybrid search response."""
    query: str
    results: List[SearchResult]
    total_results: int
    execution_time_ms: float
    search_type: str = "hybrid"


class RelatedPagesResponse(BaseModel):
    """Related pages response."""
    page_slug: str
    related_pages: List[SearchResult]
    total_results: int


class DuplicateDetectionResponse(BaseModel):
    """Duplicate detection response."""
    page_slug: str
    duplicates: List[SearchResult]
    total_duplicates: int


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/hybrid", response_model=HybridSearchResponse)
async def hybrid_search(request: HybridSearchRequest):
    """
    Hybrid search combining semantic and keyword search.

    Uses both vector similarity and BM25 ranking for comprehensive results.
    Semantic search finds conceptually related content, while keyword search
    finds exact term matches. Combined weights let you balance precision/recall.

    **Parameters:**
    - `query`: Search terms
    - `top_k`: Number of results (default: 10)
    - `semantic_weight`: Vector similarity weight (0-1, default: 0.7)
    - `keyword_weight`: Keyword/BM25 weight (0-1, default: 0.3)

    **Returns:**
    - Ranked results by combined score
    - Execution time in milliseconds
    """
    start_time = time.time()

    try:
        # Check cache
        cache_key = f"hybrid_search:{request.query}:{request.top_k}:{request.semantic_weight}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for hybrid search: {request.query}")
            return cached_result

        # Perform search
        service = HybridSearchService()
        results = service.hybrid_search(
            query=request.query,
            top_k=request.top_k,
            semantic_weight=request.semantic_weight,
            keyword_weight=request.keyword_weight,
        )

        # Format response
        search_results = [
            SearchResult(
                doc_id=r["doc_id"],
                title=r["title"],
                content=r["content"][:200] if r["content"] else "",
                slug=r.get("slug"),
                score=r["score"],
                search_type=r.get("search_type", "hybrid"),
            )
            for r in results
        ]

        elapsed = (time.time() - start_time) * 1000
        response = HybridSearchResponse(
            query=request.query,
            results=search_results,
            total_results=len(search_results),
            execution_time_ms=elapsed,
        )

        cache.set(cache_key, response, ttl_seconds=300)
        logger.info(f"Hybrid search completed in {elapsed:.2f}ms")

        return response
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/semantic", response_model=HybridSearchResponse)
async def semantic_search(
    query: str = Query(..., description="Search query"),
    top_k: int = Query(10, description="Number of results"),
):
    """
    Pure semantic search using vector similarity.

    Finds conceptually related content regardless of exact keyword matches.
    Best for finding pages about similar topics or related ideas.

    **Parameters:**
    - `query`: Search terms
    - `top_k`: Number of results (default: 10)

    **Returns:**
    - Results ranked by semantic similarity (0-1)
    """
    start_time = time.time()

    try:
        cache_key = f"semantic_search:{query}:{top_k}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        service = HybridSearchService()
        results = service.semantic_search(query=query, top_k=top_k)

        search_results = [
            SearchResult(
                doc_id=r["doc_id"],
                title=r["title"],
                content=r["content"][:200] if r["content"] else "",
                slug=r.get("slug"),
                score=r["score"],
                search_type="semantic",
            )
            for r in results
        ]

        elapsed = (time.time() - start_time) * 1000
        response = HybridSearchResponse(
            query=query,
            results=search_results,
            total_results=len(search_results),
            execution_time_ms=elapsed,
            search_type="semantic",
        )

        cache.set(cache_key, response, ttl_seconds=300)
        return response
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keyword", response_model=HybridSearchResponse)
async def keyword_search(
    query: str = Query(..., description="Search query"),
    top_k: int = Query(10, description="Number of results"),
):
    """
    Keyword search using BM25 ranking.

    Finds pages with relevant keywords. Best for exact term matching,
    finding pages about specific topics by name.

    **Parameters:**
    - `query`: Search terms
    - `top_k`: Number of results (default: 10)

    **Returns:**
    - Results ranked by keyword relevance (BM25 score)
    """
    start_time = time.time()

    try:
        cache_key = f"keyword_search:{query}:{top_k}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        service = HybridSearchService()
        results = service.keyword_search(query=query, top_k=top_k)

        search_results = [
            SearchResult(
                doc_id=r["doc_id"],
                title=r["title"],
                content=r["content"][:200] if r["content"] else "",
                slug=r.get("slug"),
                score=r["score"],
                search_type="keyword",
            )
            for r in results
        ]

        elapsed = (time.time() - start_time) * 1000
        response = HybridSearchResponse(
            query=query,
            results=search_results,
            total_results=len(search_results),
            execution_time_ms=elapsed,
            search_type="keyword",
        )

        cache.set(cache_key, response, ttl_seconds=300)
        return response
    except Exception as e:
        logger.error(f"Keyword search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/related/{page_slug}", response_model=RelatedPagesResponse)
async def get_related_pages(
    page_slug: str,
    top_k: int = Query(5, description="Number of related pages"),
):
    """
    Find semantically related wiki pages.

    Discovers pages about similar topics without explicit links.
    Useful for "you might also be interested in..." recommendations.

    **Parameters:**
    - `page_slug`: Wiki page identifier
    - `top_k`: Number of related pages (default: 5)

    **Returns:**
    - Related pages sorted by semantic similarity
    """
    try:
        service = HybridSearchService()
        related = service.find_related_pages(page_slug=page_slug, top_k=top_k)

        related_results = [
            SearchResult(
                doc_id=r["doc_id"],
                title=r["title"],
                content=r["content"][:200] if r["content"] else "",
                slug=r.get("slug"),
                score=r["score"],
                search_type="semantic",
            )
            for r in related
        ]

        return RelatedPagesResponse(
            page_slug=page_slug,
            related_pages=related_results,
            total_results=len(related_results),
        )
    except Exception as e:
        logger.error(f"Failed to get related pages for {page_slug}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/duplicates/{page_slug}", response_model=DuplicateDetectionResponse)
async def detect_duplicates(
    page_slug: str,
    threshold: float = Query(0.85, ge=0.0, le=1.0, description="Similarity threshold"),
):
    """
    Detect potentially duplicate or very similar content.

    Finds pages with highly similar content (default: 85%+ similarity).
    Useful for maintaining knowledge base consistency and avoiding redundancy.

    **Parameters:**
    - `page_slug`: Wiki page to check
    - `threshold`: Similarity threshold 0-1 (default: 0.85)
      - 0.85+: Very similar (likely duplicates)
      - 0.75-0.85: Similar concepts
      - Below 0.75: Different content

    **Returns:**
    - Duplicate/similar pages ranked by similarity
    """
    try:
        service = HybridSearchService()
        duplicates = service.detect_duplicate_content(
            page_slug=page_slug,
            threshold=threshold,
        )

        duplicate_results = [
            SearchResult(
                doc_id=r["doc_id"],
                title=r["title"],
                content=r["content"][:200] if r["content"] else "",
                slug=r.get("slug"),
                score=r["score"],
                search_type="semantic",
            )
            for r in duplicates
        ]

        return DuplicateDetectionResponse(
            page_slug=page_slug,
            duplicates=duplicate_results,
            total_duplicates=len(duplicate_results),
        )
    except Exception as e:
        logger.error(f"Duplicate detection failed for {page_slug}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index-page")
async def index_wiki_page(
    slug: str = Query(..., description="Wiki page slug"),
    title: str = Query(..., description="Page title"),
    content: str = Query(..., description="Page content"),
):
    """
    Index a wiki page for semantic search.

    Embeds page and adds to vector database.
    Should be called when creating/updating wiki pages.

    **Parameters:**
    - `slug`: Unique page identifier
    - `title`: Page title
    - `content`: Page body content

    **Returns:**
    - Success status
    """
    try:
        service = HybridSearchService()
        success = service.index_wiki_page(
            page_slug=slug,
            title=title,
            content=content,
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to index page")

        return {"status": "indexed", "slug": slug}
    except Exception as e:
        logger.error(f"Failed to index page {slug}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

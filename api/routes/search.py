"""Semantic search API endpoints."""

import time
import logging
import json
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from process.embed import EmbeddingPipeline
from storage.vector_db import VectorStore
from api.cache import cache
from api.models import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    AdvancedSearchRequest,
    AdvancedSearchResponse,
    SearchFacet,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=SearchResponse)
async def semantic_search(request: SearchRequest):
    """Semantic search across all documents.

    Query text is embedded and compared against document vectors in Chroma.
    Returns top-K results sorted by cosine similarity (relevance score).
    Cached for 5 minutes.
    """
    start_time = time.time()

    try:
        cache_key = f"search:{request.query}:{request.top_k}"
        cached_result = cache.get(cache_key)

        if cached_result:
            logger.info(f"Cache hit for query: {request.query}")
            return cached_result

        pipeline = EmbeddingPipeline()
        vector_store = VectorStore()

        # Embed query
        logger.info(f"Embedding query: {request.query}")
        query_embedding = pipeline.embed_query(request.query)

        # Search vector store
        logger.info(f"Searching for top {request.top_k} results")
        results = vector_store.search(query_embedding, n_results=request.top_k)

        # Format response
        search_results = [
            SearchResult(
                doc_id=r["id"],
                title=r["metadata"].get("title", "Unknown"),
                excerpt=r["document"][:200],
                relevance_score=1 - r["distance"],  # Convert distance to similarity (0-1)
                source_type=r["metadata"].get("source_type", "unknown"),
                metadata=r["metadata"] if request.include_metadata else None,
            )
            for r in results
        ]

        elapsed = (time.time() - start_time) * 1000

        response = SearchResponse(
            query=request.query,
            results=search_results,
            total_results=len(search_results),
            execution_time_ms=elapsed,
        )

        cache.set(cache_key, response, ttl_seconds=300)

        logger.info(f"Search completed in {elapsed:.2f}ms, found {len(search_results)} results")

        return response

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def apply_filters(results: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Filter search results by metadata fields."""
    if not filters:
        return results

    filtered = results

    # Filter by source type
    if "source_type" in filters:
        filtered = [
            r for r in filtered
            if r["metadata"].get("source_type") == filters["source_type"]
        ]

    # Filter by date range
    if "date_after" in filters:
        filtered = [
            r for r in filtered
            if r["metadata"].get("ingestion_date", "") >= filters["date_after"]
        ]

    if "date_before" in filters:
        filtered = [
            r for r in filtered
            if r["metadata"].get("ingestion_date", "") <= filters["date_before"]
        ]

    return filtered


def compute_facets(results: List[Dict[str, Any]]) -> List[SearchFacet]:
    """Compute facet counts from search results."""
    facets = {}

    for result in results:
        metadata = result.get("metadata", {})

        # Count by source type
        source_type = metadata.get("source_type", "unknown")
        if "source_type" not in facets:
            facets["source_type"] = {}
        facets["source_type"][source_type] = facets["source_type"].get(source_type, 0) + 1

    # Convert to facet objects
    return [
        SearchFacet(name=name, counts=counts)
        for name, counts in facets.items()
    ]


@router.post("/advanced", response_model=AdvancedSearchResponse)
async def advanced_search(request: AdvancedSearchRequest):
    """Advanced semantic search with filters and aggregations.

    Supports:
    - Filtering by source_type, date range
    - Faceted aggregations (counts by source type)
    - Custom sorting (relevance or date)
    """
    start_time = time.time()

    try:
        pipeline = EmbeddingPipeline()
        vector_store = VectorStore()

        # Embed query
        logger.info(f"Embedding query: {request.query}")
        query_embedding = pipeline.embed_query(request.query)

        # Search with more results to account for filtering
        logger.info(f"Searching for top {request.top_k * 2} results (pre-filtering)")
        results = vector_store.search(query_embedding, n_results=min(request.top_k * 2, 100))

        # Apply filters
        if request.filters:
            logger.info(f"Applying filters: {request.filters}")
            results = apply_filters(results, request.filters)

        # Trim to top_k
        results = results[:request.top_k]

        # Format response
        search_results = [
            SearchResult(
                doc_id=r["id"],
                title=r["metadata"].get("title", "Unknown"),
                excerpt=r["document"][:200],
                relevance_score=1 - r["distance"],
                source_type=r["metadata"].get("source_type", "unknown"),
                metadata=r["metadata"] if request.include_metadata else None,
            )
            for r in results
        ]

        # Compute facets if requested
        facets = None
        if request.facets:
            facets = compute_facets(results)

        elapsed = (time.time() - start_time) * 1000

        logger.info(f"Advanced search completed in {elapsed:.2f}ms, found {len(search_results)} results")

        return AdvancedSearchResponse(
            query=request.query,
            results=search_results,
            total_results=len(search_results),
            execution_time_ms=elapsed,
            facets=facets,
        )

    except Exception as e:
        logger.error(f"Advanced search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

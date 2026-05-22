"""Semantic search API endpoints."""

import time
import logging
from fastapi import APIRouter, HTTPException
from process.embed import EmbeddingPipeline
from storage.vector_db import VectorStore
from api.models import SearchRequest, SearchResponse, SearchResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=SearchResponse)
async def semantic_search(request: SearchRequest):
    """Semantic search across all documents.

    Query text is embedded and compared against document vectors in Chroma.
    Returns top-K results sorted by cosine similarity (relevance score).
    """
    start_time = time.time()

    try:
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

        logger.info(f"Search completed in {elapsed:.2f}ms, found {len(search_results)} results")

        return SearchResponse(
            query=request.query,
            results=search_results,
            total_results=len(search_results),
            execution_time_ms=elapsed,
        )

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

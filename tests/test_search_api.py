"""Tests for semantic search API models and logic."""

import pytest
from api.models import SearchRequest, SearchResult, SearchResponse


def test_search_request_creation():
    """Test SearchRequest model creation."""
    request = SearchRequest(
        query="artificial intelligence",
        top_k=10,
        include_metadata=True
    )
    assert request.query == "artificial intelligence"
    assert request.top_k == 10
    assert request.include_metadata is True


def test_search_request_defaults():
    """Test SearchRequest with default values."""
    request = SearchRequest(query="test")
    assert request.query == "test"
    assert request.top_k == 10
    assert request.include_metadata is True


def test_search_result_creation():
    """Test SearchResult model creation."""
    result = SearchResult(
        doc_id="doc_1",
        title="Test Document",
        excerpt="This is a test excerpt",
        relevance_score=0.95,
        source_type="pdf",
        metadata={"author": "Test Author"}
    )
    assert result.doc_id == "doc_1"
    assert result.title == "Test Document"
    assert result.relevance_score == 0.95
    assert result.source_type == "pdf"


def test_search_response_creation():
    """Test SearchResponse model creation."""
    results = [
        SearchResult(
            doc_id="doc_1",
            title="Test 1",
            excerpt="Excerpt 1",
            relevance_score=0.95,
            source_type="pdf"
        ),
        SearchResult(
            doc_id="doc_2",
            title="Test 2",
            excerpt="Excerpt 2",
            relevance_score=0.85,
            source_type="url"
        )
    ]

    response = SearchResponse(
        query="test query",
        results=results,
        total_results=2,
        execution_time_ms=125.5
    )

    assert response.query == "test query"
    assert len(response.results) == 2
    assert response.total_results == 2
    assert response.execution_time_ms == 125.5


def test_search_response_empty_results():
    """Test SearchResponse with empty results."""
    response = SearchResponse(
        query="no results",
        results=[],
        total_results=0,
        execution_time_ms=50.0
    )
    assert response.total_results == 0
    assert len(response.results) == 0

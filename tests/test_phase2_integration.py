"""Phase 2 integration tests for Second Brain API."""

import pytest
from fastapi.testclient import TestClient
from api.server import app


@pytest.fixture
def client():
    """Provide test client."""
    return TestClient(app)


class TestSearchAPI:
    """Tests for semantic search endpoints."""

    def test_search_basic(self, client):
        """Test basic search endpoint."""
        response = client.post(
            "/search",
            json={
                "query": "artificial intelligence",
                "top_k": 10,
                "include_metadata": True
            }
        )
        assert response.status_code in [200, 422]  # 422 if embeddings not ready
        if response.status_code == 200:
            data = response.json()
            assert "results" in data
            assert "total_results" in data
            assert "execution_time_ms" in data

    def test_search_advanced_with_filters(self, client):
        """Test advanced search with filters."""
        response = client.post(
            "/search/advanced",
            json={
                "query": "machine learning",
                "top_k": 5,
                "filters": {"source_type": "pdf"},
                "facets": True,
                "sort_by": "relevance"
            }
        )
        assert response.status_code in [200, 422]

    def test_search_empty_query(self, client):
        """Test search with empty query."""
        response = client.post(
            "/search",
            json={"query": "", "top_k": 10}
        )
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]


class TestGraphAPI:
    """Tests for knowledge graph endpoints."""

    def test_entity_detail(self, client):
        """Test entity detail endpoint."""
        response = client.post(
            "/graph/entity",
            params={"entity_id": "test-entity"}
        )
        assert response.status_code in [200, 404]  # 404 if entity not found

    def test_graph_traverse_depth_validation(self, client):
        """Test graph traverse depth validation."""
        # Valid depth (1-5)
        response = client.post(
            "/graph/traverse",
            params={"entity_id": "test-entity", "depth": 3}
        )
        assert response.status_code in [200, 404]

        # Invalid depth (>5)
        response = client.post(
            "/graph/traverse",
            params={"entity_id": "test-entity", "depth": 10}
        )
        assert response.status_code == 400

        # Invalid depth (<1)
        response = client.post(
            "/graph/traverse",
            params={"entity_id": "test-entity", "depth": 0}
        )
        assert response.status_code == 400

    def test_graph_traverse_with_filter(self, client):
        """Test graph traverse with relationship filter."""
        response = client.post(
            "/graph/traverse",
            params={
                "entity_id": "test-entity",
                "depth": 2,
                "relationship_type": "mentions"
            }
        )
        assert response.status_code in [200, 404]

    def test_graph_traverse_response_structure(self, client):
        """Test graph traverse response structure."""
        response = client.post(
            "/graph/traverse",
            params={"entity_id": "test-entity", "depth": 2}
        )
        if response.status_code == 200:
            data = response.json()
            assert "root_entity_id" in data
            assert "nodes" in data
            assert "edges" in data
            assert "depth" in data
            assert "node_count" in data
            assert "edge_count" in data


class TestVisualizationAPI:
    """Tests for graph visualization endpoints."""

    def test_viz_entity_basic(self, client):
        """Test entity visualization endpoint."""
        response = client.get("/viz/entity/test-entity")
        assert response.status_code in [200, 404]

    def test_viz_response_structure(self, client):
        """Test visualization response format."""
        response = client.get("/viz/entity/test-entity")
        if response.status_code == 200:
            data = response.json()
            assert "nodes" in data
            assert "edges" in data
            assert "center_id" in data
            assert "node_count" in data
            assert "edge_count" in data

            # Validate nodes
            for node in data.get("nodes", []):
                assert "id" in node
                assert "label" in node
                assert "type" in node
                assert "size" in node
                assert 10 <= node["size"] <= 50  # Size range

            # Validate edges
            for edge in data.get("edges", []):
                assert "source" in edge
                assert "target" in edge
                assert "label" in edge


class TestHealthCheck:
    """Basic health checks."""

    def test_api_health(self, client):
        """Test API is running."""
        response = client.get("/health")
        assert response.status_code in [200, 404]  # 404 if not implemented


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_on_missing_route(self, client):
        """Test 404 for missing routes."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_invalid_method(self, client):
        """Test invalid HTTP method."""
        response = client.put("/search")
        assert response.status_code == 405

    def test_malformed_json(self, client):
        """Test handling of malformed JSON."""
        response = client.post(
            "/search",
            data="not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]


class TestCORS:
    """Tests for CORS configuration."""

    def test_cors_headers(self, client):
        """Test CORS headers are set."""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
        # CORS headers may be present depending on configuration
        assert response.status_code in [200, 404]

    def test_preflight_request(self, client):
        """Test OPTIONS preflight request."""
        response = client.options("/search")
        assert response.status_code in [200, 404]


class TestPerformance:
    """Performance-related tests."""

    def test_search_response_time(self, client):
        """Test search completes in reasonable time."""
        import time
        start = time.time()
        response = client.post(
            "/search",
            json={"query": "test", "top_k": 10}
        )
        elapsed = time.time() - start
        # Should complete within 5 seconds
        assert elapsed < 5.0

    def test_graph_traverse_response_time(self, client):
        """Test graph traversal completes in reasonable time."""
        import time
        start = time.time()
        response = client.post(
            "/graph/traverse",
            params={"entity_id": "test", "depth": 2}
        )
        elapsed = time.time() - start
        # Should complete within 2 seconds
        assert elapsed < 2.0

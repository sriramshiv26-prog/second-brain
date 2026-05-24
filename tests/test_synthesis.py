"""Tests for Phase 6: Wiki and Synthesis System"""

import pytest
import json
from datetime import datetime
from storage.wiki_db import get_wiki_db, WikiPage
from api.synthesis_service import get_synthesis_service


class TestWikiLayer:
    """Test Task 1: Wiki Database Layer"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.wiki_db = get_wiki_db()

    def test_wiki_page_creation(self):
        """Test creating a wiki page"""
        page = self.wiki_db.create_page(
            slug="test-entity",
            title="Test Entity",
            content="This is a test page",
            entity_ids=["entity_123"]
        )

        assert page is not None
        assert page.slug == "test-entity"
        assert page.title == "Test Entity"
        assert "entity_123" in page.entity_ids
        assert page.version == 1

    def test_wiki_page_retrieval(self):
        """Test fetching a wiki page"""
        created = self.wiki_db.create_page(
            slug="retrieve-test",
            title="Retrieve Test",
            content="Content for retrieval",
            entity_ids=["entity_456"]
        )

        retrieved = self.wiki_db.get_page("retrieve-test")

        assert retrieved is not None
        assert retrieved.slug == "retrieve-test"
        assert retrieved.content == "Content for retrieval"

    def test_wiki_page_update(self):
        """Test updating a wiki page"""
        self.wiki_db.create_page(
            slug="update-test",
            title="Original Title",
            content="Original content"
        )

        updated = self.wiki_db.update_page(
            slug="update-test",
            title="Updated Title",
            content="Updated content"
        )

        assert updated.title == "Updated Title"
        assert updated.content == "Updated content"
        assert updated.version == 2

    def test_wiki_page_search(self):
        """Test searching wiki pages"""
        self.wiki_db.create_page(
            slug="machine-learning",
            title="Machine Learning",
            content="ML is about teaching computers"
        )
        self.wiki_db.create_page(
            slug="deep-learning",
            title="Deep Learning",
            content="DL uses neural networks"
        )

        results = self.wiki_db.search_pages("learning")

        assert len(results) >= 2

    def test_wiki_backlinks(self):
        """Test creating and retrieving backlinks"""
        self.wiki_db.create_page(
            slug="neural-networks",
            title="Neural Networks",
            content="NN content"
        )
        self.wiki_db.create_page(
            slug="deep-learning",
            title="Deep Learning",
            content="DL content"
        )

        backlink = self.wiki_db.add_backlink(
            from_slug="deep-learning",
            to_slug="neural-networks",
            context="Uses neural networks"
        )

        assert backlink.from_slug == "deep-learning"
        assert backlink.to_slug == "neural-networks"

        backlinks = self.wiki_db.get_backlinks("neural-networks")
        assert len(backlinks) >= 1

    def test_wiki_page_deletion(self):
        """Test deleting a wiki page"""
        self.wiki_db.create_page(
            slug="to-delete",
            title="To Delete",
            content="This will be deleted"
        )

        success = self.wiki_db.delete_page("to-delete")
        assert success is True

        retrieved = self.wiki_db.get_page("to-delete")
        assert retrieved is None


class TestSynthesisIntegration:
    """Test Task 2: Document Integration"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.synthesis_service = get_synthesis_service()
        self.wiki_db = get_wiki_db()

    @pytest.mark.asyncio
    async def test_document_integration_creates_wiki_pages(self):
        """Test that integrating a document creates wiki pages"""
        entities = [
            {
                "id": "entity_001",
                "name": "Python Programming",
                "type": "concept",
                "definition": "A high-level programming language"
            }
        ]

        wiki_mapping = await self.synthesis_service.integrate_document(
            doc_id="doc_001",
            entities=entities,
            doc_title="AI Basics"
        )

        assert len(wiki_mapping) >= 1
        assert "entity_001" in wiki_mapping

    def test_slug_generation(self):
        """Test wiki slug generation"""
        slug = self.synthesis_service._create_entity_slug("Machine Learning Systems")
        assert slug == "machine-learning-systems"

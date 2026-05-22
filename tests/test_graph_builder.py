import pytest
import sqlite3
import tempfile
from pathlib import Path
from storage.graph_db import init_graph_db, GraphDB

@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = init_graph_db(str(db_path))
        yield GraphDB(conn)
        conn.close()

def test_add_document(temp_db):
    """Test adding a document."""
    success = temp_db.add_document(
        doc_id="doc_1",
        source_type="file",
        source_path="/path/to/document.pdf",
        title="Test Document",
        content_hash="abc123"
    )
    assert success is True

def test_add_or_get_entity(temp_db):
    """Test adding and retrieving entities."""
    entity_id_1 = temp_db.add_or_get_entity("Transformer", "concept", "A neural architecture")
    entity_id_2 = temp_db.add_or_get_entity("transformer", "concept")  # Case-insensitive

    assert entity_id_1 == entity_id_2

def test_add_relationship(temp_db):
    """Test adding relationships."""
    ent1 = temp_db.add_or_get_entity("BERT", "concept")
    ent2 = temp_db.add_or_get_entity("Transformer", "concept")

    success = temp_db.add_relationship(ent1, ent2, "based_on")
    assert success is True

def test_link_document_entities(temp_db):
    """Test linking document to entities."""
    doc_id = "doc_1"
    ent1 = temp_db.add_or_get_entity("AI", "concept")
    ent2 = temp_db.add_or_get_entity("Learning", "concept")

    temp_db.add_document(doc_id, "file", "/test", "Test", "hash123")
    temp_db.link_document_to_entities(doc_id, [ent1, ent2])

    # Verify links
    docs = temp_db.get_entity_documents(ent1)
    assert len(docs) == 1
    assert docs[0]["id"] == doc_id

def test_get_entity_relationships(temp_db):
    """Test retrieving entity relationships."""
    ent1 = temp_db.add_or_get_entity("NLP", "concept")
    ent2 = temp_db.add_or_get_entity("Language", "concept")
    temp_db.add_relationship(ent1, ent2, "relates_to")

    rels = temp_db.get_entity_relationships(ent1)
    assert len(rels) > 0

import pytest
import json
from storage.entity_store import EntityStore

@pytest.fixture
def entity_store(tmp_path):
    return EntityStore(entities_dir=tmp_path)

def test_create_entity(entity_store):
    """Test creating an entity."""
    entity_id = entity_store.create_entity(
        name="Transformer",
        entity_type="concept",
        definition="A neural network architecture"
    )

    assert entity_id is not None
    entity = entity_store.get_entity(entity_id)
    assert entity["name"] == "Transformer"
    assert entity["type"] == "concept"

def test_get_entity_by_name(entity_store):
    """Test retrieving entity by name."""
    entity_id = entity_store.create_entity(
        name="BERT",
        entity_type="concept"
    )

    entity = entity_store.get_entity_by_name("bert")  # case-insensitive
    assert entity is not None
    assert entity["id"] == entity_id

def test_update_entity(entity_store):
    """Test updating entity."""
    entity_id = entity_store.create_entity(
        name="NLP",
        entity_type="concept"
    )

    entity_store.update_entity(entity_id, {"mention_count": 5})
    updated = entity_store.get_entity(entity_id)
    assert updated["mention_count"] == 5

def test_list_entities_by_type(entity_store):
    """Test listing entities by type."""
    entity_store.create_entity("Alice", "person")
    entity_store.create_entity("Bob", "person")
    entity_store.create_entity("Python", "concept")

    people = entity_store.list_entities_by_type("person")
    assert len(people) == 2
    assert all(e["type"] == "person" for e in people)

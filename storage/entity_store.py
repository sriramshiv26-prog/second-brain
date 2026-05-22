import json
import uuid
from pathlib import Path
from typing import Dict, List, Any
from config.constants import ENTITIES_DIR
import logging

logger = logging.getLogger(__name__)

class EntityStore:
    """Store and retrieve entities from JSON files."""

    def __init__(self, entities_dir: Path = None):
        self.entities_dir = entities_dir or ENTITIES_DIR
        self.entities_dir.mkdir(parents=True, exist_ok=True)

    def create_entity(self, name: str, entity_type: str, definition: str = None, metadata: Dict = None) -> str:
        """Create a new entity."""
        entity_id = f"ent_{uuid.uuid4().hex[:12]}"

        entity = {
            "id": entity_id,
            "name": name,
            "type": entity_type,
            "definition": definition,
            "aliases": [],
            "mention_count": 1,
            "first_mentioned": None,
            "tags": [],
            "metadata": metadata or {}
        }

        self._save_entity(entity_id, entity)
        logger.info(f"Created entity {entity_id}: {name}")
        return entity_id

    def get_entity(self, entity_id: str) -> Dict:
        """Get entity by ID."""
        path = self.entities_dir / f"{entity_id}.json"
        if path.exists():
            return json.loads(path.read_text())
        return None

    def get_entity_by_name(self, name: str) -> Dict:
        """Find entity by name (case-insensitive)."""
        name_lower = name.lower()
        for entity_file in self.entities_dir.glob("*.json"):
            entity = json.loads(entity_file.read_text())
            if entity["name"].lower() == name_lower:
                return entity
        return None

    def update_entity(self, entity_id: str, updates: Dict):
        """Update entity fields."""
        entity = self.get_entity(entity_id)
        if entity:
            entity.update(updates)
            self._save_entity(entity_id, entity)
            logger.info(f"Updated entity {entity_id}")

    def _save_entity(self, entity_id: str, entity: Dict):
        """Save entity to file."""
        path = self.entities_dir / f"{entity_id}.json"
        path.write_text(json.dumps(entity, indent=2))

    def list_entities_by_type(self, entity_type: str) -> List[Dict]:
        """List all entities of a specific type."""
        results = []
        for entity_file in self.entities_dir.glob("*.json"):
            entity = json.loads(entity_file.read_text())
            if entity["type"] == entity_type:
                results.append(entity)
        return results

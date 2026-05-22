# Entity Extraction Pipeline

## Overview

Entity extraction identifies and catalogs key concepts, people, organizations, projects, and locations from your documents. This creates a queryable knowledge graph where entities are nodes and relationships are edges.

## Components

### EntityExtractor (`process/extract_entities.py`)

Extracts entities and relationships from text using Ollama (local LLM).

**Key Methods:**

- **`extract(text: str, doc_id: str = None) -> Dict[str, Any]`**
  - Extracts entities and relationships from text
  - Truncates text to 5,000 chars to respect token limits
  - Returns JSON with entities and relationships arrays
  - Uses JSON-structured prompting for reliable parsing

**Entity Types:**
- `person` — individuals, authors, researchers
- `concept` — ideas, theories, techniques, frameworks
- `organization` — companies, institutions, teams
- `project` — research projects, products, initiatives
- `location` — places, cities, regions

**Relationship Types:**
- `mentions` — entity mentioned in context
- `relates_to` — conceptual relationship
- `cites` — formal citation or attribution
- `authored_by` — authorship relationship
- `tags` — categorical labels

### EntityStore (`storage/entity_store.py`)

Persists extracted entities as JSON files for efficient retrieval and updates.

**Key Methods:**

- **`create_entity(name, entity_type, definition, metadata) -> str`**
  - Create new entity with unique ID (format: `ent_<12-char-hex>`)
  - Stores as JSON file: `entities/ent_XXXXX.json`
  - Returns entity ID

- **`get_entity(entity_id) -> Dict`**
  - Retrieve entity by ID

- **`get_entity_by_name(name) -> Dict`**
  - Case-insensitive lookup by name
  - Returns full entity object if found

- **`update_entity(entity_id, updates)`**
  - Merge updates into existing entity
  - Persists immediately to disk

- **`list_entities_by_type(entity_type) -> List[Dict]`**
  - List all entities of specific type
  - Useful for browsing related concepts

## Extraction Workflow

```
Document Text
    ↓
[EntityExtractor.extract via Ollama]
    ↓
JSON Response:
{
  "entities": [
    {"name": "Transformer", "type": "concept", "definition": "..."},
    {"name": "Yann LeCun", "type": "person", "definition": "..."}
  ],
  "relationships": [
    {"source": "Transformer", "target": "Attention", "type": "relates_to"}
  ]
}
    ↓
[EntityStore.create_entity] (for each entity)
    ↓
JSON Files in entities/ Directory
```

## Configuration

See `config/constants.py`:

```python
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL_ENTITY = "qwen2.5-coder"
ENTITY_TYPES = {"person", "concept", "organization", "project", "location"}
```

## Prompt Structure

The extractor uses JSON-structured prompting to ensure reliable parsing:

```python
prompt = """Extract entities and relationships from this text.

Return ONLY valid JSON with this structure:
{
    "entities": [
        {"name": "...", "type": "person|concept|organization|project|location", "definition": "..."}
    ],
    "relationships": [
        {"source": "entity_name_1", "target": "entity_name_2", "type": "mentions|relates_to|cites|authored_by"}
    ]
}

Text:
{text_truncated}"""
```

## Notes

- Uses local Ollama (qwen2.5-coder model) for zero-cost, private extraction
- Text truncated to 5,000 chars to avoid token limits
- JSON parsing includes regex fallback to handle incomplete responses
- Entities stored as individual JSON files for easy inspection and updates
- Entity IDs are collision-resistant (12-character hex UUIDs)

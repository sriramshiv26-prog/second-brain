# Knowledge Graph Builder

## Overview

The graph builder creates a queryable knowledge graph by linking documents to extracted entities and building relationships between entities. This enables cross-document reasoning and relationship discovery.

## Components

### GraphDB (`storage/graph_db.py`)

High-level interface for graph database operations using SQLite.

**Key Methods:**

- **`add_document(doc_id, source_type, source_path, title, content_hash, metadata) -> bool`**
  - Add document to graph
  - Source types: `url`, `file`, `voice`, `obsidian`, `genspark`
  - Returns `True` on success, `False` if document already exists
  - Content hash prevents duplicate ingestion

- **`add_or_get_entity(name, entity_type, definition) -> str`**
  - Add entity or return existing ID if entity with same name exists
  - Case-insensitive name matching
  - Returns entity ID (format: `ent_<12-char-hex>`)
  - Auto-creates if new

- **`add_relationship(source_entity_id, target_entity_id, rel_type, confidence=1.0) -> bool`**
  - Create directed relationship between entities
  - Types: `mentions`, `relates_to`, `cites`, `authored_by`, `tags`
  - Confidence score (0.0-1.0) for uncertain relationships
  - Returns `True` on success, `False` if relationship already exists

- **`link_document_to_entities(doc_id, entity_ids)`**
  - Associate document with extracted entities
  - Tracks occurrence count (incremented if linked multiple times)
  - Supports deduplication in ingestion pipeline

- **`get_entity_documents(entity_id, limit=10) -> List[Dict]`**
  - Retrieve all documents mentioning an entity
  - Sorted by occurrence count (most-mentioned first)
  - Returns document ID, title, source path, mention count

- **`get_entity_relationships(entity_id) -> List[Dict]`**
  - Retrieve all relationships for an entity (both incoming and outgoing)
  - Returns related entity name, type, and relationship type
  - Bidirectional query (finds A→B and B→A)

## Data Model

### Documents Table
```sql
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    source_type TEXT,              -- 'url', 'file', 'voice', etc.
    source_path TEXT,              -- URL or file path
    title TEXT,
    ingestion_date TIMESTAMP,
    content_hash TEXT UNIQUE,       -- Prevents duplicate ingestion
    metadata_json TEXT
);
```

### Entities Table
```sql
CREATE TABLE entities (
    id TEXT PRIMARY KEY,            -- ent_XXXXX format
    name TEXT NOT NULL UNIQUE,      -- Entity name
    type TEXT,                      -- person, concept, organization, etc.
    definition TEXT,                -- Description
    first_seen TIMESTAMP,
    last_updated TIMESTAMP,
    mention_count INTEGER,          -- Across all documents
    metadata_json TEXT
);
```

### Relationships Table
```sql
CREATE TABLE relationships (
    id TEXT PRIMARY KEY,            -- rel_XXXXX format
    source_entity_id TEXT,
    target_entity_id TEXT,
    relationship_type TEXT,         -- mentions, relates_to, cites, etc.
    confidence REAL,                -- 0.0-1.0
    UNIQUE(source_entity_id, target_entity_id, relationship_type)
);
```

### Document-Entity Junction Table
```sql
CREATE TABLE document_entities (
    document_id TEXT,
    entity_id TEXT,
    occurrence_count INTEGER,       -- How many times mentioned in doc
    PRIMARY KEY (document_id, entity_id)
);
```

## Workflow

```
Extracted Entities & Relationships
    ↓
[GraphDB.add_or_get_entity] (for each entity)
    ↓
Entity IDs (ent_XXXXX)
    ↓
[GraphDB.add_relationship] (for each relationship)
    ↓
SQLite relationships table
    ↓
[GraphDB.link_document_to_entities]
    ↓
SQLite document_entities junction table
```

## Query Examples

### Find related concepts
```python
graph = GraphDB()
relationships = graph.get_entity_relationships("ent_abc123")
# Returns all entities related to this concept
```

### Find mentions of an entity
```python
documents = graph.get_entity_documents("ent_person_1", limit=20)
# Returns all documents mentioning this person, sorted by frequency
```

### Build entity profile
```python
entity = graph.get_entity(entity_id)
docs = graph.get_entity_documents(entity_id)
relationships = graph.get_entity_relationships(entity_id)
# Complete view of entity: definition, where mentioned, what it relates to
```

## Indexes

The schema includes indexes on frequently-queried columns:

```sql
CREATE INDEX idx_entities_name ON entities(name);
CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_documents_source_type ON documents(source_type);
CREATE INDEX idx_relationships_source ON relationships(source_entity_id);
CREATE INDEX idx_relationships_target ON relationships(target_entity_id);
```

## Notes

- SQLite chosen for portability (single file, no server)
- UNIQUE constraint on relationships prevents duplicate edges
- Case-insensitive entity name matching enables deduplication
- Content hash on documents prevents re-ingesting the same file
- Thread-safe: each connection opens fresh (no caching)

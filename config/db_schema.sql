-- Second Brain Database Schema

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,  -- url, file, voice, obsidian, genspark
    source_path TEXT NOT NULL,
    title TEXT,
    ingestion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content_hash TEXT UNIQUE NOT NULL,
    metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL,  -- person, concept, organization, project, location
    definition TEXT,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    mention_count INTEGER DEFAULT 1,
    metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS relationships (
    id TEXT PRIMARY KEY,
    source_entity_id TEXT NOT NULL,
    target_entity_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,  -- mentions, cites, relates_to, authored_by, tags
    confidence REAL DEFAULT 1.0,
    FOREIGN KEY (source_entity_id) REFERENCES entities(id),
    FOREIGN KEY (target_entity_id) REFERENCES entities(id),
    UNIQUE(source_entity_id, target_entity_id, relationship_type)
);

CREATE TABLE IF NOT EXISTS document_entities (
    document_id TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    occurrence_count INTEGER DEFAULT 1,
    PRIMARY KEY (document_id, entity_id),
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (entity_id) REFERENCES entities(id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
CREATE INDEX IF NOT EXISTS idx_documents_source_type ON documents(source_type);
CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_entity_id);

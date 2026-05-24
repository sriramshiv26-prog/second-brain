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

-- Phase 6: Wiki Pages for Knowledge Synthesis
CREATE TABLE IF NOT EXISTS wiki_pages (
    id TEXT PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synthesis TIMESTAMP,
    entity_ids TEXT,
    contradiction_count INTEGER DEFAULT 0,
    version INTEGER DEFAULT 1,
    synthesized_content TEXT
);

CREATE TABLE IF NOT EXISTS wiki_backlinks (
    from_slug TEXT NOT NULL,
    to_slug TEXT NOT NULL,
    context TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (from_slug, to_slug),
    FOREIGN KEY (from_slug) REFERENCES wiki_pages(slug),
    FOREIGN KEY (to_slug) REFERENCES wiki_pages(slug)
);

CREATE TABLE IF NOT EXISTS contradictions (
    id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    wiki_slug TEXT NOT NULL,
    statement_a TEXT NOT NULL,
    statement_b TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolution_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entity_id) REFERENCES entities(id),
    FOREIGN KEY (wiki_slug) REFERENCES wiki_pages(slug)
);

CREATE TABLE IF NOT EXISTS synthesis_logs (
    id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    wiki_slug TEXT NOT NULL,
    synthesis_type TEXT,
    input_content TEXT,
    output_content TEXT,
    cost REAL DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entity_id) REFERENCES entities(id),
    FOREIGN KEY (wiki_slug) REFERENCES wiki_pages(slug)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
CREATE INDEX IF NOT EXISTS idx_documents_source_type ON documents(source_type);
CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_entity_id);
CREATE INDEX IF NOT EXISTS idx_wiki_pages_slug ON wiki_pages(slug);
CREATE INDEX IF NOT EXISTS idx_wiki_pages_entity_ids ON wiki_pages(entity_ids);
CREATE INDEX IF NOT EXISTS idx_contradictions_entity ON contradictions(entity_id);
CREATE INDEX IF NOT EXISTS idx_contradictions_resolved ON contradictions(resolved);
CREATE INDEX IF NOT EXISTS idx_synthesis_logs_entity ON synthesis_logs(entity_id);

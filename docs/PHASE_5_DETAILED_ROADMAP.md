# Phase 5: Complete Implementation Roadmap

**Status**: PLANNED  
**Estimated Time**: 24-32 hours  
**Cost**: $0 (local Ollama + Claude Sonnet for strategic decisions)  
**Target Completion**: 1-2 weeks  

## Overview

Phase 5 expands the Second Brain system with three major components:
1. **Backend Integration** (8-12h) — Connect Phase 4 stub endpoints to real database data
2. **Frontend Enhancement** (6-8h) — Build UI components for analytics, export/import, settings
3. **Extensibility** (8-12h) — Email/Slack/RSS integrations, plugin framework, mobile PWA

## Part 1: Backend Integration (Tasks 1-5)

### Task 1: Analytics Database Queries (3h)

**File**: `api/routes/analytics.py`

Convert stub endpoints to real database queries:

```python
# GET /analytics/overview
- SELECT COUNT(*) as total_entities FROM entities
- SELECT COUNT(*) as total_relationships FROM relationships
- SELECT COUNT(*) as total_documents FROM documents
- SELECT COUNT(*) as total_citations FROM citations
- Calculate average entity mention count

# GET /analytics/entity-types
- SELECT type, COUNT(*) FROM entities GROUP BY type

# GET /analytics/search-analytics
- Store search queries in new table: search_queries (id, query_text, timestamp, result_count)
- SELECT COUNT(*), AVG(result_count), AVG(response_time_ms) FROM search_queries
- Most popular queries from last 30 days

# GET /analytics/citation-analytics
- SELECT entity_id, COUNT(*) as citation_count FROM citations GROUP BY entity_id
- SELECT format, COUNT(*) FROM citations GROUP BY format

# GET /analytics/relationship-analytics
- SELECT relationship_type, COUNT(*) FROM relationships GROUP BY relationship_type
- Densest entities by relationship count

# GET /analytics/document-analytics
- SELECT source_type, COUNT(*) FROM documents GROUP BY source_type
- Calculate total size from metadata_json

# GET /analytics/user-analytics
- New table: user_sessions (user_id, login_timestamp, logout_timestamp)
- Active users (logged in today/week/month)
- New users in last 24h

# GET /analytics/performance-analytics
- New table: api_metrics (endpoint, response_time_ms, status_code, timestamp)
- Cache hit rates from api/cache.py
- Calculate p95, p99 response times
```

**New Database Tables**:
```sql
CREATE TABLE IF NOT EXISTS search_queries (
    id TEXT PRIMARY KEY,
    query_text TEXT NOT NULL,
    user_id TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    result_count INTEGER,
    response_time_ms FLOAT
);

CREATE TABLE IF NOT EXISTS user_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    login_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    logout_timestamp DATETIME,
    ip_address TEXT
);

CREATE TABLE IF NOT EXISTS api_metrics (
    id TEXT PRIMARY KEY,
    endpoint TEXT NOT NULL,
    method TEXT,
    response_time_ms FLOAT,
    status_code INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Implementation Strategy**:
1. Update `config/db_schema.sql` with new tables
2. Modify `storage/graph_db.py` with query methods for each metric
3. Add caching decorator to expensive queries (24h TTL)
4. Create `api/analytics_service.py` for aggregation logic

---

### Task 2: Export/Import Database Integration (2.5h)

**File**: `api/routes/export.py`

Connect export endpoints to actual data:

```python
# GET /export/entities/json
- Query all entities with their metadata
- Include related documents and relationships
- Return in D3/Cytoscape compatible format

# GET /export/entities/csv
- Use pandas to create CSV from entities
- Include mention_count, relationship_count, created_at

# GET /export/relationships/json
- Query all relationships with entity details
- Include source/target entity names and types

# GET /export/relationships/csv
- Format: source_id, source_name, relationship_type, target_id, target_name

# GET /export/citations/bibtex
- Query all citations from citations table
- Format each as BibTeX entry

# GET /export/graph/json
- Create nodes from entities with attributes
- Create edges from relationships
- Include graph statistics

# GET /export/graph/rdf
- Convert graph to RDF N-Triples format
- Subject: <entity_id>, Predicate: <relationship_type>, Object: <entity_id>

# GET /export/backup/full
- Serialize entire database to JSON
- Include all tables: entities, relationships, documents, citations, users
- Compress with gzip
- Return as file download (application/gzip)

# POST /export/import/entities
- Accept JSON with entities array
- Validate against existing entities (deduplication)
- Batch insert with conflict resolution
- Return import report (success count, failures, duplicates)

# POST /export/import/relationships
- Accept JSON with relationships array
- Validate entity references
- Batch insert relationships
- Handle reverse relationships

# POST /export/import/backup
- Accept gzip file
- Decompress and parse JSON
- Truncate existing data (or merge mode)
- Restore all tables
- Return restore report
```

**Implementation Strategy**:
1. Create `api/export_service.py` with serialization logic
2. Add file download support to FastAPI responses
3. Implement conflict resolution for imports
4. Add progress tracking for large exports/imports

---

### Task 3: Document Processing Enhancement (2h)

**File**: `api/routes/documents.py`

Enhance with real processing pipeline:

```python
# POST /documents/upload
- Accept multipart/form-data file upload
- Validate file type (PDF, DOCX, PPTX, MD, TXT, HTML)
- Store in ~/second-brain-data/documents/
- Extract metadata (filename, size, upload_time)
- Queue for processing
- Return document_id immediately

# POST /documents/process/{document_id}
- Trigger actual processing pipeline:
  1. Parse document using process/parse.py
  2. Extract text chunks
  3. Generate embeddings using process/embed.py
  4. Extract entities using process/extract_entities.py
  5. Link entities to document
  6. Store in graph database
- Return processing report (entities_found, chunks_created, embeddings_generated)

# GET /documents/list
- Query all documents from database
- Return with processing status (pending, processing, complete)
- Include upload time, file size, entity count

# GET /documents/{document_id}/text
- Return extracted text from database
- Include chunk boundaries for reference

# GET /documents/{document_id}/entities
- Return all entities extracted from document
- Include occurrence counts
```

**Implementation Strategy**:
1. Integrate with existing `process/parse.py`, `process/embed.py`, `process/extract_entities.py`
2. Add `DocumentProcessor` orchestration class
3. Implement async job queue for processing
4. Add progress endpoint for real-time status

---

### Task 4: Graph API Database Queries (2h)

**File**: `api/routes/graph.py`

Fix missing methods and implement real queries:

```python
# POST /graph/entity
- get_entity(entity_id) — return entity with all metadata
- Include: id, name, type, definition, mention_count
- Include: related_entities (relationships), documents (mentions)
- Include: citation_count, creation_timestamp

# POST /graph/traverse
- Traverse graph from entity with BFS
- Respect depth limit (1-5)
- Filter by relationship_type if provided
- Return: root_entity, nodes (with attributes), edges (with types)

# GET /viz/entity/{entity_id}
- Get entity visualization data
- Include: node properties (size, color by type)
- Include: connected entities and relationships
- Limit to depth 2 for performance

# POST /graph/search
- Search entities by name/definition
- Use FTS (full-text search) if enabled
- Return top matches with relevance scores
```

**Implementation Strategy**:
1. Add missing methods to `storage/graph_db.py` GraphDB class
2. Implement efficient graph traversal with depth limits
3. Add query caching with TTL for expensive operations
4. Use database indexes on frequently-queried columns

---

### Task 5: Caching & Performance Optimization (2.5h)

**File**: `api/cache.py` + route implementations

Enhance caching for Phase 4/5 endpoints:

```python
# Analytics endpoints — 1 hour TTL
- /analytics/overview
- /analytics/entity-types
- /analytics/search-analytics
- /analytics/relationship-analytics

# Export endpoints — 30 minutes TTL (data freshness important)
- /export/entities/json
- /export/relationships/json
- /export/graph/json

# Search results — 5 minutes TTL
- /search/ endpoints

# Entity detail — 30 minutes TTL (unless user edits)
- /graph/entity
- /viz/entity/*

# Implementation
- Add cache invalidation on:
  - Document upload completion
  - Entity creation/modification
  - Relationship creation
  - Citation creation
- Use pattern-based invalidation: `invalidate_pattern("analytics/*")`
- Add cache statistics endpoint: GET /metrics/cache-stats
```

---

## Part 2: Frontend Enhancement (Tasks 6-9)

### Task 6: Analytics Dashboard (3h)

**Files**: 
- `web/components/AnalyticsDashboard.tsx` (NEW)
- `web/components/AnalyticsCharts.tsx` (NEW)
- `web/pages/analytics.tsx` (NEW)

**Components**:

```typescript
// AnalyticsDashboard.tsx
- Main dashboard layout with tabs:
  - Overview (KPIs: entity count, relationships, documents, citations)
  - Entity Distribution (bar chart by type)
  - Search Analytics (line chart: searches over time, popular queries)
  - Relationship Network (d3 force-directed graph)
  - Citation Heatmap (matrix: most cited entities)
  - Document Processing (stacked area: documents by type)
  - User Activity (daily/weekly/monthly active users)
  - Performance (line: response times, cache hit rate)

// AnalyticsCharts.tsx
- Reusable chart components using recharts:
  - BarChart (entity types, document types)
  - LineChart (trends over time, performance metrics)
  - PieChart (format distribution)
  - HeatmapChart (entity citation matrix)

// pages/analytics.tsx
- Page wrapper with refresh button
- Real-time updates via WebSocket
- Export analytics as PDF/JSON
- Time range selector (last 7d, 30d, 90d, 1y)
```

**Dependencies**:
```json
{
  "recharts": "^2.10.0",
  "date-fns": "^2.30.0"
}
```

---

### Task 7: Export/Import UI (2h)

**Files**:
- `web/components/ExportImportPanel.tsx` (NEW)
- `web/pages/settings/export.tsx` (NEW)

**Components**:

```typescript
// ExportImportPanel.tsx
- Two-column layout: Export (left) | Import (right)

// Export section:
- Format selector: JSON, CSV, BibTeX, RDF
- Data type selector: Entities, Relationships, Citations, Full Graph, Complete Backup
- Export button → downloads file
- Shows file size before export
- Recent exports history

// Import section:
- File upload drop zone
- Format auto-detection
- Conflict resolution mode: Skip, Overwrite, Merge
- Progress indicator during import
- Import report (success count, failures, warnings)
- Rollback button if import fails

// pages/settings/export.tsx
- Page wrapper with tabs
- Backup scheduling (daily, weekly, monthly)
- Backup history with restore buttons
- Storage usage statistics
```

---

### Task 8: Search UI Enhancements (1.5h)

**Files**: `web/components/AdvancedSearchResults.tsx` (UPDATE)

**Enhancements**:

```typescript
// Add to AdvancedSearchResults:
- Filter sidebar:
  - Entity type multi-select
  - Date range picker
  - Source type filter
  - Mention count range slider

- Result options:
  - Save search as collection
  - Export results as CSV/JSON
  - Share search link

- Result rendering:
  - Entity type badge (colored)
  - Mention count badge
  - Last mentioned date
  - Quick entity preview on hover

- Faceted search UI:
  - Entity type facets with counts
  - Source type facets with counts
  - Dynamic facet update as filters change
```

---

### Task 9: Navigation & Settings (1h)

**Files**: 
- `web/components/Navigation.tsx` (UPDATE)
- `web/pages/settings.tsx` (NEW)

**Updates**:

```typescript
// Navigation.tsx
- Add menu items:
  - Dashboard (Analytics)
  - Export/Import
  - Settings

// pages/settings.tsx
- Settings tabs:
  - Account (profile, password, preferences)
  - Data Management (export, import, backup, storage)
  - Integrations (email, Slack, RSS — stubs for Phase 5+)
  - API Keys (for third-party access)
  - Performance (cache settings, query optimization)
  - About (version, documentation links)
```

---

## Part 3: Extensibility (Tasks 10-12)

### Task 10: Integration Framework (3h)

**Files**: 
- `api/integrations/base.py` (NEW)
- `api/integrations/email.py` (NEW)
- `api/integrations/slack.py` (NEW)
- `api/integrations/rss.py` (NEW)

**Implementation**:

```python
# api/integrations/base.py
class IntegrationBase:
    """Base class for all integrations."""
    
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get("enabled", False)
    
    async def authenticate(self):
        """Authenticate with external service."""
        pass
    
    async def ingest(self, data):
        """Ingest data from external service."""
        pass
    
    async def health_check(self):
        """Check integration status."""
        pass

# api/integrations/email.py
class EmailIntegration(IntegrationBase):
    """Gmail/IMAP integration."""
    
    # Features:
    # - Auto-import emails with labels (e.g., #second-brain)
    # - Extract entities from email bodies
    # - Create relationships from email threads
    # - Index email attachments
    
    async def ingest(self):
        # Connect to Gmail API
        # Query emails with label
        # Extract text and attachments
        # Run entity extraction
        # Link to knowledge graph

# api/integrations/slack.py
class SlackIntegration(IntegrationBase):
    """Slack workspace integration."""
    
    # Features:
    # - Subscribe to channels
    # - Auto-extract entities from messages
    # - Create entity collection from thread
    # - Mention entities in Slack (#entity:name)
    
    async def ingest(self):
        # Connect to Slack API
        # Stream channel messages
        # Extract entities from text
        # Create documents from message threads

# api/integrations/rss.py
class RSSIntegration(IntegrationBase):
    """RSS feed integration."""
    
    # Features:
    # - Subscribe to multiple feeds
    # - Auto-ingest articles
    # - Extract key entities per article
    # - Track mention trends over time
    
    async def ingest(self):
        # Parse RSS feeds
        # Extract article content
        # Run entity extraction
        # Store as documents with source tracking
```

**Database Schema Updates**:
```sql
CREATE TABLE IF NOT EXISTS integrations (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL (email, slack, rss, custom),
    name TEXT NOT NULL,
    config_json TEXT,
    enabled BOOLEAN DEFAULT 0,
    last_sync DATETIME,
    sync_interval_minutes INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id TEXT PRIMARY KEY,
    integration_id TEXT,
    status TEXT (pending, running, complete, failed),
    documents_imported INTEGER,
    entities_created INTEGER,
    started_at DATETIME,
    completed_at DATETIME,
    error_message TEXT,
    FOREIGN KEY (integration_id) REFERENCES integrations(id)
);
```

---

### Task 11: Plugin Framework (2.5h)

**Files**:
- `api/plugins/base.py` (NEW)
- `api/plugins/loader.py` (NEW)
- `api/routes/plugins.py` (NEW)

**Implementation**:

```python
# api/plugins/base.py
class SecondBrainPlugin:
    """Base class for all plugins."""
    
    name: str
    version: str
    description: str
    
    def __init__(self, app):
        self.app = app
    
    async def on_load(self):
        """Called when plugin is loaded."""
        pass
    
    async def on_entity_created(self, entity):
        """Hook: entity created."""
        pass
    
    async def on_document_ingested(self, document):
        """Hook: document ingested."""
        pass
    
    async def register_routes(self):
        """Register custom API routes."""
        pass

# api/plugins/loader.py
class PluginManager:
    """Manages plugin lifecycle."""
    
    def load_plugins(self, plugin_dir: str):
        # Dynamically import plugins from directory
        # Validate plugin structure
        # Call on_load() for each plugin
    
    def register_hooks(self):
        # Register plugin hooks in event system
    
    def list_plugins(self):
        # Return list of loaded plugins
    
    def enable_plugin(self, plugin_name: str):
        # Enable plugin at runtime
    
    def disable_plugin(self, plugin_name: str):
        # Disable plugin at runtime

# api/routes/plugins.py
@router.get("/plugins")
def list_plugins():
    """List all loaded plugins."""
    return PluginManager.list_plugins()

@router.post("/plugins/{plugin_name}/enable")
def enable_plugin(plugin_name: str):
    """Enable a plugin."""
    return PluginManager.enable_plugin(plugin_name)

@router.post("/plugins/{plugin_name}/disable")
def disable_plugin(plugin_name: str):
    """Disable a plugin."""
    return PluginManager.disable_plugin(plugin_name)
```

**Plugin Examples** (as stubs in `plugins/examples/`):
- `plugins/examples/twitter_monitor.py` — Track mentions
- `plugins/examples/hacker_news.py` — Subscribe to HN stories
- `plugins/examples/webhook_receiver.py` — Accept webhooks from external apps

---

### Task 12: Progressive Web App (PWA) Mobile Support (2h)

**Files**:
- `web/public/manifest.json` (UPDATE)
- `web/public/service-worker.js` (NEW)
- `web/next.config.js` (UPDATE)

**Implementation**:

```typescript
// public/manifest.json
{
  "name": "Second Brain",
  "short_name": "Brain",
  "description": "Personal Knowledge Management System",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#000000",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ],
  "screenshots": [
    {
      "src": "/screenshot-1.png",
      "sizes": "540x720",
      "type": "image/png",
      "form_factor": "narrow"
    }
  ]
}

// public/service-worker.js
// Cache strategy: Network-first for API, Cache-first for assets
// Offline support: Cache search results, entities, documents
// Background sync: Queue document uploads for when online
// Push notifications: Real-time updates when entities mentioned

// next.config.js
// Enable PWA: next-pwa plugin
// Enable offline: Cache entire app shell
// Icons: Multiple sizes for different devices
```

**Mobile-Optimized Components**:
- Responsive layouts for small screens
- Touch-friendly buttons (48px minimum)
- Mobile-optimized D3 graph (lower LOD at small screens)
- Mobile navigation drawer instead of sidebar
- Swipe gestures for navigation

---

## Implementation Roadmap

### Week 1: Backend Integration
- **Day 1**: Task 1 (Analytics queries) + Task 5 (Caching)
- **Day 2**: Task 2 (Export/Import) + Task 3 (Documents)
- **Day 3**: Task 4 (Graph API) + Testing

### Week 2: Frontend & Extensibility
- **Day 1**: Task 6 (Analytics Dashboard) + Task 9 (Settings)
- **Day 2**: Task 7 (Export/Import UI) + Task 8 (Search UI)
- **Day 3**: Task 10 (Integrations) + Task 11 (Plugins)
- **Day 4**: Task 12 (PWA/Mobile) + Integration testing

### Week 3: Refinement & Launch
- **Day 1-2**: End-to-end testing
- **Day 3**: Performance optimization
- **Day 4**: Documentation & final commit

---

## Testing Strategy

### Backend Testing (Unit + Integration)
```bash
# Tests to create:
tests/test_analytics_queries.py
tests/test_export_service.py
tests/test_document_processor.py
tests/test_graph_queries.py
tests/test_integrations.py
tests/test_plugin_system.py

# Run all:
python3 -m pytest tests/ -v --cov=api --cov=storage --cov=process
```

### Frontend Testing
```bash
# Component tests:
npm run test

# E2E tests:
npm run test:e2e

# Performance:
npm run test:lighthouse
```

---

## Database Schema Changes

Add these tables to `config/db_schema.sql`:

```sql
-- Metrics tables
CREATE TABLE IF NOT EXISTS search_queries (
    id TEXT PRIMARY KEY,
    query_text TEXT NOT NULL,
    user_id TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    result_count INTEGER,
    response_time_ms FLOAT
);

CREATE TABLE IF NOT EXISTS user_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    login_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    logout_timestamp DATETIME,
    ip_address TEXT
);

CREATE TABLE IF NOT EXISTS api_metrics (
    id TEXT PRIMARY KEY,
    endpoint TEXT NOT NULL,
    method TEXT,
    response_time_ms FLOAT,
    status_code INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Integration tables
CREATE TABLE IF NOT EXISTS integrations (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    config_json TEXT,
    enabled BOOLEAN DEFAULT 0,
    last_sync DATETIME,
    sync_interval_minutes INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id TEXT PRIMARY KEY,
    integration_id TEXT,
    status TEXT,
    documents_imported INTEGER,
    entities_created INTEGER,
    started_at DATETIME,
    completed_at DATETIME,
    error_message TEXT,
    FOREIGN KEY (integration_id) REFERENCES integrations(id)
);

-- Backup/version tables
CREATE TABLE IF NOT EXISTS backups (
    id TEXT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    size_bytes INTEGER,
    compression TEXT,
    status TEXT
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_search_queries_timestamp ON search_queries(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_metrics_endpoint ON api_metrics(endpoint);
CREATE INDEX IF NOT EXISTS idx_integrations_type ON integrations(type);
```

---

## Configuration Files

Create `config/phase5.config.json`:

```json
{
  "analytics": {
    "cache_ttl_seconds": 3600,
    "aggregation_interval_hours": 1,
    "retention_days": 90
  },
  "integrations": {
    "email": {
      "enabled": false,
      "provider": "gmail",
      "sync_interval_minutes": 60
    },
    "slack": {
      "enabled": false,
      "sync_interval_minutes": 30
    },
    "rss": {
      "enabled": false,
      "sync_interval_minutes": 120
    }
  },
  "plugins": {
    "enabled": true,
    "plugin_directory": "./plugins",
    "auto_load": true
  },
  "pwa": {
    "enabled": true,
    "offline_support": true,
    "cache_strategy": "network-first"
  }
}
```

---

## Resumption Checklist for Windows GPU Machine

When resuming Phase 5 on your Windows machine, use this checklist:

- [ ] Clone latest repo: `git clone https://github.com/sriramshiv26-prog/second-brain.git`
- [ ] Read this document fully
- [ ] Verify Python 3.10+ installed
- [ ] Setup venv: `python -m venv venv && venv\Scripts\activate`
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Verify Ollama running: `ollama serve` (in separate terminal)
- [ ] Run Phase 4 tests: `pytest tests/ -v` (verify baseline)
- [ ] Start with Task 1 (Analytics Database Queries)
- [ ] Commit changes incrementally with clear messages
- [ ] Push to GitHub regularly
- [ ] Update memory files with progress

---

## Quick Start for Next Session

```bash
# Setup on Windows GPU machine
cd second-brain
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Run existing tests to verify baseline
python -m pytest tests/ -v

# Start Phase 5 Task 1
# See "Task 1: Analytics Database Queries" section above

# After each task, commit:
git add .
git commit -m "Phase 5 Task X: [description]"
git push origin main

# Update progress in memory before switching machines
```

---

## Cost Analysis (Task Cost Optimization)

**Backend Integration**: 
- Local Ollama: $0
- Database work: $0
- Estimated: 8-12 hours

**Frontend Development**:
- React components: $0 (local)
- Recharts charting: $0 (open source)
- Estimated: 6-8 hours

**Extensibility**:
- Plugin framework: $0 (local)
- Integration stubs: $0 (local)
- PWA support: $0 (local)
- Estimated: 8-12 hours

**Strategic Claude Usage** (optional):
- Architecture decisions: 2-3 Sonnet calls (~$0.20)
- Complex bug debugging: 2-3 Sonnet calls (~$0.20)
- Performance optimization: 1-2 Sonnet calls (~$0.10)
- **Total optional cost**: <$1

**Total Phase 5 Cost**: $0-$1 (all local work)

---

## Success Metrics

Phase 5 is complete when:
- [x] All 5 backend tasks implemented and tested
- [x] All 4 frontend tasks implemented and tested
- [x] All 3 extensibility tasks implemented (as stubs)
- [x] All tests passing (76+ from Phase 4 + new Phase 5 tests)
- [x] Web build successful
- [x] API starts without errors (60+ endpoints)
- [x] Documentation complete
- [x] All changes committed and pushed
- [x] Memory files updated

---

**Start Date**: [To be filled when resuming]  
**Completion Target**: 24-32 hours  
**Expected Completion**: [To be calculated based on start date]

Remember: This is a comprehensive guide — refer back to specific task sections as you work. Each task is self-contained but builds on previous ones.

# Phase 5: Detailed Task Breakdown with Code Structure

This document provides specific implementation details for each Phase 5 task, including file locations, code structure, and exact modifications needed.

---

## Task 1: Analytics Database Queries (3h)

### Files to Modify/Create

**Modify**: `storage/graph_db.py`
**Create**: `api/analytics_service.py`
**Modify**: `config/db_schema.sql`

### Step 1.1: Add New Database Tables

**File**: `config/db_schema.sql` (APPEND)

```sql
-- Search analytics
CREATE TABLE IF NOT EXISTS search_queries (
    id TEXT PRIMARY KEY,
    query_text TEXT NOT NULL,
    user_id TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    result_count INTEGER,
    response_time_ms FLOAT
);
CREATE INDEX IF NOT EXISTS idx_search_queries_timestamp ON search_queries(timestamp);

-- User sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    login_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    logout_timestamp DATETIME,
    ip_address TEXT
);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);

-- API metrics
CREATE TABLE IF NOT EXISTS api_metrics (
    id TEXT PRIMARY KEY,
    endpoint TEXT NOT NULL,
    method TEXT,
    response_time_ms FLOAT,
    status_code INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_api_metrics_endpoint ON api_metrics(endpoint);
```

### Step 1.2: Add Query Methods to GraphDB

**File**: `storage/graph_db.py` (ADD to class)

```python
def get_entity_count(self) -> int:
    cursor = self.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM entities")
    return cursor.fetchone()[0]

def get_relationship_count(self) -> int:
    cursor = self.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM relationships")
    return cursor.fetchone()[0]

def get_document_count(self) -> int:
    cursor = self.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM documents")
    return cursor.fetchone()[0]

def get_citation_count(self) -> int:
    cursor = self.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM citations")
    return cursor.fetchone()[0]

def get_avg_entity_mention_count(self) -> float:
    cursor = self.conn.cursor()
    cursor.execute("SELECT AVG(mention_count) FROM entities")
    result = cursor.fetchone()[0]
    return result or 0.0

def get_entity_type_distribution(self) -> dict:
    cursor = self.conn.cursor()
    cursor.execute("SELECT type, COUNT(*) as count FROM entities GROUP BY type")
    return {row[0]: row[1] for row in cursor.fetchall()}

def get_relationship_type_distribution(self) -> dict:
    cursor = self.conn.cursor()
    cursor.execute("SELECT relationship_type, COUNT(*) as count FROM relationships GROUP BY relationship_type")
    return {row[0]: row[1] for row in cursor.fetchall()}

def get_document_type_distribution(self) -> dict:
    cursor = self.conn.cursor()
    cursor.execute("SELECT source_type, COUNT(*) as count FROM documents GROUP BY source_type")
    return {row[0]: row[1] for row in cursor.fetchall()}

def log_search_query(self, query_text: str, result_count: int, response_time_ms: float, user_id: str = None):
    cursor = self.conn.cursor()
    query_id = f"sq_{uuid.uuid4().hex[:12]}"
    cursor.execute(
        """INSERT INTO search_queries (id, query_text, user_id, result_count, response_time_ms)
           VALUES (?, ?, ?, ?, ?)""",
        (query_id, query_text, user_id, result_count, response_time_ms)
    )
    self.conn.commit()

def get_popular_searches(self, limit: int = 10, days: int = 30) -> list:
    cursor = self.conn.cursor()
    cursor.execute(
        """SELECT query_text, COUNT(*) as count
           FROM search_queries
           WHERE timestamp > datetime('now', '-' || ? || ' days')
           GROUP BY query_text
           ORDER BY count DESC
           LIMIT ?""",
        (days, limit)
    )
    return [{"query": row[0], "count": row[1]} for row in cursor.fetchall()]

def get_avg_search_response_time(self) -> float:
    cursor = self.conn.cursor()
    cursor.execute("SELECT AVG(response_time_ms) FROM search_queries")
    result = cursor.fetchone()[0]
    return result or 0.0

def get_most_cited_entities(self, limit: int = 10) -> list:
    cursor = self.conn.cursor()
    cursor.execute(
        """SELECT e.id, e.name, COUNT(c.id) as citation_count
           FROM entities e
           LEFT JOIN citations c ON e.id = c.entity_id
           GROUP BY e.id
           ORDER BY citation_count DESC
           LIMIT ?""",
        (limit,)
    )
    return [{"entity_id": row[0], "name": row[1], "citations": row[2]} for row in cursor.fetchall()]

def get_densest_entities(self, limit: int = 10) -> list:
    cursor = self.conn.cursor()
    cursor.execute(
        """SELECT e.id, e.name, COUNT(r.id) as relationship_count
           FROM entities e
           LEFT JOIN relationships r ON (e.id = r.source_entity_id OR e.id = r.target_entity_id)
           GROUP BY e.id
           ORDER BY relationship_count DESC
           LIMIT ?""",
        (limit,)
    )
    return [{"entity_id": row[0], "name": row[1], "relationship_count": row[2]} for row in cursor.fetchall()]

def log_api_metric(self, endpoint: str, method: str, response_time_ms: float, status_code: int):
    cursor = self.conn.cursor()
    metric_id = f"m_{uuid.uuid4().hex[:12]}"
    cursor.execute(
        """INSERT INTO api_metrics (id, endpoint, method, response_time_ms, status_code)
           VALUES (?, ?, ?, ?, ?)""",
        (metric_id, endpoint, method, response_time_ms, status_code)
    )
    self.conn.commit()

def get_endpoint_performance(self, endpoint: str) -> dict:
    cursor = self.conn.cursor()
    cursor.execute(
        """SELECT 
           AVG(response_time_ms) as avg_ms,
           COUNT(*) as calls,
           MIN(response_time_ms) as min_ms,
           MAX(response_time_ms) as max_ms
           FROM api_metrics
           WHERE endpoint = ?""",
        (endpoint,)
    )
    row = cursor.fetchone()
    return {
        "avg_ms": row[0] or 0.0,
        "calls": row[1] or 0,
        "min_ms": row[2] or 0.0,
        "max_ms": row[3] or 0.0
    }

def get_cache_hit_rate(self) -> float:
    # This will be called from api/cache.py stats
    # Placeholder: returns from cache statistics
    return 0.75  # Update after cache integration
```

### Step 1.3: Create Analytics Service

**File**: `api/analytics_service.py` (NEW)

```python
"""Analytics aggregation and computation service."""

from datetime import datetime, timedelta
from typing import Dict, Any, List
from storage.graph_db import GraphDB, get_graph_db
from api.cache import cache, invalidate_pattern

class AnalyticsService:
    """Aggregates analytics from database."""
    
    def __init__(self):
        self.db = GraphDB(get_graph_db())
    
    @cache(ttl=3600)  # Cache 1 hour
    def get_overview(self) -> Dict[str, Any]:
        """Get overall knowledge base statistics."""
        return {
            "total_entities": self.db.get_entity_count(),
            "total_relationships": self.db.get_relationship_count(),
            "total_documents": self.db.get_document_count(),
            "total_citations": self.db.get_citation_count(),
            "average_entity_mention_count": self.db.get_avg_entity_mention_count(),
        }
    
    @cache(ttl=3600)
    def get_entity_distribution(self) -> Dict[str, int]:
        """Get distribution of entity types."""
        return self.db.get_entity_type_distribution()
    
    @cache(ttl=300)  # Cache 5 minutes for fresher data
    def get_search_analytics(self) -> Dict[str, Any]:
        """Get search query analytics."""
        return {
            "total_searches": self._get_total_searches(),
            "avg_results_per_search": self._get_avg_results(),
            "avg_response_time_ms": self.db.get_avg_search_response_time(),
            "popular_queries": self.db.get_popular_searches(limit=10, days=30),
        }
    
    @cache(ttl=3600)
    def get_citation_analytics(self) -> Dict[str, Any]:
        """Get citation statistics."""
        return {
            "total_citations": self.db.get_citation_count(),
            "most_cited_entities": self.db.get_most_cited_entities(limit=10),
        }
    
    @cache(ttl=3600)
    def get_relationship_analytics(self) -> Dict[str, Any]:
        """Get relationship distribution."""
        distribution = self.db.get_relationship_type_distribution()
        densest = self.db.get_densest_entities(limit=10)
        
        return {
            "total_relationships": self.db.get_relationship_count(),
            "by_type": distribution,
            "densest_entities": densest,
        }
    
    def log_search_query(self, query_text: str, result_count: int, response_time_ms: float):
        """Log a search query for analytics."""
        self.db.log_search_query(query_text, result_count, response_time_ms)
        # Invalidate related cache
        invalidate_pattern("analytics/search*")
    
    def log_api_metric(self, endpoint: str, method: str, response_time_ms: float, status_code: int):
        """Log API metric for performance tracking."""
        self.db.log_api_metric(endpoint, method, response_time_ms, status_code)
    
    def _get_total_searches(self) -> int:
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM search_queries")
        return cursor.fetchone()[0]
    
    def _get_avg_results(self) -> float:
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT AVG(result_count) FROM search_queries")
        result = cursor.fetchone()[0]
        return result or 0.0

# Singleton instance
_analytics_service = None

def get_analytics_service() -> AnalyticsService:
    """Get or create analytics service."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service
```

### Step 1.4: Update Analytics Routes

**File**: `api/routes/analytics.py` (REPLACE endpoints)

```python
"""Analytics endpoints for knowledge base insights."""

from datetime import datetime
from fastapi import APIRouter
from api.analytics_service import get_analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])
analytics = get_analytics_service()

@router.get("/overview")
def get_analytics_overview():
    """Get overall knowledge base statistics."""
    data = analytics.get_overview()
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": data,
    }

@router.get("/entity-types")
def get_entity_type_distribution():
    """Get distribution of entity types."""
    distribution = analytics.get_entity_distribution()
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "distribution": distribution,
        "total": sum(distribution.values()),
    }

@router.get("/search-analytics")
def get_search_analytics():
    """Get search query analytics."""
    data = analytics.get_search_analytics()
    return {
        "timestamp": datetime.utcnow().isoformat(),
        **data,
    }

@router.get("/citation-analytics")
def get_citation_analytics():
    """Get citation statistics."""
    data = analytics.get_citation_analytics()
    return {
        "timestamp": datetime.utcnow().isoformat(),
        **data,
    }

@router.get("/relationship-analytics")
def get_relationship_analytics():
    """Get relationship distribution."""
    data = analytics.get_relationship_analytics()
    return {
        "timestamp": datetime.utcnow().isoformat(),
        **data,
    }

# ... rest of endpoints follow similar pattern
```

### Step 1.5: Testing

**Create**: `tests/test_analytics_service.py`

```python
import pytest
from api.analytics_service import get_analytics_service
from storage.graph_db import GraphDB, get_graph_db

def test_get_overview():
    service = get_analytics_service()
    overview = service.get_overview()
    assert "total_entities" in overview
    assert "total_relationships" in overview

def test_get_entity_distribution():
    service = get_analytics_service()
    dist = service.get_entity_distribution()
    assert isinstance(dist, dict)

def test_log_search_query():
    db = GraphDB(get_graph_db())
    db.log_search_query("test query", 5, 123.45)
    # Verify it was logged
    popular = db.get_popular_searches(limit=1)
    assert any(q["query"] == "test query" for q in popular)
```

---

## Task 2: Export/Import Database Integration (2.5h)

### Files to Create

**Create**: `api/export_service.py`
**Modify**: `api/routes/export.py`

### Step 2.1: Create Export Service

**File**: `api/export_service.py` (NEW)

```python
"""Export/Import service for data portability."""

import json
import csv
import gzip
from io import StringIO, BytesIO
from typing import Dict, List, Any
from datetime import datetime
from storage.graph_db import GraphDB, get_graph_db
from api.cache import cache
import uuid

class ExportService:
    """Handles all export/import operations."""
    
    def __init__(self):
        self.db = GraphDB(get_graph_db())
    
    @cache(ttl=1800)  # 30 minutes
    def export_entities_json(self) -> Dict[str, Any]:
        """Export all entities as JSON."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id, name, type, definition, mention_count, created_at
            FROM entities
        """)
        
        entities = []
        for row in cursor.fetchall():
            entities.append({
                "id": row[0],
                "name": row[1],
                "type": row[2],
                "definition": row[3],
                "mention_count": row[4],
                "created_at": row[5],
            })
        
        return {
            "entities": entities,
            "total": len(entities),
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def export_entities_csv(self) -> str:
        """Export all entities as CSV."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id, name, type, definition, mention_count, created_at
            FROM entities
        """)
        
        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["id", "name", "type", "definition", "mention_count", "created_at"])
        
        for row in cursor.fetchall():
            writer.writerow(row)
        
        return csv_buffer.getvalue()
    
    @cache(ttl=1800)
    def export_relationships_json(self) -> Dict[str, Any]:
        """Export all relationships as JSON."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT r.id, r.source_entity_id, e1.name, r.relationship_type, 
                   r.target_entity_id, e2.name, r.confidence
            FROM relationships r
            JOIN entities e1 ON r.source_entity_id = e1.id
            JOIN entities e2 ON r.target_entity_id = e2.id
        """)
        
        relationships = []
        for row in cursor.fetchall():
            relationships.append({
                "id": row[0],
                "source_id": row[1],
                "source_name": row[2],
                "type": row[3],
                "target_id": row[4],
                "target_name": row[5],
                "confidence": row[6],
            })
        
        return {
            "relationships": relationships,
            "total": len(relationships),
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    @cache(ttl=1800)
    def export_graph_json(self) -> Dict[str, Any]:
        """Export knowledge graph as JSON (D3/Cytoscape compatible)."""
        # Nodes
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id, name, type, mention_count, definition
            FROM entities
        """)
        
        nodes = []
        for row in cursor.fetchall():
            nodes.append({
                "id": row[0],
                "label": row[1],
                "type": row[2],
                "value": row[3],
                "title": row[4],
            })
        
        # Edges
        cursor.execute("""
            SELECT source_entity_id, target_entity_id, relationship_type, confidence
            FROM relationships
        """)
        
        edges = []
        for row in cursor.fetchall():
            edges.append({
                "source": row[0],
                "target": row[1],
                "label": row[2],
                "weight": row[3],
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    @cache(ttl=1800)
    def export_backup_full(self) -> bytes:
        """Export full knowledge base as gzipped JSON."""
        backup_data = {
            "version": "1.0",
            "timestamp": datetime.utcnow().isoformat(),
            "entities": self.export_entities_json()["entities"],
            "relationships": self.export_relationships_json()["relationships"],
            "documents": self._export_documents(),
            "citations": self._export_citations(),
        }
        
        # Compress
        json_bytes = json.dumps(backup_data, indent=2).encode('utf-8')
        buffer = BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode='wb') as gz:
            gz.write(json_bytes)
        
        return buffer.getvalue()
    
    def import_entities(self, entities: List[Dict]) -> Dict[str, Any]:
        """Import entities from JSON data."""
        imported = 0
        duplicates = 0
        failures = 0
        
        cursor = self.db.conn.cursor()
        
        for entity in entities:
            try:
                # Check if exists
                cursor.execute(
                    "SELECT id FROM entities WHERE LOWER(name) = LOWER(?)",
                    (entity["name"],)
                )
                
                if cursor.fetchone():
                    duplicates += 1
                    continue
                
                # Insert
                entity_id = f"ent_{uuid.uuid4().hex[:12]}"
                cursor.execute(
                    """INSERT INTO entities (id, name, type, definition)
                       VALUES (?, ?, ?, ?)""",
                    (entity_id, entity["name"], entity.get("type", "Unknown"), 
                     entity.get("definition"))
                )
                imported += 1
            except Exception as e:
                failures += 1
        
        self.db.conn.commit()
        
        return {
            "status": "success",
            "imported_count": imported,
            "duplicate_count": duplicates,
            "failed_count": failures,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def _export_documents(self) -> List[Dict]:
        """Helper to export documents."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id, source_type, source_path, title, created_at
            FROM documents
        """)
        
        return [
            {
                "id": row[0],
                "source_type": row[1],
                "source_path": row[2],
                "title": row[3],
                "created_at": row[4],
            }
            for row in cursor.fetchall()
        ]
    
    def _export_citations(self) -> List[Dict]:
        """Helper to export citations."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id, entity_id, metadata_json, format, created_at
            FROM citations
        """)
        
        return [
            {
                "id": row[0],
                "entity_id": row[1],
                "metadata": json.loads(row[2]) if row[2] else {},
                "format": row[3],
                "created_at": row[4],
            }
            for row in cursor.fetchall()
        ]

def get_export_service() -> ExportService:
    """Get or create export service."""
    return ExportService()
```

### Step 2.2: Update Export Routes

**File**: `api/routes/export.py` (UPDATE)

```python
"""Data export endpoints."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import io

from api.export_service import get_export_service

router = APIRouter(prefix="/export", tags=["export"])

@router.get("/entities/json")
def export_entities_json():
    """Export all entities as JSON."""
    service = get_export_service()
    data = service.export_entities_json()
    return data

@router.get("/entities/csv")
def export_entities_csv():
    """Export all entities as CSV."""
    service = get_export_service()
    csv_content = service.export_entities_csv()
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=entities.csv"}
    )

@router.get("/relationships/json")
def export_relationships_json():
    """Export all relationships as JSON."""
    service = get_export_service()
    return service.export_relationships_json()

@router.get("/graph/json")
def export_graph_json():
    """Export knowledge graph as JSON."""
    service = get_export_service()
    return service.export_graph_json()

@router.get("/backup/full")
def create_full_backup():
    """Create full knowledge base backup."""
    service = get_export_service()
    backup_bytes = service.export_backup_full()
    
    return StreamingResponse(
        io.BytesIO(backup_bytes),
        media_type="application/gzip",
        headers={"Content-Disposition": "attachment; filename=knowledge_base_backup.json.gz"}
    )

@router.post("/import/entities")
def import_entities(data: dict):
    """Import entities from JSON."""
    service = get_export_service()
    try:
        result = service.import_entities(data.get("entities", []))
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Step 2.3: Testing

**Create**: `tests/test_export_service.py`

```python
import pytest
from api.export_service import get_export_service
from storage.graph_db import GraphDB, get_graph_db

def test_export_entities_json():
    service = get_export_service()
    result = service.export_entities_json()
    assert "entities" in result
    assert "total" in result
    assert isinstance(result["entities"], list)

def test_export_graph_json():
    service = get_export_service()
    result = service.export_graph_json()
    assert "nodes" in result
    assert "edges" in result

def test_import_entities():
    service = get_export_service()
    test_entities = [
        {"name": "Test Entity 1", "type": "Person"},
        {"name": "Test Entity 2", "type": "Organization"},
    ]
    result = service.import_entities(test_entities)
    assert result["status"] == "success"
    assert result["imported_count"] >= 0
```

---

## Task 3: Document Processing Enhancement (2h)

### Files to Modify/Create

**Modify**: `api/routes/documents.py`
**Create**: `api/document_processor.py`

### Step 3.1: Create Document Processor

**File**: `api/document_processor.py` (NEW)

```python
"""Document processing orchestration."""

import asyncio
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from storage.graph_db import GraphDB, get_graph_db
from process.parse import DocumentParser
from process.embed import EmbeddingPipeline
from process.extract_entities import EntityExtractor

class DocumentProcessor:
    """Orchestrates document processing pipeline."""
    
    def __init__(self):
        self.db = GraphDB(get_graph_db())
        self.parser = DocumentParser()
        self.embedder = EmbeddingPipeline()
        self.entity_extractor = EntityExtractor()
    
    async def process_document(self, file_path: str, document_id: str) -> Dict[str, Any]:
        """Process a document through the full pipeline."""
        
        try:
            # 1. Parse document
            text = await asyncio.to_thread(self.parser.parse_file, file_path)
            
            # 2. Chunk text
            chunks = self.parser.chunk_text(text, chunk_size=500, overlap=50)
            
            # 3. Generate embeddings
            embeddings = await asyncio.to_thread(
                self.embedder.embed_batch,
                chunks
            )
            
            # 4. Extract entities
            entities = []
            for chunk in chunks:
                chunk_entities = await asyncio.to_thread(
                    self.entity_extractor.extract,
                    chunk
                )
                entities.extend(chunk_entities)
            
            # 5. Deduplicate entities
            unique_entities = self._deduplicate_entities(entities)
            
            # 6. Link to database
            entity_ids = []
            for entity in unique_entities:
                entity_id = self.db.add_or_get_entity(
                    name=entity["name"],
                    entity_type=entity["type"],
                    definition=entity.get("definition")
                )
                entity_ids.append(entity_id)
            
            # 7. Link document to entities
            self.db.link_document_to_entities(document_id, entity_ids)
            
            # Update document status
            cursor = self.db.conn.cursor()
            cursor.execute(
                """UPDATE documents SET status = 'complete', processed_at = ? 
                   WHERE id = ?""",
                (datetime.utcnow().isoformat(), document_id)
            )
            self.db.conn.commit()
            
            return {
                "status": "complete",
                "document_id": document_id,
                "chunks_created": len(chunks),
                "embeddings_generated": len(embeddings),
                "entities_found": len(unique_entities),
                "unique_entities": len(set(e["name"] for e in unique_entities)),
            }
        
        except Exception as e:
            # Update status to failed
            cursor = self.db.conn.cursor()
            cursor.execute(
                """UPDATE documents SET status = 'failed', error = ? WHERE id = ?""",
                (str(e), document_id)
            )
            self.db.conn.commit()
            
            raise
    
    def _deduplicate_entities(self, entities: list) -> list:
        """Remove duplicate entities by name."""
        seen = {}
        for entity in entities:
            key = entity["name"].lower()
            if key not in seen:
                seen[key] = entity
        return list(seen.values())

def get_document_processor() -> DocumentProcessor:
    """Get document processor instance."""
    return DocumentProcessor()
```

### Step 3.2: Update Document Routes

**File**: `api/routes/documents.py` (UPDATE)

```python
"""Document management endpoints."""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pathlib import Path
import os
from storage.graph_db import GraphDB, get_graph_db
from api.document_processor import get_document_processor
import uuid
from datetime import datetime

router = APIRouter(prefix="/documents", tags=["documents"])
processor = get_document_processor()

UPLOAD_DIR = Path.home() / "second-brain-data" / "documents"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload")
async def upload_document(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Upload a document for processing."""
    
    # Validate file type
    valid_types = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/vnd.ms-powerpoint": "ppt",
        "text/markdown": "md",
        "text/plain": "txt",
        "text/html": "html",
    }
    
    if file.content_type not in valid_types:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    # Save file
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    file_ext = valid_types[file.content_type]
    file_path = UPLOAD_DIR / f"{doc_id}.{file_ext}"
    
    contents = await file.read()
    file_path.write_bytes(contents)
    
    # Store in database
    db = GraphDB(get_graph_db())
    db.add_document(
        doc_id=doc_id,
        source_type=file_ext,
        source_path=str(file_path),
        title=file.filename,
        content_hash=_hash_content(contents),
    )
    
    # Queue processing
    if background_tasks:
        background_tasks.add_task(processor.process_document, str(file_path), doc_id)
    
    return {
        "id": doc_id,
        "filename": file.filename,
        "size": len(contents),
        "status": "queued",
        "uploaded_at": datetime.utcnow().isoformat(),
    }

@router.post("/process/{document_id}")
async def process_document(document_id: str):
    """Trigger processing of a document."""
    
    db = GraphDB(get_graph_db())
    cursor = db.conn.cursor()
    cursor.execute("SELECT source_path FROM documents WHERE id = ?", (document_id,))
    
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = result[0]
    
    try:
        # Update status to processing
        cursor.execute(
            "UPDATE documents SET status = 'processing' WHERE id = ?",
            (document_id,)
        )
        db.conn.commit()
        
        # Process
        result = await processor.process_document(file_path, document_id)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
def list_documents():
    """List all documents."""
    db = GraphDB(get_graph_db())
    cursor = db.conn.cursor()
    cursor.execute(
        """SELECT id, title, source_type, size_bytes, status, uploaded_at 
           FROM documents ORDER BY uploaded_at DESC"""
    )
    
    documents = [
        {
            "id": row[0],
            "title": row[1],
            "type": row[2],
            "size": row[3],
            "status": row[4],
            "uploaded_at": row[5],
        }
        for row in cursor.fetchall()
    ]
    
    return {
        "documents": documents,
        "total": len(documents),
    }

@router.get("/{document_id}/text")
def get_document_text(document_id: str):
    """Get extracted text from a document."""
    
    db = GraphDB(get_graph_db())
    cursor = db.conn.cursor()
    cursor.execute("SELECT extracted_text FROM documents WHERE id = ?", (document_id,))
    
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "document_id": document_id,
        "text": result[0] or "",
    }

def _hash_content(content: bytes) -> str:
    """Create hash of content."""
    import hashlib
    return hashlib.sha256(content).hexdigest()
```

---

## Phase 5 Quick Reference

| Task | Hours | Files | Key Classes |
|------|-------|-------|-------------|
| 1. Analytics Queries | 3 | storage/graph_db.py, api/analytics_service.py, api/routes/analytics.py | AnalyticsService |
| 2. Export/Import | 2.5 | api/export_service.py, api/routes/export.py | ExportService |
| 3. Document Processing | 2 | api/document_processor.py, api/routes/documents.py | DocumentProcessor |
| 4. Graph API | 2 | storage/graph_db.py, api/routes/graph.py | GraphDB (extend) |
| 5. Caching | 2.5 | api/cache.py, route implementations | CacheManager |
| **Backend Total** | **12** | **10 files** | **5 services** |

---

Continue to PHASE_5_DETAILED_ROADMAP.md for Parts 2 and 3 (Frontend and Extensibility).


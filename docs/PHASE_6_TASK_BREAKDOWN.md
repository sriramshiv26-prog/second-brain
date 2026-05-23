# Phase 6: Detailed Task Breakdown

Complete implementation guide for AI-powered knowledge synthesis.

---

## Task 1: Markdown Wiki Layer (8 hours)

### 1.1: Database Schema

**File**: `config/db_schema.sql` (APPEND)

```sql
-- Wiki pages (markdown files)
CREATE TABLE IF NOT EXISTS wiki_pages (
    id TEXT PRIMARY KEY,
    entity_id TEXT,
    topic TEXT NOT NULL,
    content TEXT,
    version INTEGER DEFAULT 1,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by TEXT DEFAULT 'system',
    change_log TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entity_id) REFERENCES entities(id)
);

-- Wiki links between pages
CREATE TABLE IF NOT EXISTS wiki_links (
    id TEXT PRIMARY KEY,
    source_page_id TEXT,
    target_page_id TEXT,
    relationship TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_page_id) REFERENCES wiki_pages(id),
    FOREIGN KEY (target_page_id) REFERENCES wiki_pages(id)
);

-- Synthesis execution log
CREATE TABLE IF NOT EXISTS synthesis_jobs (
    id TEXT PRIMARY KEY,
    wiki_page_id TEXT,
    trigger TEXT,  -- 'document_added', 'daily_synthesis', 'manual'
    status TEXT DEFAULT 'pending',  -- pending, running, complete, failed
    result_summary TEXT,
    updates_made INTEGER DEFAULT 0,
    contradictions_found INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY (wiki_page_id) REFERENCES wiki_pages(id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_wiki_pages_entity ON wiki_pages(entity_id);
CREATE INDEX IF NOT EXISTS idx_wiki_pages_topic ON wiki_pages(topic);
CREATE INDEX IF NOT EXISTS idx_wiki_pages_updated ON wiki_pages(last_updated);
CREATE INDEX IF NOT EXISTS idx_wiki_links_source ON wiki_links(source_page_id);
CREATE INDEX IF NOT EXISTS idx_wiki_links_target ON wiki_links(target_page_id);
CREATE INDEX IF NOT EXISTS idx_synthesis_jobs_status ON synthesis_jobs(status);
```

### 1.2: Wiki Storage Service

**File**: `storage/wiki_db.py` (NEW)

```python
"""Wiki page storage and management."""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import sqlite3

class WikiDB:
    """Manages wiki pages and relationships."""
    
    def __init__(self, conn=None):
        if conn is None:
            from storage.graph_db import get_graph_db
            conn = get_graph_db()
        self.conn = conn
        self.wiki_dir = Path.home() / "second-brain-data" / "wiki"
        self.wiki_dir.mkdir(parents=True, exist_ok=True)
    
    def create_wiki_page(
        self,
        entity_id: str,
        topic: str,
        initial_content: str = None
    ) -> str:
        """Create new wiki page."""
        page_id = f"wiki_{uuid.uuid4().hex[:12]}"
        
        default_content = f"""# {topic}

**Entity ID**: {entity_id}

## Overview
TBD - Initial content from entity extraction.

## Details
TBD - Will be populated from sources.

## Related Topics
See linked pages below.

## Sources
No sources yet.

---
*Auto-managed by Second Brain synthesis system*
"""
        
        content = initial_content or default_content
        
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO wiki_pages 
               (id, entity_id, topic, content, version, updated_by)
               VALUES (?, ?, ?, ?, 1, 'system')""",
            (page_id, entity_id, topic, content)
        )
        self.conn.commit()
        
        # Save to markdown file
        file_path = self.wiki_dir / f"{page_id}.md"
        file_path.write_text(content)
        
        return page_id
    
    def get_wiki_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get wiki page."""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT id, entity_id, topic, content, version, 
                      last_updated, updated_by
               FROM wiki_pages WHERE id = ?""",
            (page_id,)
        )
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            "id": row[0],
            "entity_id": row[1],
            "topic": row[2],
            "content": row[3],
            "version": row[4],
            "last_updated": row[5],
            "updated_by": row[6],
        }
    
    def update_wiki_page(
        self,
        page_id: str,
        new_content: str,
        change_description: str,
        updated_by: str = "system"
    ) -> bool:
        """Update wiki page with new content."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT version, content FROM wiki_pages WHERE id = ?",
            (page_id,)
        )
        result = cursor.fetchone()
        
        if not result:
            return False
        
        current_version = result[0]
        old_content = result[1]
        
        # Update database
        new_version = current_version + 1
        cursor.execute(
            """UPDATE wiki_pages 
               SET content = ?, version = ?, last_updated = ?, 
                   updated_by = ?
               WHERE id = ?""",
            (new_content, new_version, datetime.utcnow().isoformat(), 
             updated_by, page_id)
        )
        self.conn.commit()
        
        # Update markdown file
        file_path = self.wiki_dir / f"{page_id}.md"
        file_path.write_text(new_content)
        
        return True
    
    def list_wiki_pages(self, entity_id: str = None) -> List[Dict]:
        """List wiki pages."""
        cursor = self.conn.cursor()
        
        if entity_id:
            cursor.execute(
                """SELECT id, topic, version, last_updated 
                   FROM wiki_pages WHERE entity_id = ? 
                   ORDER BY last_updated DESC""",
                (entity_id,)
            )
        else:
            cursor.execute(
                """SELECT id, topic, version, last_updated 
                   FROM wiki_pages ORDER BY last_updated DESC"""
            )
        
        return [
            {
                "id": row[0],
                "topic": row[1],
                "version": row[2],
                "last_updated": row[3],
            }
            for row in cursor.fetchall()
        ]
    
    def create_wiki_link(
        self,
        source_page_id: str,
        target_page_id: str,
        relationship: str
    ) -> bool:
        """Create link between pages."""
        link_id = f"wl_{uuid.uuid4().hex[:12]}"
        cursor = self.conn.cursor()
        
        try:
            cursor.execute(
                """INSERT INTO wiki_links 
                   (id, source_page_id, target_page_id, relationship)
                   VALUES (?, ?, ?, ?)""",
                (link_id, source_page_id, target_page_id, relationship)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_related_pages(self, page_id: str) -> List[Dict]:
        """Get pages linked to this page."""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT wp.id, wp.topic, wl.relationship
               FROM wiki_links wl
               JOIN wiki_pages wp ON wl.target_page_id = wp.id
               WHERE wl.source_page_id = ?""",
            (page_id,)
        )
        
        return [
            {
                "id": row[0],
                "topic": row[1],
                "relationship": row[2],
            }
            for row in cursor.fetchall()
        ]
    
    def find_wiki_pages_for_entity(self, entity_id: str) -> str:
        """Get or create wiki page for entity."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id FROM wiki_pages WHERE entity_id = ?",
            (entity_id,)
        )
        
        result = cursor.fetchone()
        if result:
            return result[0]
        
        # Get entity name
        cursor.execute(
            "SELECT name FROM entities WHERE id = ?",
            (entity_id,)
        )
        name_result = cursor.fetchone()
        name = name_result[0] if name_result else "Unknown"
        
        # Create new page
        return self.create_wiki_page(entity_id, name)

def get_wiki_db(conn=None) -> WikiDB:
    """Get wiki database."""
    return WikiDB(conn)
```

### 1.3: Wiki API Routes

**File**: `api/routes/wiki.py` (NEW)

```python
"""Wiki management API."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from storage.wiki_db import get_wiki_db
from api.cache import cache, invalidate_pattern

router = APIRouter(prefix="/wiki", tags=["wiki"])

class WikiPageCreate(BaseModel):
    entity_id: str
    topic: str
    content: Optional[str] = None

class WikiPageUpdate(BaseModel):
    content: str
    change_description: str

@router.post("/pages")
def create_wiki_page(page: WikiPageCreate):
    """Create wiki page."""
    wiki = get_wiki_db()
    page_id = wiki.create_wiki_page(page.entity_id, page.topic, page.content)
    
    return {
        "id": page_id,
        "topic": page.topic,
        "entity_id": page.entity_id,
        "status": "created",
    }

@router.get("/pages/{page_id}")
@cache(ttl=3600)
def get_wiki_page(page_id: str):
    """Get wiki page."""
    wiki = get_wiki_db()
    page = wiki.get_wiki_page(page_id)
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    return page

@router.put("/pages/{page_id}")
def update_wiki_page(page_id: str, update: WikiPageUpdate):
    """Update wiki page."""
    wiki = get_wiki_db()
    
    success = wiki.update_wiki_page(
        page_id,
        update.content,
        update.change_description
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Page not found")
    
    invalidate_pattern(f"wiki*")
    
    return {"status": "updated", "page_id": page_id}

@router.get("/entity/{entity_id}/pages")
def get_entity_pages(entity_id: str):
    """Get pages for entity."""
    wiki = get_wiki_db()
    pages = wiki.list_wiki_pages(entity_id)
    
    return {
        "entity_id": entity_id,
        "pages": pages,
        "total": len(pages),
    }

@router.post("/pages/{source_id}/link/{target_id}")
def link_pages(source_id: str, target_id: str, relationship: str):
    """Link pages."""
    wiki = get_wiki_db()
    success = wiki.create_wiki_link(source_id, target_id, relationship)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to link")
    
    return {"status": "linked"}

@router.get("/pages/{page_id}/related")
def get_related_pages(page_id: str):
    """Get related pages."""
    wiki = get_wiki_db()
    related = wiki.get_related_pages(page_id)
    
    return {"page_id": page_id, "related": related}
```

---

## Task 2: Active Integration Service (12 hours)

### 2.1: Synthesis Service

**File**: `api/synthesis_service.py` (NEW - Core Logic)

```python
"""Knowledge synthesis service."""

import json
import os
import asyncio
from typing import Dict, List, Any
from datetime import datetime
from storage.graph_db import GraphDB, get_graph_db
from storage.wiki_db import WikiDB, get_wiki_db
from api.cache import invalidate_pattern
import anthropic

class SynthesisService:
    """Synthesizes knowledge when documents arrive."""
    
    def __init__(self):
        self.graph_db = GraphDB(get_graph_db())
        self.wiki_db = WikiDB()
        self.client = anthropic.Anthropic()
    
    async def integrate_document(
        self,
        document_id: str,
        entities: List[Dict]
    ) -> Dict[str, Any]:
        """Integrate new document by updating wiki pages."""
        
        results = {
            "document_id": document_id,
            "entities_processed": len(entities),
            "pages_created": 0,
            "pages_updated": 0,
            "links_created": 0,
            "contradictions": [],
        }
        
        for entity in entities:
            # Ensure wiki page exists
            page_id = self.wiki_db.find_wiki_pages_for_entity(entity["id"])
            
            # Get related pages for context
            cursor = self.graph_db.conn.cursor()
            cursor.execute(
                """SELECT DISTINCT target_entity_id 
                   FROM relationships 
                   WHERE source_entity_id = ?""",
                (entity["id"],)
            )
            
            related_entity_ids = [row[0] for row in cursor.fetchall()]
            
            # Find wiki pages for related entities
            related_page_ids = []
            for rel_id in related_entity_ids[:5]:  # Limit to 5
                cursor.execute(
                    "SELECT id FROM wiki_pages WHERE entity_id = ?",
                    (rel_id,)
                )
                result = cursor.fetchone()
                if result:
                    related_page_ids.append(result[0])
            
            # Synthesize update
            synthesis = await self._synthesize_with_claude(
                entity,
                page_id,
                related_page_ids,
                document_id
            )
            
            if synthesis.get("should_update"):
                self.wiki_db.update_wiki_page(
                    page_id,
                    synthesis["new_content"],
                    f"Updated from document {document_id}",
                    "synthesis_service"
                )
                results["pages_updated"] += 1
                invalidate_pattern("wiki*")
            
            # Create links to related pages
            for rel_page_id in related_page_ids:
                if self.wiki_db.create_wiki_link(
                    page_id,
                    rel_page_id,
                    "related"
                ):
                    results["links_created"] += 1
            
            if synthesis.get("contradictions"):
                results["contradictions"].extend(synthesis["contradictions"])
        
        return results
    
    async def _synthesize_with_claude(
        self,
        entity: Dict,
        page_id: str,
        related_page_ids: List[str],
        document_id: str
    ) -> Dict[str, Any]:
        """Use Claude to synthesize understanding."""
        
        # Get current wiki content
        current_page = self.wiki_db.get_wiki_page(page_id)
        
        # Get related wiki content for context
        related_content = []
        for rel_id in related_page_ids:
            rel_page = self.wiki_db.get_wiki_page(rel_id)
            if rel_page:
                related_content.append({
                    "topic": rel_page["topic"],
                    "content": rel_page["content"][:500]  # First 500 chars
                })
        
        prompt = f"""You are a knowledge synthesis assistant helping maintain a personal knowledge base.

Current Understanding of '{entity['name']}':
{current_page['content']}

Related Topics for Context:
{json.dumps(related_content, indent=2)}

New Information Added:
Entity: {entity['name']}
Type: {entity.get('type', 'Unknown')}
Definition: {entity.get('definition', 'Not provided')}

Your Task:
1. Should we update the wiki page based on this new information?
2. If yes, provide improved understanding that integrates this information
3. Flag any contradictions with current knowledge

Respond with valid JSON only:
{{
    "should_update": true/false,
    "reasoning": "Why or why not update",
    "new_content": "Updated markdown (only if should_update=true)",
    "contradictions": ["list of contradictions if any"]
}}"""
        
        try:
            message = self.client.messages.create(
                model="claude-opus-4-7",
                max_tokens=1500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            result = json.loads(response_text)
            return result
        
        except Exception as e:
            # Fallback if synthesis fails
            return {
                "should_update": False,
                "reasoning": f"Synthesis failed: {str(e)}",
                "contradictions": []
            }

def get_synthesis_service() -> SynthesisService:
    """Get synthesis service."""
    return SynthesisService()
```

### 2.2: Integration Hook

**File**: `api/routes/documents.py` (UPDATE)

Add to `process_document` endpoint:

```python
from api.synthesis_service import get_synthesis_service

# After document processing completes, integrate with synthesis
synthesis_service = get_synthesis_service()
await synthesis_service.integrate_document(document_id, extracted_entities)
```

---

## Task 3: Contradiction Detection (6 hours)

```python
class ContradictionDetector:
    """Detects contradictions in knowledge."""
    
    async def detect_contradictions(
        self,
        new_fact: str,
        entity_id: str
    ) -> Dict[str, Any]:
        """Detect if new fact contradicts existing knowledge."""
        
        # Get wiki page for entity
        wiki_db = get_wiki_db()
        page_id = wiki_db.find_wiki_pages_for_entity(entity_id)
        page = wiki_db.get_wiki_page(page_id)
        
        # Use Claude to detect contradictions
        prompt = f"""Detect contradictions:
        
New Fact: {new_fact}

Current Knowledge:
{page['content']}

Is there a contradiction? Respond with JSON:
{{
    "is_contradiction": true/false,
    "confidence": 0.95,
    "explanation": "..."
}}"""
        
        # Call Claude...
```

---

## Task 4: Periodic Synthesis (12 hours)

```python
class PeriodicSynthesizer:
    """Runs periodic synthesis jobs."""
    
    async def synthesize_daily(self):
        """Daily synthesis to consolidate understanding."""
        
        wiki_db = get_wiki_db()
        pages = wiki_db.list_wiki_pages()
        
        for page in pages:
            # For each page, synthesize current understanding
            # Generate "open questions"
            # Generate "key insights"
            # Update page with new sections
```

---

## Task 5: Knowledge Graph ↔ Wiki Sync (8 hours)

```python
class SyncManager:
    """Keeps graph and wiki in sync."""
    
    async def sync_graph_to_wiki(self):
        """Graph changes → Wiki updates."""
        # When relationship created → Update related pages
        # When entity renamed → Update wiki
    
    async def sync_wiki_to_graph(self):
        """Wiki changes → Graph updates."""
        # When page edited → Update entity metadata
        # When link created → Create relationship
```

---

## Testing

**Create**: `tests/test_synthesis.py`

```python
def test_wiki_page_creation():
    wiki = get_wiki_db()
    page_id = wiki.create_wiki_page("entity1", "Test Topic")
    assert page_id.startswith("wiki_")

def test_wiki_page_update():
    wiki = get_wiki_db()
    page_id = wiki.create_wiki_page("entity1", "Test")
    success = wiki.update_wiki_page(page_id, "New content", "test update")
    assert success

def test_synthesis_integration():
    service = get_synthesis_service()
    result = asyncio.run(service.integrate_document(
        "doc1",
        [{"id": "ent1", "name": "Test", "type": "Concept"}]
    ))
    assert result["pages_updated"] >= 0
```

---

## Quick Reference

| Task | Hours | Files | Functions |
|------|-------|-------|-----------|
| 1. Wiki Layer | 8 | wiki_db.py, wiki.py | 6+ methods |
| 2. Active Integration | 12 | synthesis_service.py | 2 core methods |
| 3. Contradiction | 6 | contradiction_detector.py | 1 core method |
| 4. Periodic | 12 | periodic_synthesis.py | 2 core methods |
| 5. Sync | 8 | sync_manager.py | 2 core methods |

---

## Integration Points

```
documents.py → synthesis_service → wiki_db → wiki pages
          ↓
      periodic jobs → synthesis_jobs → wiki updates
          ↓
      contradiction detector → flags contradictions
          ↓
      sync_manager ↔ knowledge graph ↔ wiki
```

---

This breakdown gives you everything needed to implement Phase 6. Start with Task 1 (Wiki Layer), then build each task incrementally.

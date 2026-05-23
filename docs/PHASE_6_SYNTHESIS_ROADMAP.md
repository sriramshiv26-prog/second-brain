# Phase 6: AI-Powered Knowledge Synthesis Layer

**Status**: PLANNED  
**Estimated Time**: 40-50 hours  
**Cost**: $0 local + ~$2-5 Claude Sonnet (for synthesis decisions)  
**Inspiration**: Andrej Karpathy's "LLM Wiki" vision  

## Vision

Transform Second Brain from a **knowledge retrieval system** into a **knowledge synthesis system**.

Instead of just storing and searching documents, automatically:
- Synthesize understanding from new documents
- Update evolving knowledge wiki pages
- Detect contradictions between sources
- Deepen knowledge with each addition
- Maintain a "truth state" that evolves

**Current flow**:
```
Document → Parse → Extract → Store → (user searches) → Retrieve
```

**Phase 6 flow**:
```
Document → Parse → Extract → FIND RELATED KNOWLEDGE → LLM SYNTHESIZES → UPDATE WIKI → Refine understanding
```

---

## Overview

Phase 6 adds 5 major components to create Karpathy's vision:

### Task 1: Markdown Wiki Layer (8h)
- Generate markdown files for each entity/topic
- These become the "source of truth"
- Version controlled and auditable
- Auto-updated by LLM

### Task 2: Active Integration (12h)
- When document added → Find related wiki pages
- LLM reads document + related wiki pages
- Synthesizes updates
- Updates wiki automatically
- Logs changes

### Task 3: Contradiction Detection (6h)
- Compare new facts against existing knowledge
- Flag conflicts
- Ask LLM to reconcile or note as "unresolved"
- Surface to user

### Task 4: Automatic Synthesis (12h)
- Periodic synthesis jobs (daily/weekly)
- Consolidate all facts about a topic
- Generate "current understanding" documents
- Create "open questions" list
- Generate "key insights"

### Task 5: Knowledge Graph ↔ Wiki Sync (8h)
- Two-way synchronization
- Changes in graph update wiki
- Changes in wiki update graph
- Single source of truth across formats

---

## Part 1: Markdown Wiki Layer (Task 1)

### Files to Create

**Create**: `storage/wiki_db.py`
**Create**: `api/routes/wiki.py`
**Modify**: `config/db_schema.sql`

### Task 1.1: Database Schema for Wiki

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
    updated_by TEXT,
    change_log TEXT,  -- JSON array of changes
    FOREIGN KEY (entity_id) REFERENCES entities(id)
);

-- Wiki metadata
CREATE TABLE IF NOT EXISTS wiki_metadata (
    id TEXT PRIMARY KEY,
    wiki_page_id TEXT,
    key TEXT,
    value TEXT,
    FOREIGN KEY (wiki_page_id) REFERENCES wiki_pages(id)
);

-- Related pages (links between wiki pages)
CREATE TABLE IF NOT EXISTS wiki_links (
    id TEXT PRIMARY KEY,
    source_page_id TEXT,
    target_page_id TEXT,
    relationship TEXT,
    FOREIGN KEY (source_page_id) REFERENCES wiki_pages(id),
    FOREIGN KEY (target_page_id) REFERENCES wiki_pages(id)
);

-- Synthesis jobs (for Phase 4 task)
CREATE TABLE IF NOT EXISTS synthesis_jobs (
    id TEXT PRIMARY KEY,
    wiki_page_id TEXT,
    status TEXT (pending, running, complete, failed),
    synthesis_result TEXT,
    contradictions_found INTEGER,
    last_run DATETIME,
    next_scheduled DATETIME,
    FOREIGN KEY (wiki_page_id) REFERENCES wiki_pages(id)
);

CREATE INDEX IF NOT EXISTS idx_wiki_pages_entity ON wiki_pages(entity_id);
CREATE INDEX IF NOT EXISTS idx_wiki_pages_topic ON wiki_pages(topic);
CREATE INDEX IF NOT EXISTS idx_wiki_pages_updated ON wiki_pages(last_updated);
```

### Task 1.2: Wiki Storage Service

**File**: `storage/wiki_db.py` (NEW)

```python
"""Wiki page management and synthesis."""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import sqlite3

class WikiDB:
    """Manages wiki pages and synthesis."""
    
    def __init__(self, conn=None):
        if conn is None:
            from storage.graph_db import get_graph_db
            conn = get_graph_db()
        self.conn = conn
        self.wiki_dir = Path.home() / "second-brain-data" / "wiki"
        self.wiki_dir.mkdir(parents=True, exist_ok=True)
    
    def create_wiki_page(self, entity_id: str, topic: str, initial_content: str = None) -> str:
        """Create a new wiki page for an entity/topic."""
        page_id = f"wiki_{uuid.uuid4().hex[:12]}"
        
        # Create in database
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO wiki_pages (id, entity_id, topic, content, version, updated_by)
               VALUES (?, ?, ?, ?, 1, 'system')""",
            (page_id, entity_id, topic, initial_content or f"# {topic}\n\nNo content yet.")
        )
        self.conn.commit()
        
        # Create markdown file
        file_path = self.wiki_dir / f"{page_id}.md"
        file_path.write_text(initial_content or f"# {topic}\n\nNo content yet.")
        
        return page_id
    
    def update_wiki_page(self, page_id: str, new_content: str, change_description: str, updated_by: str = "system") -> bool:
        """Update wiki page with new content."""
        cursor = self.conn.cursor()
        
        # Get current version
        cursor.execute("SELECT version, content FROM wiki_pages WHERE id = ?", (page_id,))
        result = cursor.fetchone()
        if not result:
            return False
        
        current_version = result[0]
        old_content = result[1]
        
        # Log change
        change_log = {
            "version": current_version + 1,
            "timestamp": datetime.utcnow().isoformat(),
            "description": change_description,
            "updated_by": updated_by,
            "old_length": len(old_content) if old_content else 0,
            "new_length": len(new_content),
        }
        
        # Update database
        cursor.execute(
            """UPDATE wiki_pages 
               SET content = ?, version = version + 1, last_updated = ?, updated_by = ?,
                   change_log = json_array(?)
               WHERE id = ?""",
            (new_content, datetime.utcnow().isoformat(), updated_by, json.dumps(change_log), page_id)
        )
        self.conn.commit()
        
        # Update markdown file
        file_path = self.wiki_dir / f"{page_id}.md"
        file_path.write_text(new_content)
        
        return True
    
    def get_wiki_page(self, page_id: str) -> Dict[str, Any]:
        """Get wiki page content."""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT id, entity_id, topic, content, version, last_updated, updated_by
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
    
    def list_wiki_pages(self, entity_id: str = None) -> List[Dict]:
        """List all wiki pages, optionally filtered by entity."""
        cursor = self.conn.cursor()
        
        if entity_id:
            cursor.execute(
                """SELECT id, topic, version, last_updated FROM wiki_pages 
                   WHERE entity_id = ? ORDER BY last_updated DESC""",
                (entity_id,)
            )
        else:
            cursor.execute(
                """SELECT id, topic, version, last_updated FROM wiki_pages 
                   ORDER BY last_updated DESC"""
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
    
    def link_wiki_pages(self, source_page_id: str, target_page_id: str, relationship: str) -> bool:
        """Create link between wiki pages."""
        link_id = f"wl_{uuid.uuid4().hex[:12]}"
        cursor = self.conn.cursor()
        
        try:
            cursor.execute(
                """INSERT INTO wiki_links (id, source_page_id, target_page_id, relationship)
                   VALUES (?, ?, ?, ?)""",
                (link_id, source_page_id, target_page_id, relationship)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_related_pages(self, page_id: str) -> List[Dict]:
        """Get related wiki pages."""
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
    
    def find_related_pages(self, entity_id: str) -> List[str]:
        """Find wiki pages related to an entity based on relationships."""
        cursor = self.conn.cursor()
        
        # Get relationships for this entity
        cursor.execute(
            """SELECT DISTINCT target_entity_id FROM relationships 
               WHERE source_entity_id = ?
               UNION
               SELECT DISTINCT source_entity_id FROM relationships 
               WHERE target_entity_id = ?""",
            (entity_id, entity_id)
        )
        
        related_entities = [row[0] for row in cursor.fetchall()]
        
        # Find wiki pages for related entities
        page_ids = []
        for rel_entity_id in related_entities:
            cursor.execute(
                "SELECT id FROM wiki_pages WHERE entity_id = ?",
                (rel_entity_id,)
            )
            pages = cursor.fetchall()
            page_ids.extend([row[0] for row in pages])
        
        return page_ids

def get_wiki_db(conn=None) -> WikiDB:
    """Get wiki database instance."""
    return WikiDB(conn)
```

### Task 1.3: Wiki API Routes

**File**: `api/routes/wiki.py` (NEW)

```python
"""Wiki management endpoints."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List
from storage.wiki_db import get_wiki_db
from api.cache import cache, invalidate_pattern
import uuid

router = APIRouter(prefix="/wiki", tags=["wiki"])

class WikiPageCreate(BaseModel):
    entity_id: str
    topic: str
    content: str = None

class WikiPageUpdate(BaseModel):
    content: str
    change_description: str

@router.post("/pages")
def create_wiki_page(page: WikiPageCreate):
    """Create new wiki page."""
    wiki = get_wiki_db()
    page_id = wiki.create_wiki_page(page.entity_id, page.topic, page.content)
    
    return {
        "id": page_id,
        "topic": page.topic,
        "entity_id": page.entity_id,
        "created_at": datetime.utcnow().isoformat(),
    }

@router.get("/pages/{page_id}")
@cache(ttl=3600)
def get_wiki_page(page_id: str):
    """Get wiki page content."""
    wiki = get_wiki_db()
    page = wiki.get_wiki_page(page_id)
    
    if not page:
        raise HTTPException(status_code=404, detail="Wiki page not found")
    
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
        raise HTTPException(status_code=404, detail="Wiki page not found")
    
    # Invalidate cache
    invalidate_pattern(f"wiki/{page_id}*")
    
    return {"status": "updated", "page_id": page_id}

@router.get("/entity/{entity_id}/pages")
def get_entity_wiki_pages(entity_id: str):
    """Get all wiki pages for an entity."""
    wiki = get_wiki_db()
    pages = wiki.list_wiki_pages(entity_id)
    
    return {
        "entity_id": entity_id,
        "pages": pages,
        "total": len(pages),
    }

@router.get("/pages/{page_id}/related")
def get_related_wiki_pages(page_id: str):
    """Get related wiki pages."""
    wiki = get_wiki_db()
    related = wiki.get_related_pages(page_id)
    
    return {
        "page_id": page_id,
        "related": related,
        "count": len(related),
    }

@router.post("/pages/{source_id}/link/{target_id}")
def link_wiki_pages(source_id: str, target_id: str, relationship: str):
    """Create link between wiki pages."""
    wiki = get_wiki_db()
    
    success = wiki.link_wiki_pages(source_id, target_id, relationship)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to create link")
    
    return {"status": "linked", "source": source_id, "target": target_id, "relationship": relationship}

from datetime import datetime
```

---

## Part 2: Active Integration (Task 2)

### Files to Create

**Create**: `api/synthesis_service.py`

### Task 2.1: Document Integration Service

**File**: `api/synthesis_service.py` (NEW - excerpt)

```python
"""AI-powered knowledge synthesis service."""

import asyncio
from typing import List, Dict, Any
from storage.graph_db import GraphDB, get_graph_db
from storage.wiki_db import WikiDB, get_wiki_db
from process.embed import EmbeddingPipeline
from api.cache import invalidate_pattern
import httpx

class SynthesisService:
    """Synthesizes knowledge when new documents arrive."""
    
    def __init__(self):
        self.graph_db = GraphDB(get_graph_db())
        self.wiki_db = WikiDB()
        self.embedder = EmbeddingPipeline()
    
    async def integrate_new_document(self, document_id: str, extracted_entities: List[Dict]) -> Dict[str, Any]:
        """
        When new document processed, find related knowledge and synthesize updates.
        
        Flow:
        1. For each extracted entity
        2. Find or create wiki page
        3. Find related wiki pages (based on relationships)
        4. Ask LLM: "Given this new document, how should we update our understanding?"
        5. Update wiki pages
        6. Log changes
        """
        
        results = {
            "document_id": document_id,
            "pages_created": 0,
            "pages_updated": 0,
            "syntheses_performed": 0,
            "contradictions_found": [],
        }
        
        for entity in extracted_entities:
            # 1. Find or create wiki page
            page_id = await self._ensure_wiki_page_exists(entity)
            
            # 2. Find related pages
            related_pages = self.wiki_db.find_related_pages(entity["id"])
            
            # 3. Synthesize with LLM
            if related_pages:
                synthesis = await self._synthesize_update(
                    document_id,
                    entity,
                    page_id,
                    related_pages
                )
                
                if synthesis["should_update"]:
                    # Update wiki page
                    self.wiki_db.update_wiki_page(
                        page_id,
                        synthesis["new_content"],
                        f"Updated based on document {document_id}",
                        updated_by="synthesis_service"
                    )
                    results["pages_updated"] += 1
                    results["syntheses_performed"] += 1
                
                if synthesis.get("contradictions"):
                    results["contradictions_found"].extend(synthesis["contradictions"])
        
        return results
    
    async def _ensure_wiki_page_exists(self, entity: Dict) -> str:
        """Create wiki page if it doesn't exist."""
        cursor = self.graph_db.conn.cursor()
        cursor.execute(
            "SELECT id FROM wiki_pages WHERE entity_id = ?",
            (entity["id"],)
        )
        
        if cursor.fetchone():
            return cursor.fetchone()[0]
        
        # Create new page
        page_id = self.wiki_db.create_wiki_page(
            entity["id"],
            entity["name"],
            f"# {entity['name']}\n\nType: {entity['type']}\n\n{entity.get('definition', '')}"
        )
        
        return page_id
    
    async def _synthesize_update(self, document_id: str, entity: Dict, page_id: str, related_pages: List[str]) -> Dict[str, Any]:
        """
        Use LLM to determine if wiki page should be updated based on new document.
        
        Calls Claude to:
        - Read current understanding from wiki page
        - Read related pages for context
        - Read new document excerpt
        - Decide: Should we update understanding?
        - Detect contradictions
        """
        
        # Get current wiki content
        current_page = self.wiki_db.get_wiki_page(page_id)
        
        # Get related wiki content
        related_content = {}
        for rel_page_id in related_pages[:5]:  # Limit to 5 for context
            rel_page = self.wiki_db.get_wiki_page(rel_page_id)
            if rel_page:
                related_content[rel_page["topic"]] = rel_page["content"]
        
        # Prepare prompt for Claude
        prompt = f"""
You are a knowledge synthesis assistant. 

Current understanding of {entity['name']}:
{current_page['content']}

Related knowledge:
{json.dumps(related_content, indent=2)}

New information from document:
{entity.get('context', '')}

Your task:
1. Analyze if this new information changes our understanding
2. If yes, provide updated understanding
3. Flag any contradictions with current knowledge
4. Suggest related pages that should be linked

Respond as JSON:
{{
    "should_update": true/false,
    "new_content": "Updated markdown content",
    "reasoning": "Why we should/shouldn't update",
    "contradictions": ["list of contradictions if any"],
    "suggested_links": ["related topic names to link"]
}}
"""
        
        # Call Claude for synthesis
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": os.environ.get("ANTHROPIC_API_KEY"),
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-opus-4-7",  # Or appropriate model
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
        
        # Parse response
        synthesis_result = json.loads(response.json()["content"][0]["text"])
        return synthesis_result

def get_synthesis_service() -> SynthesisService:
    """Get synthesis service instance."""
    return SynthesisService()
```

---

## Part 3: Contradiction Detection (Task 3)

### Files to Create

**Create**: `api/contradiction_detector.py`

```python
"""Detect contradictions between new information and existing knowledge."""

class ContradictionDetector:
    """Detects logical contradictions in knowledge base."""
    
    async def check_contradiction(self, new_fact: str, entity_id: str) -> Dict[str, Any]:
        """
        Check if new fact contradicts existing knowledge.
        
        Returns:
        - is_contradiction: bool
        - confidence: float (0-1)
        - conflicting_facts: list
        - resolution: suggested resolution
        """
        
        # Get all facts about entity from wiki pages
        wiki = get_wiki_db()
        wiki_pages = wiki.list_wiki_pages(entity_id)
        
        existing_facts = []
        for page in wiki_pages:
            page_content = wiki.get_wiki_page(page["id"])
            existing_facts.append(page_content["content"])
        
        # Use LLM to detect contradictions
        prompt = f"""
Analyze if this new fact contradicts any existing knowledge:

New Fact: {new_fact}

Existing Knowledge:
{json.dumps(existing_facts)}

Response as JSON:
{{
    "is_contradiction": true/false,
    "confidence": 0.95,
    "conflicting_fact": "The specific fact it contradicts",
    "resolution": "Suggested way to reconcile or mark as conflicting"
}}
"""
        
        # Call Claude
        # ... (implementation details)
```

---

## Part 4: Automatic Synthesis (Task 4)

### Files to Create

**Create**: `api/periodic_synthesis.py`

```python
"""Periodic synthesis jobs that deepen understanding."""

class PeriodicSynthesizer:
    """Runs daily/weekly synthesis to consolidate knowledge."""
    
    async def daily_synthesis(self):
        """Daily: Update each wiki page with consolidated facts."""
        
        # For each wiki page:
        # 1. Collect all facts about that topic
        # 2. Ask LLM: "What is our current understanding?"
        # 3. Ask LLM: "What are the open questions?"
        # 4. Ask LLM: "What are the key insights?"
        # 5. Update "Current Understanding" section
        # 6. Add "Open Questions" section
        # 7. Add "Key Insights" section
    
    async def weekly_synthesis(self):
        """Weekly: Synthesize across multiple topics to find connections."""
        
        # For each pair of related wiki pages:
        # 1. Ask LLM: "How do these topics relate?"
        # 2. Create synthesis document
        # 3. Suggest new connections
        # 4. Update relationship strength
```

---

## Part 5: Knowledge Graph ↔ Wiki Sync (Task 5)

### Bidirectional Sync

```python
class SyncManager:
    """Keeps knowledge graph and wiki in sync."""
    
    async def sync_graph_to_wiki(self):
        """When graph changes, update wiki."""
        # New relationship created → Add to relevant wiki pages
        # Entity updated → Update wiki page
        # Entity merged → Merge wiki pages
    
    async def sync_wiki_to_graph(self):
        """When wiki changes, update graph."""
        # Wiki page edited → Update entity metadata
        # New link created → Create relationship
        # Page merged → Merge entities
```

---

## Implementation Roadmap

### Week 1: Wiki Foundation
- **Day 1-2**: Task 1 (Markdown Wiki Layer)
- **Day 3**: Basic API routes for wiki

### Week 2: Active Synthesis
- **Day 1-2**: Task 2 (Active Integration)
- **Day 3**: Wire into document ingestion pipeline

### Week 3: Intelligence
- **Day 1**: Task 3 (Contradiction Detection)
- **Day 2**: Task 4 (Periodic Synthesis)
- **Day 3**: Task 5 (Sync Manager)

### Week 4: Testing & Refinement
- **Day 1-2**: Test all synthesis flows
- **Day 3**: Optimization and documentation

---

## Database Schema Summary

New tables added:
```sql
wiki_pages          — Markdown files + metadata
wiki_metadata       — Additional page info
wiki_links          — Page relationships
synthesis_jobs      — Synthesis execution log
```

---

## Cost Analysis

**Backend computation**: $0 (local)
**Claude Sonnet for synthesis**: 
- ~5 synthesis calls per document
- ~0.01 per call = ~$0.05 per document
- Average project: 50 documents = ~$2.50
- Large project: 500 documents = ~$25

**Total Phase 6**: $0-30 depending on document volume

---

## Success Metrics

Phase 6 is complete when:
- [ ] Wiki pages auto-generate for entities
- [ ] New documents trigger synthesis updates
- [ ] Contradictions detected and surfaced
- [ ] Daily synthesis job produces insights
- [ ] Graph ↔ Wiki stays in sync
- [ ] All tests passing
- [ ] 120+ API tests (up from 90+)

---

## The Transformation

**Before Phase 6** (Retrieval):
```
User: "What do I know about neural networks?"
System: Searches and retrieves relevant documents
```

**After Phase 6** (Synthesis):
```
System: "You added 3 new papers about neural networks. Here's how they 
change our understanding... These new ideas challenge your previous assumption 
about X. Here are the open questions. Here are key insights you're missing."
```

---

## Next Steps

1. Start with Task 1 (Markdown Wiki Layer)
2. Build incrementally
3. Test at each stage
4. Commit frequently
5. Update memory with progress

This is what transforms Second Brain from good to **Karpathy-grade** ✨

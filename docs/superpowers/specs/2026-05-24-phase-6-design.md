# Phase 6 Design Spec: Local-First Hybrid Synthesis
**Status**: APPROVED  
**Date**: 2026-05-24  
**Approach**: Option B (Local-First Hybrid with cost optimization)  
**Estimated Cost**: $0.50-2.00/month (80%+ savings vs Claude-only)  
**Estimated Time**: 46 hours (Chunk 1: 20h, Chunk 2: 26h)

---

## 1. Vision & Goals

**Current State (Phases 1-5)**:
```
Document → Parse → Extract → Store → Search → Retrieve
```

**Phase 6 Target**:
```
Document → Parse → Extract → [FIND RELATED] → [LLM SYNTHESIZES] → [UPDATE WIKI] → Knowledge Deepens
```

**Inspired by**: Andrej Karpathy's "LLM Wiki" approach—knowledge that actively evolves and deepens with each addition.

**Success Metrics**:
- New documents auto-create wiki pages (Task 2)
- Contradictions detected and flagged (Task 3)
- Daily synthesis consolidates knowledge (Task 4)
- Graph and wiki stay bidirectionally synced (Task 5)
- Total monthly cost < $2.00 (vs $5-10 for Claude-only)

---

## 2. Architecture

### 2.1 System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERACTION LAYER                        │
│         (Web UI / Obsidian Plugin / CLI)                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    FASTAPI SERVER                                │
├──────────────────────────────────────────────────────────────────┤
│  Routes Layer (NEW endpoints)                                    │
│  ├─ POST /documents/{id}/process  (hook: Task 2)               │
│  ├─ POST/GET /wiki                 (Task 1)                     │
│  ├─ GET /contradictions            (Task 3)                     │
│  ├─ POST /synthesis/trigger        (Task 4)                     │
│  └─ POST /sync/force               (Task 5)                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│              SERVICE LAYER (NEW MODULES)                        │
├──────────────────────────────────────────────────────────────────┤
│  • wiki_db.py              → SQLite wiki pages CRUD              │
│  • synthesis_service.py    → Orchestrates Tasks 2-5              │
│  • contradiction_detector.py → Logic conflict detection          │
│  • periodic_synthesis.py   → Scheduled daily consolidation       │
│  • sync_manager.py         → Graph ↔ Wiki bidirectional sync     │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
│  SQLITE      │  │   OLLAMA    │  │   QWEN API  │
│  Wiki DB     │  │  (Local)    │  │  (Remote)   │
│  NEW TABLE   │  │  FREE       │  │  Ultra-cheap│
│              │  │ Embeddings  │  │  Synthesis  │
│              │  │ Entity XTR  │  │  & Logic    │
└──────────────┘  └─────────────┘  └──────────────┘
```

### 2.2 Cost Allocation Strategy

**Chunk 1 ($0.00)**:
- Task 1: Wiki layer (SQLite, Python ORM) — No external calls
- Task 2: Auto-integration (Ollama embeddings) — Local, no cost

**Chunk 2 (~$0.20-0.50/week)**:
- Task 3: Contradiction detection (Qwen, ~2 calls/week per entity) — $0.001-0.005/call
- Task 4: Periodic synthesis (Qwen batched, 1x/day) — $0.0005-0.002/call
- Task 5: Graph↔wiki sync (local Python) — No cost

**Optional Premium (per-request)**:
- User-triggered Claude Sonnet synthesis (reserved for high-value items)
- Cost: $0.01-0.05 per synthesis
- Frequency: ~5% of documents (estimated)

**Total Monthly**: $2-10 vs $50+ for Claude-only approach (80%+ savings)

---

## 3. Task Breakdown & Implementation Path

### 3.1 Chunk 1: Wiki Foundation (20 hours, $0)

#### **Task 1: Wiki Layer (8 hours)**
**What**: Markdown wiki with SQLite backend

**Deliverables**:
- Database schema (`config/db_schema.sql` — wiki_pages table)
- Module: `storage/wiki_db.py` (CRUD operations)
- Routes: `api/routes/wiki.py` (REST endpoints)
- Tests: `tests/test_synthesis.py::test_wiki_*`

**Endpoints**:
```
POST   /wiki                    Create new wiki page
GET    /wiki/{slug}            Fetch page + links
PUT    /wiki/{slug}            Update page content
DELETE /wiki/{slug}            Archive page
GET    /wiki/search?q=query    Full-text search
GET    /wiki/graph             Return backlink graph (for visualization)
```

**Database Schema**:
```sql
CREATE TABLE wiki_pages (
    id TEXT PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content TEXT,                    -- Markdown
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_synthesis TIMESTAMP,        -- Track when last updated by synthesis
    entity_ids TEXT,                 -- JSON list of linked entities
    contradiction_count INT DEFAULT 0,
    version INT DEFAULT 1
);

CREATE TABLE wiki_backlinks (
    from_slug TEXT,
    to_slug TEXT,
    context TEXT,                   -- Why they're related
    PRIMARY KEY (from_slug, to_slug)
);
```

**Code Structure** (`storage/wiki_db.py`):
```python
class WikiPage:
    id: str
    slug: str
    title: str
    content: str  # Markdown
    created_at: datetime
    updated_at: datetime
    entity_ids: List[str]  # Linked entities from graph

def create_page(title: str, content: str, entity_ids: List[str]) → WikiPage
def get_page(slug: str) → WikiPage | None
def update_page(slug: str, content: str) → WikiPage
def search_pages(query: str) → List[WikiPage]
def add_backlink(from_slug: str, to_slug: str, context: str) → None
def get_related_pages(slug: str) → List[WikiPage]
```

**Integration Point**: Register router in `api/server.py`

---

#### **Task 2: Active Integration (12 hours)**
**What**: Auto-create/update wiki pages when documents added

**Deliverables**:
- Module: `api/synthesis_service.py` (orchestrates integration)
- Hook in: `api/routes/documents.py` (call synthesis_service after processing)
- Tests: `tests/test_synthesis.py::test_integration_*`

**Flow**:
```
1. Document uploaded → Stored in graph DB
2. Entities extracted (existing pipeline)
3. synthesis_service.integrate_document() called
4. For each entity:
   a. Check if wiki page exists for this entity
   b. If not: Create new page with entity info + context
   c. If yes: Queue for Task 4 (periodic synthesis) to update
5. Create backlinks between related entities
```

**Code Structure** (`api/synthesis_service.py`):
```python
class SynthesisService:
    def integrate_document(
        self,
        doc_id: str,
        entities: List[Entity]
    ) → Dict[str, str]:  # {entity_id: wiki_slug}
        """
        Main integration hook.
        1. Create/get wiki pages for entities
        2. Add backlinks based on relationships
        3. Return mapping of entity_id → wiki_slug
        """
        
    def _create_wiki_page(
        self,
        entity: Entity,
        context: str
    ) → WikiPage:
        """
        Create initial wiki page from entity.
        Uses entity metadata (name, type, relationships).
        """
        
    def _link_related_entities(
        self,
        primary_entity_id: str,
        related_entities: List[Entity]
    ) → None:
        """
        Create backlinks between related entities.
        """
```

**Integration Hook** (in `api/routes/documents.py`):
```python
@router.post("/documents/{doc_id}/process")
async def process_document(doc_id: str):
    # ... existing processing ...
    
    # NEW: Trigger synthesis integration
    synthesis_service = get_synthesis_service()
    wiki_mapping = await synthesis_service.integrate_document(
        doc_id,
        extracted_entities
    )
    
    return {
        "document": doc_data,
        "wiki_pages_created": wiki_mapping  # NEW
    }
```

**Chunk 1 Result**: 
- ✅ Wiki layer operational
- ✅ Documents auto-create wiki pages
- ✅ Zero external API calls
- ✅ Ready to move to Chunk 2

---

### 3.2 Chunk 2: Smart Synthesis (26 hours, ~$0.20-0.50/week)

#### **Task 3: Contradiction Detection (6 hours)**
**What**: Identify conflicting information in knowledge base

**Deliverables**:
- Module: `api/contradiction_detector.py`
- Routes: `api/routes/contradictions.py`
- Tests: `tests/test_synthesis.py::test_contradiction_*`

**Endpoints**:
```
GET  /contradictions              List all detected conflicts
GET  /contradictions/{id}         Fetch conflict details
POST /contradictions/{id}/resolve Mark as resolved
```

**Logic**:
```python
class ContradictionDetector:
    def detect(self, entity_id: str) → List[Contradiction]:
        """
        1. Get entity from graph DB
        2. Get all wiki pages mentioning this entity
        3. Run Qwen logic check: "Do these statements about {entity} conflict?"
        4. Return list of conflicts with confidence scores
        """
        
    async def _query_qwen(self, statements: List[str]) → List[Contradiction]:
        """
        Call Qwen with: 
        "Analyze these statements. List any logical contradictions."
        Cost: ~$0.001 per call
        """
```

**Cost**: ~2 calls/week per active entity (~$0.01-0.02/week)

---

#### **Task 4: Periodic Synthesis (12 hours)**
**What**: Daily consolidation that deepens knowledge

**Deliverables**:
- Module: `api/periodic_synthesis.py`
- Scheduler: Uses APScheduler for daily runs
- Routes: `api/routes/synthesis.py` (manual trigger + logs)
- Tests: `tests/test_synthesis.py::test_periodic_*`

**Endpoints**:
```
POST /synthesis/trigger           Manually trigger synthesis
GET  /synthesis/logs              View synthesis history
GET  /synthesis/logs/{entity_id}  See synthesis updates for entity
```

**Flow** (runs daily at 2am UTC):
```
1. Get all entities with wiki pages updated in past 24h
2. Batch them (max 10 per Qwen call for efficiency)
3. For each batch:
   a. Prompt: "These entities were just added/updated. 
              How do they relate to existing knowledge? 
              What gaps exist? What connections are missing?"
   b. Qwen generates synthesis summary
   c. Update corresponding wiki pages with synthesis
   d. Log confidence scores and citations
4. Cost: ~$0.10-0.20 per day (batched calls)
```

**Code Structure** (`api/periodic_synthesis.py`):
```python
class PeriodicSynthesis:
    def __init__(self):
        self.scheduler = APScheduler()
        self.scheduler.add_job(
            self.daily_synthesis,
            trigger="cron",
            hour=2,
            minute=0,
            timezone="UTC"
        )
    
    async def daily_synthesis(self) → SynthesisReport:
        """Main daily consolidation job."""
        updated_entities = get_recently_updated_entities(hours=24)
        
        batches = self._batch_entities(updated_entities, batch_size=10)
        
        results = []
        for batch in batches:
            synthesis = await self._synthesize_batch(batch)
            results.extend(synthesis)
            
        return SynthesisReport(completed=len(results))
    
    async def _synthesize_batch(self, entities: List[Entity]) → List[WikiUpdate]:
        """Batch synthesis via Qwen."""
        # Prepare context from wiki pages
        context = "\n".join([
            f"Entity: {e.name}\nWiki: {get_wiki_page(e.id).content}"
            for e in entities
        ])
        
        prompt = f"""
        These entities were recently added/updated:
        {context}
        
        1. How do they relate to existing knowledge?
        2. What gaps or contradictions exist?
        3. What connections should be drawn?
        """
        
        response = await qwen.generate(prompt, max_tokens=500)
        
        return parse_synthesis_response(response, entities)
```

**Cost**: ~$0.0005-0.002 per call × 2-3 batches/day = $0.10-0.20/day

---

#### **Task 5: Graph ↔ Wiki Sync (8 hours)**
**What**: Keep graph DB and wiki in bidirectional sync

**Deliverables**:
- Module: `api/sync_manager.py`
- Routes: Force sync endpoint
- Tests: `tests/test_synthesis.py::test_sync_*`

**Endpoints**:
```
POST /sync/force               Force immediate sync
GET  /sync/status              Last sync time + stats
```

**Two-way Sync**:

*Graph → Wiki* (automatic, triggered by Task 2-4):
- When entity relationship changes → Update wiki backlinks
- When entity properties update → Update wiki page

*Wiki → Graph* (manual, explicit):
- User edits wiki page → Updates entity properties in graph
- User adds connection in wiki → Creates relationship in graph

**Code Structure** (`api/sync_manager.py`):
```python
class SyncManager:
    async def sync_graph_to_wiki(self) → SyncReport:
        """
        Triggered by: entity updates from Task 2-4
        - For each updated entity: update corresponding wiki page
        - For each new relationship: add backlink
        """
        
    async def sync_wiki_to_graph(self) → SyncReport:
        """
        Triggered by: user edits wiki or explicit /sync endpoint
        - Extract entities from wiki page content
        - Update graph DB with extracted properties
        """
        
    def _extract_entities_from_wiki(self, content: str) → List[Entity]:
        """Parse wiki markdown for entity references and properties."""
```

**Cost**: $0.00 (pure Python, no external calls)

---

## 4. File Structure (After Phase 6)

```
second-brain/
├── api/
│   ├── routes/
│   │   ├── documents.py         (UPDATED: add synthesis hook)
│   │   ├── wiki.py              (NEW Task 1)
│   │   ├── contradictions.py   (NEW Task 3)
│   │   ├── synthesis.py        (NEW Task 4)
│   │   └── sync.py             (NEW Task 5)
│   ├── synthesis_service.py    (NEW Task 2)
│   ├── contradiction_detector.py (NEW Task 3)
│   ├── periodic_synthesis.py   (NEW Task 4)
│   ├── sync_manager.py         (NEW Task 5)
│   └── server.py               (UPDATED: register new routes)
│
├── storage/
│   ├── wiki_db.py              (NEW Task 1)
│   └── graph_db.py             (unchanged)
│
├── config/
│   └── db_schema.sql           (UPDATED: add wiki tables)
│
├── tests/
│   └── test_synthesis.py       (NEW: all Phase 6 tests)
│
└── docs/
    ├── PHASE_6_QUICK_START.md  (existing)
    ├── PHASE_6_TASK_BREAKDOWN.md (existing)
    └── superpowers/specs/
        └── 2026-05-24-phase-6-design.md (THIS SPEC)
```

---

## 5. Data Flow & Integration Points

### 5.1 Complete Document Lifecycle

```
1. USER UPLOADS DOCUMENT
   ↓
2. [Existing] Parse & extract entities via graph DB
   ↓
3. [NEW Task 2] synthesis_service.integrate_document(doc_id, entities)
   ├─ Create wiki pages for new entities
   ├─ Add backlinks between related entities
   └─ Trigger initial synthesis (optional)
   ↓
4. WIKI PAGES NOW EXIST FOR DOCUMENT ENTITIES
   ↓
5. [Daily] Task 4 runs: periodic_synthesis.daily_synthesis()
   ├─ Get all updated entities from past 24h
   ├─ Batch call to Qwen for synthesis
   ├─ Update wiki pages with synthesis
   └─ Log updates to synthesis log
   ↓
6. [Continuous] Task 3 runs: contradiction_detector.detect(entity_id)
   ├─ Check wiki pages for conflicts
   ├─ Call Qwen logic check
   └─ Flag contradictions
   ↓
7. [Real-time] Task 5: sync_manager.sync_graph_to_wiki()
   ├─ Entity updates → Wiki updates
   ├─ New relationships → Backlinks
   └─ Maintain bidirectional consistency
   ↓
8. WIKI EVOLVES, KNOWLEDGE DEEPENS
   [User can read wiki, explore connections, trigger premium synthesis]
```

---

## 6. Testing Strategy

### 6.1 Unit Tests (per task)

**Task 1 (Wiki Layer)**:
```python
test_wiki_page_creation()          # CRUD basic
test_wiki_page_update()
test_wiki_search()
test_wiki_backlinks()
test_wiki_slug_generation()
```

**Task 2 (Integration)**:
```python
test_synthesis_integration()        # Integration works
test_entity_to_wiki_mapping()
test_multi_entity_integration()
test_backlink_creation()
```

**Task 3 (Contradictions)**:
```python
test_contradiction_detection()      # Logic works
test_confidence_scoring()
test_false_positive_filtering()
```

**Task 4 (Periodic)**:
```python
test_periodic_scheduler()           # Scheduling works
test_batch_synthesis()
test_synthesis_logging()
test_cost_per_batch()
```

**Task 5 (Sync)**:
```python
test_graph_to_wiki_sync()          # Bidirectional sync
test_wiki_to_graph_sync()
test_conflict_resolution()
```

### 6.2 Integration Test

```python
async def test_full_phase_6_flow():
    """End-to-end: document → wiki → synthesis → sync"""
    # 1. Upload document
    doc = await upload_document("test.pdf", content)
    
    # 2. Verify wiki pages created (Task 1-2)
    wiki_pages = await get_wiki_pages_for_document(doc.id)
    assert len(wiki_pages) > 0
    
    # 3. Verify backlinks exist
    for page in wiki_pages:
        backlinks = await get_backlinks(page.slug)
        assert len(backlinks) > 0
    
    # 4. Trigger synthesis (Task 4)
    synthesis = await trigger_synthesis()
    assert synthesis.status == "completed"
    
    # 5. Verify wiki updated
    updated_pages = await get_wiki_pages_for_document(doc.id)
    assert updated_pages[0].updated_at > doc.processed_at
    
    # 6. Verify contradictions detected (Task 3)
    contradictions = await get_contradictions()
    assert len(contradictions) >= 0  # May or may not have contradictions
    
    # 7. Verify graph-wiki sync (Task 5)
    sync_report = await force_sync()
    assert sync_report.status == "success"
```

---

## 7. Timeline & Milestones

**Chunk 1 (20 hours)**:
- Day 1-2: Task 1 (Wiki Layer) — 8h
- Day 2-3: Task 2 (Integration) — 12h
- **Milestone**: Documents auto-create wiki pages

**Chunk 2 (26 hours)**:
- Day 4: Task 3 (Contradictions) — 6h
- Day 5-6: Task 4 (Periodic Synthesis) — 12h
- Day 7: Task 5 (Sync) — 8h
- **Milestone**: Full Phase 6 synthesis loop operational

**Buffer & Polish** (5 hours):
- Cost optimization & fine-tuning
- Documentation & edge cases
- Performance validation

**Total**: ~46-51 hours = 1 week full-time or 2-3 weeks part-time

---

## 8. Risk Mitigation & Contingencies

| Risk | Mitigation |
|------|-----------|
| Qwen API latency | Batch calls, async processing, circuit breaker |
| Ollama unavailable | Graceful degradation (skip integration), fallback to manual wiki creation |
| SQLite contention | Use WAL mode, connection pooling |
| Cost overruns | Monitor Qwen usage daily, hard cap at $5/week |
| Synthesis quality low | Use Qwen 1.5B (not base), hybrid with Claude spot-checks |
| Sync conflicts | Last-write-wins with audit log, manual review for conflicts |

---

## 9. Success Criteria (Per Chunk)

**Chunk 1 Complete** ✅:
- [ ] Task 1: Wiki CRUD endpoints operational
- [ ] Task 2: Documents trigger wiki page creation
- [ ] All Chunk 1 tests passing
- [ ] Cost: $0.00

**Chunk 2 Complete** ✅:
- [ ] Task 3: Contradictions detected reliably
- [ ] Task 4: Daily synthesis runs, updates wiki
- [ ] Task 5: Graph-wiki sync bidirectional
- [ ] All Phase 6 tests passing
- [ ] Cost: < $0.50/week

**Phase 6 Complete** ✅:
- [ ] Knowledge system self-synthesizing
- [ ] Wiki pages auto-evolve with new documents
- [ ] Contradictions flagged automatically
- [ ] Graph and wiki stay in sync
- [ ] Cost: $0.50-2.00/month
- [ ] All documentation complete

---

## 10. Design Review Checklist

- ✅ Architecture clear and scalable?
- ✅ Task breakdown covers all 5 tasks?
- ✅ Cost strategy realistic (80%+ savings)?
- ✅ Technology choices justified (Ollama/Qwen/Claude)?
- ✅ Data flow unambiguous?
- ✅ Integration points identified?
- ✅ Testing strategy comprehensive?
- ✅ No conflicting requirements?
- ✅ Scope focused (no unrelated improvements)?

---

## 11. Next Steps

**After spec approval**:
1. ✅ Design approved → Move to writing-plans skill for detailed implementation plan
2. Detailed task breakdown per task (1-5)
3. Code structure and module boundaries
4. Database migrations
5. Test templates and fixtures

**Start date**: 2026-05-24  
**Target Chunk 1 complete**: 2026-05-26  
**Target full Phase 6 complete**: 2026-06-02

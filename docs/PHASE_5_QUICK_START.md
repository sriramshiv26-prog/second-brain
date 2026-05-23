# Phase 5: Quick Start Guide for Windows GPU Machine

This guide helps you quickly resume Phase 5 work on your Windows GPU machine after cloning the repository.

---

## Prerequisites

- Windows 10/11 with GPU (RTX 5060 Ti or similar)
- Python 3.10+ installed
- Ollama running with models cached
- Git configured
- Claude Code or text editor ready

---

## Initial Setup (First Time Only)

### 1. Clone Repository

```bash
git clone https://github.com/sriramshiv26-prog/second-brain.git
cd second-brain
```

### 2. Create Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# Verify activation (should show (venv) in prompt)
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Ollama Models

```bash
# In separate terminal, ensure Ollama is running
ollama serve

# In another terminal, check available models
ollama list

# Required models:
# - nomic-embed-text-v1.5 (embeddings)
# - qwen2.5-coder (entity extraction)
```

### 5. Run Baseline Tests

```bash
# Verify Phase 1-4 works
pytest tests/ -v

# Should show 76+ passing tests
```

---

## Quick Start Checklist

- [ ] Cloned repository to Windows machine
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Ollama running with required models
- [ ] Baseline tests passing (76+ tests)
- [ ] Read PHASE_5_DETAILED_ROADMAP.md (full context)
- [ ] Read PHASE_5_TASK_BREAKDOWN.md (implementation details)

---

## Phase 5 Structure

```
Second Brain Phase 5 (24-32 hours total)
│
├─ Part 1: Backend Integration (8-12h, Tasks 1-5)
│  ├─ Task 1: Analytics Database Queries (3h)
│  ├─ Task 2: Export/Import Integration (2.5h)
│  ├─ Task 3: Document Processing (2h)
│  ├─ Task 4: Graph API Queries (2h)
│  └─ Task 5: Caching & Performance (2.5h)
│
├─ Part 2: Frontend Enhancement (6-8h, Tasks 6-9)
│  ├─ Task 6: Analytics Dashboard (3h)
│  ├─ Task 7: Export/Import UI (2h)
│  ├─ Task 8: Search UI Enhancements (1.5h)
│  └─ Task 9: Navigation & Settings (1h)
│
└─ Part 3: Extensibility (8-12h, Tasks 10-12)
   ├─ Task 10: Integration Framework (3h)
   ├─ Task 11: Plugin Framework (2.5h)
   └─ Task 12: PWA Mobile Support (2h)
```

---

## Task 1: Analytics Database Queries (3h)

### Quick Reference

**Files to modify**:
1. `config/db_schema.sql` — Add 3 new tables (search_queries, user_sessions, api_metrics)
2. `storage/graph_db.py` — Add 12 new query methods
3. `api/routes/analytics.py` — Update endpoints to use real data

**Files to create**:
1. `api/analytics_service.py` — New AnalyticsService class

**Tests to create**:
1. `tests/test_analytics_service.py`

### Implementation Steps

1. **Update DB Schema** (10 min)
   - Add 3 new tables to `config/db_schema.sql`
   - Create indexes for performance

2. **Add Query Methods to GraphDB** (60 min)
   - Implement 12 methods in `storage/graph_db.py`
   - Focus on aggregation queries (COUNT, AVG, GROUP BY)

3. **Create Analytics Service** (40 min)
   - Create `api/analytics_service.py`
   - Implement AnalyticsService class with caching
   - Methods for each analytics endpoint

4. **Update Analytics Routes** (10 min)
   - Modify `api/routes/analytics.py`
   - Replace stub returns with service calls

5. **Write Tests** (20 min)
   - Create `tests/test_analytics_service.py`
   - Test each query method

### Command Checklist

```bash
# 1. Check current status
pytest tests/test_auth.py -v  # baseline should pass

# 2. Run after implementation
pytest tests/test_analytics_service.py -v

# 3. Verify API import
python -c "from api.routes.analytics import router; print('OK')"

# 4. Commit
git add api/analytics_service.py api/routes/analytics.py storage/graph_db.py config/db_schema.sql tests/test_analytics_service.py
git commit -m "Phase 5 Task 1: Analytics database queries and aggregation service"
git push origin main
```

---

## Task 2: Export/Import Integration (2.5h)

### Quick Reference

**Files to create**:
1. `api/export_service.py` — New ExportService class

**Files to modify**:
1. `api/routes/export.py` — Connect to service

**Tests to create**:
1. `tests/test_export_service.py`

### Implementation Steps

1. **Create Export Service** (90 min)
   - JSON export (entities, relationships, graph)
   - CSV export
   - Full backup (gzipped)
   - Import with deduplication

2. **Update Export Routes** (20 min)
   - Replace stubs with service calls
   - Add file download support

3. **Write Tests** (20 min)
   - Test each export format
   - Test import deduplication

### Command Checklist

```bash
pytest tests/test_export_service.py -v
python -c "from api.export_service import get_export_service; print('OK')"
git add api/export_service.py api/routes/export.py tests/test_export_service.py
git commit -m "Phase 5 Task 2: Export/import service with JSON, CSV, and backup support"
git push origin main
```

---

## Task 3: Document Processing (2h)

### Quick Reference

**Files to create**:
1. `api/document_processor.py` — New DocumentProcessor class

**Files to modify**:
1. `api/routes/documents.py` — Connect to processor

### Implementation Steps

1. **Create Document Processor** (80 min)
   - Orchestrate: parse → embed → extract → link
   - Async processing pipeline
   - Error handling and status tracking

2. **Update Document Routes** (20 min)
   - Upload endpoint: queue for processing
   - Process endpoint: trigger pipeline
   - Status endpoint: check progress

### Command Checklist

```bash
pytest tests/test_phase2_integration.py::TestDocumentAPI -v
python -c "from api.document_processor import get_document_processor; print('OK')"
git add api/document_processor.py api/routes/documents.py
git commit -m "Phase 5 Task 3: Document processing pipeline with entity extraction"
git push origin main
```

---

## Task 4: Graph API Queries (2h)

### Quick Reference

**Files to modify**:
1. `storage/graph_db.py` — Add missing query methods
2. `api/routes/graph.py` — Fix import and use new methods

### Key Methods to Add

```python
def get_entity(self, entity_id: str) -> dict
def traverse_graph(self, entity_id: str, depth: int) -> dict
def search_entities(self, query: str) -> list
def get_entity_relationships(self, entity_id: str) -> list
```

### Command Checklist

```bash
pytest tests/test_phase2_integration.py::TestGraphAPI -v
git add storage/graph_db.py api/routes/graph.py
git commit -m "Phase 5 Task 4: Graph database query methods and entity traversal"
git push origin main
```

---

## Task 5: Caching & Performance (2.5h)

### Quick Reference

**Files to modify**:
1. `api/cache.py` — Enhance caching decorator
2. All route files — Add cache decorators to endpoints

### Caching Strategy

```python
# Analytics: 1 hour cache (analytics/*)
@cache(ttl=3600)

# Export: 30 min cache (export/*)
@cache(ttl=1800)

# Search: 5 min cache
@cache(ttl=300)

# Graph: 30 min cache
@cache(ttl=1800)
```

### Command Checklist

```bash
pytest tests/test_cache.py -v
git add api/cache.py api/routes/*.py
git commit -m "Phase 5 Task 5: Caching layer with TTL and pattern-based invalidation"
git push origin main
```

---

## After Backend Tasks (End of Week 1)

**Status**: Backend integration complete
- [ ] All 5 backend tasks done
- [ ] 90+ endpoint tests passing
- [ ] API loads 55+ routers
- [ ] Web build succeeds

**Next**: Move to Part 2 (Frontend) or Part 3 (Extensibility)

---

## Important Commands

### During Development

```bash
# Check if code imports
python -c "from api.server import app; print(len(app.routes), 'routes')"

# Run specific test
pytest tests/test_analytics_service.py::test_get_overview -v

# Run with coverage
pytest tests/ --cov=api --cov=storage -v

# Format code
black api/ storage/ process/

# Type check
mypy api/analytics_service.py

# API server (for manual testing)
uvicorn api.server:app --reload
```

### Git Workflow

```bash
# After each task
git status  # see what changed
git add <files>
git commit -m "Phase 5 Task X: [description]"
git push origin main

# Check recent commits
git log --oneline -10

# Create feature branch (if needed)
git checkout -b phase5-backend
# ... work ...
git push origin phase5-backend
# Then create PR on GitHub
```

---

## Troubleshooting

### Import Errors

```bash
# Regenerate database schema
rm ~/second-brain-data/graph.db
pytest tests/test_embedding.py::test_embed_single -v

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Ollama Issues

```bash
# On Windows, ensure Ollama service is running
ollama serve

# Check if models are cached
ollama list

# Pull a model if missing
ollama pull nomic-embed-text-v1.5
ollama pull qwen2.5-coder
```

### Test Failures

```bash
# Run a single test for debugging
pytest tests/test_analytics_service.py::test_get_overview -v -s

# Check test output
pytest tests/ --tb=short  # shorter traceback

# Run only passing tests
pytest tests/ -m "not requires_api"
```

---

## When You Get Stuck

1. **Check the detailed documents**:
   - `PHASE_5_DETAILED_ROADMAP.md` — Full context and all tasks
   - `PHASE_5_TASK_BREAKDOWN.md` — Code examples and implementations

2. **Check existing code**:
   - Similar endpoints in Phase 3/4: `api/routes/*.py`
   - Database queries: `storage/graph_db.py`
   - Caching examples: `api/cache.py`

3. **Debug**:
   - Add print statements
   - Use pytest with `-s` flag to see output
   - Check database directly: `sqlite3 ~/second-brain-data/graph.db`

4. **Ask Claude**:
   - Refer to this guide + PHASE_5_DETAILED_ROADMAP.md
   - Provide full context from repo
   - Show specific error messages

---

## Estimated Timeline

**With continuous 8-hour workdays**:
- **Day 1**: Tasks 1-2 (Analytics + Export)
- **Day 2**: Tasks 3-5 (Documents + Graph + Caching)
- **Day 3**: Tasks 6-9 (Frontend)
- **Day 4**: Tasks 10-11 (Integrations + Plugins)
- **Day 5**: Task 12 (PWA) + Testing + Documentation

**Total**: ~24-32 hours over 3-4 days

---

## Next: Pick a Task

You're ready! Start with **Task 1: Analytics Database Queries**.

1. Open `PHASE_5_TASK_BREAKDOWN.md`
2. Go to **Task 1** section
3. Follow **Step 1.1** through **Step 1.5**
4. Run tests
5. Commit and push
6. Move to Task 2

Good luck! 🚀


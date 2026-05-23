# Phase 6: AI-Powered Knowledge Synthesis - Quick Start

**Inspired by**: Andrej Karpathy's "LLM Wiki" approach  
**Goal**: Transform from search-based retrieval to synthesis-driven understanding  
**Time**: 40-50 hours  
**Cost**: $0 local + $2-5 Claude Sonnet (for synthesis)  

---

## The Vision

**Current (Phases 1-5)**: 
```
Document → Parse → Extract → Store → User searches → Retrieve
```

**Phase 6**:
```
Document → Parse → Extract → FIND RELATED → LLM SYNTHESIZES → UPDATE WIKI → Knowledge deepens
```

---

## Quick Reference

### Phase 6 has 5 Tasks:

1. **Task 1: Wiki Layer** (8h) — Markdown files + database for evolving understanding
2. **Task 2: Active Integration** (12h) — Auto-update wiki when docs added
3. **Task 3: Contradiction Detection** (6h) — Flag conflicts in knowledge
4. **Task 4: Periodic Synthesis** (12h) — Daily/weekly consolidation
5. **Task 5: Graph ↔ Wiki Sync** (8h) — Keep systems in sync

---

## Step-by-Step Start

### Step 1: Understand the Vision (30 min)
```bash
# Read Karpathy article first (you already did)
# Then read this in your repo:
cat docs/PHASE_6_SYNTHESIS_ROADMAP.md | head -100

# This explains the WHAT and WHY
```

### Step 2: Check Prerequisites (15 min)

```bash
# Verify Phase 5 tests still pass
pytest tests/ -v | head -20

# Verify API loads
python -c "from api.server import app; print(len(app.routes), 'routes')"

# Verify database works
sqlite3 ~/second-brain-data/graph.db "SELECT COUNT(*) FROM entities;"
```

### Step 3: Start Task 1 (Wiki Layer) - 8 hours

**Follow these files in order**:
1. Read: `docs/PHASE_6_DETAILED_ROADMAP.md` (Part 1 section)
2. Read: `docs/PHASE_6_TASK_BREAKDOWN.md` (Task 1 section)
3. Implement: Database schema (copy SQL to `config/db_schema.sql`)
4. Implement: `storage/wiki_db.py` (copy code)
5. Implement: `api/routes/wiki.py` (copy code)
6. Test: `pytest tests/test_synthesis.py::test_wiki_page_creation -v`
7. Commit: `git commit -m "Phase 6 Task 1: Markdown wiki layer"`

**Commands**:
```bash
# After implementing Task 1
python -c "from storage.wiki_db import get_wiki_db; wiki = get_wiki_db(); print('Wiki ready')"

pytest tests/test_synthesis.py -v

git add config/db_schema.sql storage/wiki_db.py api/routes/wiki.py
git commit -m "Phase 6 Task 1: Wiki layer with markdown pages"
git push origin main
```

### Step 4: Add Wiki Router to Server (10 min)

**File**: `api/server.py` (ADD near line 75)

```python
from api.routes.wiki import router as wiki_router

# ... in the router registration section:
app.include_router(wiki_router)
```

**Test**:
```bash
python -c "from api.server import app; print(len(app.routes), 'total routes')"
# Should show 55+ routes (up from 51)

npm run build  # Verify web still builds
```

### Step 5: Task 2 - Active Integration (12 hours)

**Same pattern**:
1. Read Task 2 in PHASE_6_TASK_BREAKDOWN.md
2. Implement `api/synthesis_service.py`
3. Wire into `api/routes/documents.py` (hook after processing)
4. Test
5. Commit

**Key**: When document processed → Call synthesis_service.integrate_document()

### Step 6: Tasks 3-5 (26 more hours)

Follow same pattern for each task.

---

## Commands Cheat Sheet

```bash
# Check current phase status
pytest tests/ -v | tail -5

# Run synthesis tests
pytest tests/test_synthesis.py -v

# Check API loads
python -c "from api.server import app; print(len(app.routes))"

# Start API for manual testing
uvicorn api.server:app --reload

# Commit each task
git add <files>
git commit -m "Phase 6 Task X: [description]"
git push origin main

# Format code
black api/synthesis_service.py storage/wiki_db.py

# Type check
mypy api/synthesis_service.py
```

---

## File Structure After Phase 6

```
api/
├── routes/
│   ├── wiki.py              ← NEW Task 1
│   ├── documents.py         ← UPDATE Task 2 (wire synthesis)
│   └── ... (existing)
├── synthesis_service.py     ← NEW Task 2
├── contradiction_detector.py ← NEW Task 3
├── periodic_synthesis.py    ← NEW Task 4
├── sync_manager.py          ← NEW Task 5
└── ... (existing)

storage/
├── wiki_db.py              ← NEW Task 1
├── graph_db.py             ← UPDATE Task 5
└── ... (existing)

config/
└── db_schema.sql           ← UPDATE Task 1

tests/
└── test_synthesis.py       ← NEW Task 1+
```

---

## What Happens After Each Task

| Task | Status | What Works |
|------|--------|-----------|
| 1 | Wiki exists | Create/read/update markdown wiki pages |
| 2 | Integration | New docs auto-update wiki pages |
| 3 | Contradict | Detect conflicting information |
| 4 | Periodic | Daily synthesis consolidates knowledge |
| 5 | Sync | Graph and wiki stay in sync |

---

## Cost During Development

**Anthropic API (for Claude synthesis)**:
- Each document synthesis: ~5 Claude API calls
- Cost per call: ~$0.0001-0.001
- Per document: ~$0.005-0.05
- Per 50 documents: ~$0.25-2.50

**How to manage**:
1. Set API key: `export ANTHROPIC_API_KEY=sk-...`
2. Monitor usage in Claude dashboard
3. Use cheaper models first (Claude 3.5 Haiku) for testing
4. Switch to Opus only when needed

---

## Testing Strategy

### Unit Tests (for each task)
```python
# Task 1: Wiki creation and updates
test_wiki_page_creation()
test_wiki_page_update()
test_wiki_links()

# Task 2: Integration
test_synthesis_integration()
test_entity_synthesis()

# Task 3: Contradictions
test_contradiction_detection()

# Task 4: Periodic
test_daily_synthesis()

# Task 5: Sync
test_graph_to_wiki_sync()
test_wiki_to_graph_sync()
```

### Integration Test
```python
# Full flow test
def test_full_synthesis_flow():
    # 1. Add document
    # 2. Extract entities
    # 3. Trigger synthesis
    # 4. Verify wiki updated
    # 5. Verify graph synced
```

---

## Common Issues & Solutions

### Issue: Claude API Key Not Found
**Solution**:
```bash
export ANTHROPIC_API_KEY=sk-your-key-here
python -c "import anthropic; print('API ready')"
```

### Issue: Database Schema Error
**Solution**:
```bash
# Regenerate database
rm ~/second-brain-data/graph.db
python -m pytest tests/ -v
```

### Issue: Wiki Pages Not Updating
**Solution**:
```python
# Debug synthesis
from api.synthesis_service import get_synthesis_service
service = get_synthesis_service()
result = await service.integrate_document("test_doc", [test_entity])
print(result)
```

### Issue: Tests Failing
**Solution**:
```bash
# Run with verbose output
pytest tests/test_synthesis.py -v -s

# Check one test
pytest tests/test_synthesis.py::test_wiki_page_creation -vv
```

---

## Timeline Estimate

**With 8-hour workdays**:
- **Day 1**: Task 1 (Wiki Layer) — 8h
- **Day 2-3**: Task 2 (Integration) — 12h
- **Day 4**: Task 3 (Contradictions) + Task 4 start — 8h
- **Day 5-6**: Task 4 (Synthesis) — 12h
- **Day 7**: Task 5 (Sync) — 8h
- **Day 8**: Testing, fixes, docs — 8h

**Total**: ~50-60 hours = 1 week full-time or 2-3 weeks part-time

---

## When You're Done

Phase 6 complete = You'll have:

✅ Wiki pages that auto-evolve  
✅ Knowledge that deepens with each document  
✅ Automatic contradiction detection  
✅ Periodic synthesis consolidating understanding  
✅ Knowledge graph ↔ Wiki staying in sync  
✅ Karpathy-style "LLM Wiki" system  

**Result**: Second Brain transforms from knowledge retrieval → knowledge synthesis 🧠✨

---

## Next Session (Windows GPU Machine)

```bash
# 1. Clone latest
git clone https://github.com/sriramshiv26-prog/second-brain.git
cd second-brain

# 2. Setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 3. Verify baseline (should see 76+ passing)
pytest tests/ -v

# 4. Read Phase 6 docs
cat docs/PHASE_6_QUICK_START.md

# 5. Start Task 1
# Follow docs/PHASE_6_TASK_BREAKDOWN.md Task 1 section
```

---

## The Transformation Vision

**Before Phase 6** (what you have):
```
User: "What do I know about machine learning?"
System: [searches and returns matching documents]
```

**After Phase 6** (what you'll build):
```
System: "You've added 5 new papers on neural networks. Here's how they 
expand our understanding... These papers contradict your assumption about 
attention mechanisms. Here are the open questions. Here are key insights 
you're missing. These topics should be connected."
```

That's the power shift from retrieval to synthesis 🚀

---

**Start with Task 1. Good luck!** 

Questions? Check the detailed roadmap or task breakdown.

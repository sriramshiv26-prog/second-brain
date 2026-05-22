# Phase 2: Search & Discovery Implementation Plan

**Goal:** Build semantic search, graph querying, and web/plugin UIs on top of Phase 1 foundation.

**Scope:** Tasks 10-21 (12 tasks, ~40 hours)

**Tech Stack:** FastAPI, React, Obsidian API, SQLite, Chroma

---

## File Structure Map (New Additions)

```
~/scripts/second-brain/
├── api/
│   ├── routes/
│   │   ├── search.py                 [NEW: /search, /search/advanced endpoints]
│   │   ├── graph.py                  [NEW: /graph/entity, /graph/traverse endpoints]
│   │   └── viz.py                    [NEW: /viz/entity, /viz/relationships endpoints]
│   └── models.py                     [EXTEND: add search + graph request/response models]
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── SearchBar.jsx         [NEW: search input with suggestions]
│   │   │   ├── SearchResults.jsx     [NEW: display search results with relevance]
│   │   │   ├── EntityBrowser.jsx     [NEW: entity list + graph visualization]
│   │   │   └── GraphViewer.jsx       [NEW: relationship graph renderer]
│   │   ├── pages/
│   │   │   ├── SearchPage.jsx        [NEW: main search interface]
│   │   │   └── EntityPage.jsx        [NEW: single entity detail + relationships]
│   │   ├── services/
│   │   │   └── api.js                [NEW: API client for search/graph/viz]
│   │   ├── App.jsx                   [NEW: React router setup]
│   │   └── index.css                 [NEW: basic styling]
│   ├── package.json                  [NEW: React + dependencies]
│   └── vite.config.js                [NEW: Vite configuration]
├── plugins/
│   ├── obsidian/
│   │   ├── manifest.json             [NEW: plugin metadata]
│   │   ├── main.ts                   [NEW: plugin entry point + search integration]
│   │   └── styles.css                [NEW: plugin styles]
│   └── __init__.py
├── tests/
│   ├── test_search_api.py            [NEW: semantic search tests]
│   ├── test_graph_api.py             [NEW: graph query tests]
│   ├── test_integration_phase2.py    [NEW: end-to-end Phase 2 tests]
│   └── __init__.py
├── docs/
│   ├── PHASE_2_PLAN.md               [THIS FILE]
│   ├── API_SPEC.md                   [NEW: full API specification]
│   └── PLUGIN_DEVELOPMENT.md         [NEW: Obsidian plugin guide]
├── docker/
│   ├── Dockerfile                    [NEW: production image]
│   └── docker-compose.yml            [NEW: local dev stack]
└── deployment/
    ├── nginx.conf                    [NEW: Nginx proxy config]
    └── deploy.sh                     [NEW: deployment script]
```

---

## Phase 2 Task Breakdown

### Task 10: Semantic Search API

**Dependencies:** Phase 1 (Tasks 5-7 complete)

**Files:**
- Create: `api/routes/search.py`
- Create: `api/models.py` (extend with search models)
- Create: `tests/test_search_api.py`

**Summary:** Build `/search` and `/search/advanced` endpoints using Phase 1 embeddings and vector store.

**Steps:**

1. **Create Pydantic models for search**
   ```python
   # api/models.py
   from pydantic import BaseModel
   from typing import List, Optional

   class SearchRequest(BaseModel):
       query: str
       top_k: int = 10
       include_metadata: bool = True

   class SearchResult(BaseModel):
       doc_id: str
       title: str
       excerpt: str
       relevance_score: float
       source_type: str
       metadata: Optional[dict]

   class SearchResponse(BaseModel):
       query: str
       results: List[SearchResult]
       total_results: int
       execution_time_ms: float
   ```

2. **Create search service**
   ```python
   # api/routes/search.py
   from fastapi import APIRouter, HTTPException
   from process.embed import EmbeddingPipeline
   from storage.vector_db import VectorStore
   import time

   router = APIRouter(prefix="/search", tags=["search"])

   @router.post("/", response_model=SearchResponse)
   async def semantic_search(request: SearchRequest):
       """Semantic search across all documents."""
       start_time = time.time()
       
       try:
           pipeline = EmbeddingPipeline()
           vector_store = VectorStore()
           
           # Embed query
           query_embedding = pipeline.embed_query(request.query)
           
           # Search vector store
           results = vector_store.search(query_embedding, n_results=request.top_k)
           
           # Format response
           search_results = [
               SearchResult(
                   doc_id=r["id"],
                   title=r["metadata"].get("title", "Unknown"),
                   excerpt=r["document"][:200],
                   relevance_score=1 - r["distance"],  # Convert distance to similarity
                   source_type=r["metadata"].get("source_type", "unknown"),
                   metadata=r["metadata"] if request.include_metadata else None
               )
               for r in results
           ]
           
           elapsed = (time.time() - start_time) * 1000
           
           return SearchResponse(
               query=request.query,
               results=search_results,
               total_results=len(search_results),
               execution_time_ms=elapsed
           )
       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))
   ```

3. **Write tests**
   ```python
   # tests/test_search_api.py
   import pytest
   from fastapi.testclient import TestClient
   from api.server import app

   client = TestClient(app)

   def test_semantic_search():
       """Test basic semantic search."""
       response = client.post(
           "/search/",
           json={"query": "artificial intelligence", "top_k": 5}
       )
       assert response.status_code == 200
       data = response.json()
       assert "results" in data
       assert data["query"] == "artificial intelligence"

   def test_search_with_metadata():
       """Test search with metadata included."""
       response = client.post(
           "/search/",
           json={"query": "neural networks", "include_metadata": True}
       )
       assert response.status_code == 200
       if response.json()["results"]:
           assert "metadata" in response.json()["results"][0]
   ```

4. **Register route in FastAPI server**
   ```python
   # api/server.py (in lifespan or main)
   from api.routes import search
   app.include_router(search.router)
   ```

**Expected Output:**
- POST `/search` returns top-K semantically similar documents
- Execution time: < 500ms for 10 results
- Relevance scores: 0.0-1.0 (cosine similarity)

**Time Estimate:** 3-4 hours

---

### Task 11: Advanced Search Filters & Aggregation

**Dependencies:** Task 10

**Files:**
- Create: `api/routes/search.py` (extend)
- Create: `tests/test_search_api.py` (extend)

**Summary:** Add filters (source type, date range), faceted search, and result aggregation.

**Steps:**

1. **Extend SearchRequest model**
   ```python
   class AdvancedSearchRequest(BaseModel):
       query: str
       top_k: int = 10
       filters: Optional[dict] = None  # {"source_type": "file", "date_after": "2026-01-01"}
       facets: bool = False  # Enable aggregations
       sort_by: str = "relevance"  # or "date", "source_type"

   class SearchFacet(BaseModel):
       name: str
       counts: dict  # {"pdf": 15, "url": 8, ...}

   class AdvancedSearchResponse(SearchResponse):
       facets: Optional[List[SearchFacet]]
   ```

2. **Implement filtering logic**
   ```python
   def apply_filters(results: List[dict], filters: dict) -> List[dict]:
       """Filter search results by metadata."""
       if not filters:
           return results
       
       filtered = results
       if "source_type" in filters:
           filtered = [r for r in filtered if r["metadata"].get("source_type") == filters["source_type"]]
       if "date_after" in filters:
           filtered = [r for r in filtered if r["metadata"].get("date") >= filters["date_after"]]
       
       return filtered

   @router.post("/advanced", response_model=AdvancedSearchResponse)
   async def advanced_search(request: AdvancedSearchRequest):
       """Search with filters and aggregations."""
       # ... (same as Task 10, but apply filters)
       
       results = vector_store.search(query_embedding, n_results=request.top_k * 2)
       results = apply_filters(results, request.filters)[:request.top_k]
       
       # Compute facets if requested
       facets = None
       if request.facets:
           facets = compute_facets(results)
       
       return AdvancedSearchResponse(
           # ... (same fields as SearchResponse)
           facets=facets
       )
   ```

3. **Tests**
   ```python
   def test_search_with_filters():
       """Test search with source type filter."""
       response = client.post(
           "/search/advanced",
           json={
               "query": "machine learning",
               "filters": {"source_type": "pdf"},
               "facets": True
           }
       )
       assert response.status_code == 200
       data = response.json()
       assert all(r["source_type"] == "pdf" for r in data["results"])
       assert "facets" in data
   ```

**Time Estimate:** 2-3 hours

---

### Task 12: Graph Query API

**Dependencies:** Phase 1 (Task 7 complete)

**Files:**
- Create: `api/routes/graph.py`
- Create: `tests/test_graph_api.py`

**Summary:** Build `/graph/entity` and `/graph/traverse` endpoints for knowledge graph queries.

**Steps:**

1. **Create graph request/response models**
   ```python
   # api/models.py (extend)
   class EntityDetailRequest(BaseModel):
       entity_id: str

   class EntityDetail(BaseModel):
       id: str
       name: str
       type: str
       definition: Optional[str]
       mention_count: int
       documents: List[dict]  # [{"doc_id": "...", "title": "...", "count": 5}, ...]
       relationships: List[dict]  # [{"target": "...", "type": "relates_to"}, ...]

   class GraphTraverseRequest(BaseModel):
       entity_id: str
       depth: int = 2  # How many hops to traverse
       relationship_type: Optional[str] = None  # Filter by type

   class GraphNode(BaseModel):
       id: str
       name: str
       type: str

   class GraphEdge(BaseModel):
       source_id: str
       target_id: str
       relationship_type: str

   class GraphTraverseResponse(BaseModel):
       root_entity_id: str
       nodes: List[GraphNode]
       edges: List[GraphEdge]
       depth: int
   ```

2. **Implement graph service**
   ```python
   # api/routes/graph.py
   from fastapi import APIRouter
   from storage.graph_db import GraphDB
   from api.models import EntityDetail, GraphTraverseResponse

   router = APIRouter(prefix="/graph", tags=["graph"])

   @router.post("/entity", response_model=EntityDetail)
   async def get_entity_detail(request: EntityDetailRequest):
       """Get entity with all related documents and relationships."""
       graph = GraphDB()
       
       entity = graph.get_entity(request.entity_id)
       documents = graph.get_entity_documents(request.entity_id)
       relationships = graph.get_entity_relationships(request.entity_id)
       
       return EntityDetail(
           id=entity["id"],
           name=entity["name"],
           type=entity["type"],
           definition=entity.get("definition"),
           mention_count=entity.get("mention_count", 0),
           documents=documents,
           relationships=relationships
       )

   @router.post("/traverse", response_model=GraphTraverseResponse)
   async def traverse_graph(request: GraphTraverseRequest):
       """Traverse knowledge graph from entity up to N hops."""
       graph = GraphDB()
       
       # Breadth-first traversal
       visited = set()
       queue = [(request.entity_id, 0)]
       nodes = {}
       edges = []
       
       while queue:
           entity_id, depth = queue.pop(0)
           
           if entity_id in visited or depth > request.depth:
               continue
           
           visited.add(entity_id)
           entity = graph.get_entity(entity_id)
           nodes[entity_id] = GraphNode(
               id=entity_id,
               name=entity["name"],
               type=entity["type"]
           )
           
           relationships = graph.get_entity_relationships(entity_id)
           for rel in relationships:
               target_id = rel["id"]  # This would need schema update
               edges.append(GraphEdge(
                   source_id=entity_id,
                   target_id=target_id,
                   relationship_type=rel["relationship_type"]
               ))
               if target_id not in visited:
                   queue.append((target_id, depth + 1))
       
       return GraphTraverseResponse(
           root_entity_id=request.entity_id,
           nodes=list(nodes.values()),
           edges=edges,
           depth=request.depth
       )
   ```

3. **Tests**
   ```python
   # tests/test_graph_api.py
   def test_entity_detail():
       """Test entity detail retrieval."""
       # (Assume entity exists from Phase 1)
       response = client.post(
           "/graph/entity",
           json={"entity_id": "ent_test123"}
       )
       assert response.status_code == 200
       data = response.json()
       assert "name" in data
       assert "relationships" in data

   def test_graph_traverse():
       """Test graph traversal."""
       response = client.post(
           "/graph/traverse",
           json={"entity_id": "ent_test123", "depth": 2}
       )
       assert response.status_code == 200
       data = response.json()
       assert "nodes" in data
       assert "edges" in data
   ```

**Time Estimate:** 3-4 hours

---

### Task 13: Graph Visualization Middleware

**Dependencies:** Task 12

**Files:**
- Create: `api/routes/viz.py`
- Create: `tests/test_viz_api.py`

**Summary:** Build endpoints that return graph data optimized for D3.js/Cytoscape visualization.

**Steps:**

1. **Create viz models**
   ```python
   class VizNode(BaseModel):
       id: str
       label: str
       type: str  # Determines color/size in viz
       size: int = 10  # Based on mention count

   class VizEdge(BaseModel):
       source: str
       target: str
       label: str

   class VizGraphResponse(BaseModel):
       nodes: List[VizNode]
       edges: List[VizEdge]
       center_id: str
   ```

2. **Implement viz service**
   ```python
   # api/routes/viz.py
   from typing import List
   from fastapi import APIRouter
   from storage.graph_db import GraphDB

   router = APIRouter(prefix="/viz", tags=["visualization"])

   @router.get("/entity/{entity_id}")
   async def visualize_entity(entity_id: str):
       """Return entity neighborhood for visualization."""
       graph = GraphDB()
       
       entity = graph.get_entity(entity_id)
       relationships = graph.get_entity_relationships(entity_id)
       
       nodes = [
           VizNode(
               id=entity_id,
               label=entity["name"],
               type=entity["type"],
               size=entity.get("mention_count", 1) * 5
           )
       ]
       
       edges = []
       for rel in relationships:
           target = graph.get_entity(rel["target_entity_id"])
           nodes.append(VizNode(
               id=rel["target_entity_id"],
               label=target["name"],
               type=target["type"],
               size=target.get("mention_count", 1) * 5
           ))
           edges.append(VizEdge(
               source=entity_id,
               target=rel["target_entity_id"],
               label=rel["relationship_type"]
           ))
       
       return VizGraphResponse(
           nodes=nodes,
           edges=edges,
           center_id=entity_id
       )
   ```

3. **Tests**
   ```python
   def test_entity_visualization():
       response = client.get(f"/viz/entity/ent_test123")
       assert response.status_code == 200
       data = response.json()
       assert "nodes" in data
       assert "edges" in data
   ```

**Time Estimate:** 2 hours

---

### Task 14: React Web UI Scaffold

**Dependencies:** Task 10 (API endpoints exist)

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/index.css`
- Create: `frontend/src/services/api.js`

**Summary:** Set up React + Vite project with API client and basic routing.

**Steps:**

1. **Initialize React project**
   ```bash
   cd ~/scripts/second-brain/frontend
   npm create vite@latest . -- --template react
   npm install axios react-router-dom
   ```

2. **Create API client**
   ```javascript
   // frontend/src/services/api.js
   import axios from 'axios';

   const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

   const client = axios.create({
       baseURL: API_URL,
       timeout: 5000
   });

   export const search = async (query, topK = 10) => {
       const response = await client.post('/search/', {
           query,
           top_k: topK,
           include_metadata: true
       });
       return response.data;
   };

   export const getEntity = async (entityId) => {
       const response = await client.post('/graph/entity', {
           entity_id: entityId
       });
       return response.data;
   };

   export const traverseGraph = async (entityId, depth = 2) => {
       const response = await client.post('/graph/traverse', {
           entity_id: entityId,
           depth
       });
       return response.data;
   };
   ```

3. **Create App component**
   ```javascript
   // frontend/src/App.jsx
   import React, { useState } from 'react';
   import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
   import SearchPage from './pages/SearchPage';
   import EntityPage from './pages/EntityPage';
   import './index.css';

   function App() {
       return (
           <Router>
               <div className="app">
                   <header className="app-header">
                       <h1>Second Brain</h1>
                       <p>Semantic search + knowledge graph</p>
                   </header>
                   <Routes>
                       <Route path="/" element={<SearchPage />} />
                       <Route path="/entity/:id" element={<EntityPage />} />
                   </Routes>
               </div>
           </Router>
       );
   }

   export default App;
   ```

4. **Styling**
   ```css
   /* frontend/src/index.css */
   * {
       margin: 0;
       padding: 0;
       box-sizing: border-box;
   }

   body {
       font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
       background: #f5f5f5;
       color: #333;
   }

   .app {
       max-width: 1200px;
       margin: 0 auto;
       padding: 20px;
   }

   .app-header {
       margin-bottom: 30px;
       text-align: center;
   }

   .app-header h1 {
       font-size: 2.5em;
       margin-bottom: 10px;
   }
   ```

5. **Tests**
   ```javascript
   // frontend/src/__tests__/api.test.js (optional)
   import { describe, it, expect } from 'vitest';
   import { search } from '../services/api';

   describe('API Client', () => {
       it('should have search function', () => {
           expect(typeof search).toBe('function');
       });
   });
   ```

**Time Estimate:** 2-3 hours

---

### Task 15: Search Results Component

**Dependencies:** Task 14

**Files:**
- Create: `frontend/src/components/SearchBar.jsx`
- Create: `frontend/src/components/SearchResults.jsx`
- Create: `frontend/src/pages/SearchPage.jsx`

**Summary:** Build search interface with input and results display.

**Code Example:**
```javascript
// frontend/src/pages/SearchPage.jsx
import React, { useState } from 'react';
import SearchBar from '../components/SearchBar';
import SearchResults from '../components/SearchResults';
import { search } from '../services/api';

export default function SearchPage() {
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [query, setQuery] = useState('');

    const handleSearch = async (q) => {
        setQuery(q);
        setLoading(true);
        try {
            const data = await search(q);
            setResults(data);
        } catch (error) {
            console.error('Search failed:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="search-page">
            <SearchBar onSearch={handleSearch} />
            {loading && <p>Searching...</p>}
            {results && <SearchResults results={results} query={query} />}
        </div>
    );
}
```

**Time Estimate:** 2-3 hours

---

### Task 16: Entity Browser Component

**Dependencies:** Task 12, Task 15

**Files:**
- Create: `frontend/src/components/EntityBrowser.jsx`
- Create: `frontend/src/components/GraphViewer.jsx`
- Create: `frontend/src/pages/EntityPage.jsx`

**Summary:** Display single entity with relationships and graph visualization.

**Time Estimate:** 3-4 hours

---

### Task 17: Obsidian Plugin Scaffold

**Dependencies:** Task 10 (API endpoints exist)

**Files:**
- Create: `plugins/obsidian/manifest.json`
- Create: `plugins/obsidian/main.ts`
- Create: `plugins/obsidian/styles.css`

**Summary:** Initialize Obsidian plugin with basic manifest and API communication.

**Code Example:**
```typescript
// plugins/obsidian/main.ts
import { Plugin, PluginSettingTab, App, Setting } from 'obsidian';

interface SecondBrainSettings {
    apiUrl: string;
}

const DEFAULT_SETTINGS: SecondBrainSettings = {
    apiUrl: 'http://localhost:5000'
};

export default class SecondBrainPlugin extends Plugin {
    settings: SecondBrainSettings;

    async onload() {
        await this.loadSettings();

        this.addCommand({
            id: 'search-second-brain',
            name: 'Search Second Brain',
            callback: () => this.openSearch()
        });

        this.addSettingTab(new SecondBrainSettingTab(this.app, this));
    }

    async openSearch() {
        // Open search modal
        console.log('Opening Second Brain search...');
    }

    async loadSettings() {
        this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
    }

    async saveSettings() {
        await this.saveData(this.settings);
    }
}

class SecondBrainSettingTab extends PluginSettingTab {
    plugin: SecondBrainPlugin;

    constructor(app: App, plugin: SecondBrainPlugin) {
        super(app, plugin);
        this.plugin = plugin;
    }

    display(): void {
        const { containerEl } = this;
        containerEl.empty();

        new Setting(containerEl)
            .setName('API URL')
            .setDesc('Second Brain API server URL')
            .addText(text => text
                .setPlaceholder('http://localhost:5000')
                .setValue(this.plugin.settings.apiUrl)
                .onChange(async (value) => {
                    this.plugin.settings.apiUrl = value;
                    await this.plugin.saveSettings();
                }));
    }
}
```

**Time Estimate:** 2-3 hours

---

### Task 18: Obsidian Plugin Search Integration

**Dependencies:** Task 17

**Files:**
- Extend: `plugins/obsidian/main.ts`
- Extend: `plugins/obsidian/styles.css`

**Summary:** Add modal search interface that queries Second Brain API from within Obsidian.

**Time Estimate:** 3-4 hours

---

### Task 19: Web UI Deployment Configuration

**Dependencies:** Task 14 (React UI exists)

**Files:**
- Create: `docker/Dockerfile`
- Create: `docker/docker-compose.yml`
- Create: `deployment/nginx.conf`
- Create: `deployment/deploy.sh`

**Summary:** Docker setup, Nginx reverse proxy, deployment script.

**Time Estimate:** 2-3 hours

---

### Task 20: Phase 2 Integration Tests

**Dependencies:** All previous tasks

**Files:**
- Create: `tests/test_integration_phase2.py`

**Summary:** End-to-end tests: search → entity detail → graph traversal → visualization.

**Time Estimate:** 2-3 hours

---

### Task 21: Phase 2 Documentation

**Dependencies:** All previous tasks

**Files:**
- Create: `docs/API_SPEC.md` (full OpenAPI)
- Create: `docs/PLUGIN_DEVELOPMENT.md` (Obsidian guide)
- Create: `docs/DEPLOYMENT.md` (docker, nginx, scaling)
- Extend: `README.md` (Phase 2 additions)

**Summary:** Comprehensive API documentation, plugin development guide, deployment instructions.

**Time Estimate:** 3-4 hours

---

## Task Dependencies

```
Task 10 (Semantic Search)
    ↓
Task 11 (Search Filters) ──────────┐
    ↓                               │
Task 12 (Graph Query API)           │
    ↓                               │
Task 13 (Graph Viz)                 │
    ↓                               │
Task 14 (React Scaffold) ←──────────┘
    ↓
Task 15 (Search Component)
    ↓
Task 16 (Entity Browser)
    
Task 17 (Obsidian Scaffold)
    ↓
Task 18 (Obsidian Integration)

Task 19 (Deployment Config)

Task 20 (Integration Tests) ← depends on 10-19
Task 21 (Documentation) ← depends on 10-19
```

---

## Implementation Order

**Week 3 (API Layer):**
- Task 10: Semantic Search API
- Task 11: Search Filters
- Task 12: Graph Query API
- Task 13: Graph Visualization

**Week 4 (Frontend):**
- Task 14: React Scaffold
- Task 15: Search Results
- Task 16: Entity Browser

**Week 4-5 (Plugins + Deployment):**
- Task 17: Obsidian Scaffold
- Task 18: Obsidian Integration
- Task 19: Deployment Config

**Week 5 (Testing + Docs):**
- Task 20: Integration Tests
- Task 21: Documentation

---

## Estimated Effort

| Task | Hours | Complexity |
|------|-------|-----------|
| 10 | 3-4 | Moderate |
| 11 | 2-3 | Light |
| 12 | 3-4 | Moderate |
| 13 | 2 | Light |
| 14 | 2-3 | Light |
| 15 | 2-3 | Light |
| 16 | 3-4 | Moderate |
| 17 | 2-3 | Light |
| 18 | 3-4 | Moderate |
| 19 | 2-3 | Light |
| 20 | 2-3 | Moderate |
| 21 | 3-4 | Moderate |
| **TOTAL** | **35-42** | - |

---

## Key Architectural Decisions

1. **FastAPI Routes:** Separate modules per domain (search, graph, viz)
2. **React + Vite:** Modern, fast build tool, good for local development
3. **SQLite queries in Python:** More control than SQL in routes
4. **Obsidian Plugin:** Communicates with API server over HTTP (stateless)
5. **Docker Deployment:** Single compose file for local, adapt for production

---

## Next Steps

Once Phase 2 plan is approved:
1. Implement Tasks 10-13 (API layer) in parallel
2. Review + test API endpoints
3. Build Tasks 14-16 (React UI)
4. Integrate with Tasks 17-18 (Obsidian)
5. Deploy + test end-to-end

**Ready to start Task 10?**

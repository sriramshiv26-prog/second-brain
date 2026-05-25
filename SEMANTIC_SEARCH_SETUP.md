# Semantic Search + Hybrid Search Setup Guide

Complete guide for enabling semantic search, vector embeddings, and hybrid search in Second Brain.

---

## What You Now Have

### 1. **Semantic Search** (Concept-based)
- Finds pages about similar topics
- Works even if exact keywords don't match
- Powered by Nomic embeddings (768-dim vectors)

### 2. **Keyword Search** (Exact match)
- Finds pages with specific terms
- Uses BM25 ranking algorithm
- Fast and precise for known terms

### 3. **Hybrid Search** (Best of both)
- Combines semantic + keyword search
- Customizable weights (70% semantic, 30% keyword default)
- Returns best matches for your intent

### 4. **Related Pages**
- Find semantically similar pages
- Auto-generates "You might also like" recommendations
- No manual linking required

### 5. **Duplicate Detection**
- Find nearly identical content
- Configurable similarity threshold (default: 85%)
- Maintain knowledge base consistency

---

## Quick Start (5 minutes)

### Step 1: Install Dependencies

```bash
cd /home/adnim1/second-brain
pip install -r requirements.txt
```

This installs:
- `qdrant-client` — Vector database
- `rank-bm25` — Keyword search ranking

### Step 2: Start Your App

**Option A: In-Memory Mode (No Server Needed)**

```bash
python -m api.server
# Uses in-memory Qdrant automatically
```

**Option B: With Qdrant Server (Faster)**

```bash
# Terminal 1: Start Qdrant (Docker)
docker run -d -p 6333:6333 qdrant/qdrant

# Terminal 2: Start your app
python -m api.server
```

### Step 3: Test the API

```bash
# Hybrid search
curl -X POST "http://localhost:8000/semantic-search/hybrid" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning algorithms",
    "top_k": 5,
    "semantic_weight": 0.7,
    "keyword_weight": 0.3
  }'

# Semantic search only
curl "http://localhost:8000/semantic-search/semantic?query=data%20science&top_k=5"

# Keyword search only
curl "http://localhost:8000/semantic-search/keyword?query=neural%20networks&top_k=5"

# Find related pages
curl "http://localhost:8000/semantic-search/related/machine-learning"

# Detect duplicates
curl "http://localhost:8000/semantic-search/duplicates/data-science?threshold=0.85"
```

---

## API Endpoints

### POST `/semantic-search/hybrid`

Hybrid search combining semantic and keyword results.

**Request:**
```json
{
  "query": "your search query",
  "top_k": 10,
  "semantic_weight": 0.7,
  "keyword_weight": 0.3
}
```

**Response:**
```json
{
  "query": "your search query",
  "results": [
    {
      "doc_id": "wiki_page-123",
      "title": "Page Title",
      "content": "Page excerpt...",
      "slug": "page-slug",
      "score": 0.85,
      "search_type": "hybrid"
    }
  ],
  "total_results": 5,
  "execution_time_ms": 145.3,
  "search_type": "hybrid"
}
```

**Use When:** You want the best of both worlds - semantic understanding + exact keyword matches

---

### GET `/semantic-search/semantic`

Pure semantic search (vector similarity).

**Query Parameters:**
- `query` (required): Search terms
- `top_k` (optional, default: 10): Number of results

**Example:**
```
GET /semantic-search/semantic?query=machine%20learning&top_k=5
```

**Use When:** Looking for related topics/concepts, not exact terms

---

### GET `/semantic-search/keyword`

Pure keyword search (BM25 ranking).

**Query Parameters:**
- `query` (required): Search terms
- `top_k` (optional, default: 10): Number of results

**Example:**
```
GET /semantic-search/keyword?query=neural%20networks&top_k=5
```

**Use When:** Searching for specific topics by name

---

### GET `/semantic-search/related/{page_slug}`

Find semantically similar pages.

**Path Parameters:**
- `page_slug` (required): Wiki page ID

**Query Parameters:**
- `top_k` (optional, default: 5): Number of related pages

**Example:**
```
GET /semantic-search/related/machine-learning?top_k=5
```

**Response:**
```json
{
  "page_slug": "machine-learning",
  "related_pages": [
    {
      "doc_id": "wiki_page-456",
      "title": "Deep Learning Basics",
      "content": "...",
      "slug": "deep-learning",
      "score": 0.92,
      "search_type": "semantic"
    }
  ],
  "total_results": 3
}
```

**Use When:** Generating recommendations or finding related topics

---

### GET `/semantic-search/duplicates/{page_slug}`

Detect duplicate/similar content.

**Path Parameters:**
- `page_slug` (required): Wiki page to check

**Query Parameters:**
- `threshold` (optional, default: 0.85, range: 0-1): Similarity threshold
  - 0.85+: Very similar (likely duplicates)
  - 0.75-0.85: Similar concepts
  - 0.60-0.75: Related content
  - <0.60: Different content

**Example:**
```
GET /semantic-search/duplicates/data-science?threshold=0.85
```

**Response:**
```json
{
  "page_slug": "data-science",
  "duplicates": [
    {
      "doc_id": "wiki_page-789",
      "title": "Data Science Overview",
      "content": "...",
      "slug": "data-science-overview",
      "score": 0.91,
      "search_type": "semantic"
    }
  ],
  "total_duplicates": 1
}
```

**Use When:** Finding redundant content, maintaining consistency

---

### POST `/semantic-search/index-page`

Index a wiki page for search.

**Query Parameters:**
- `slug` (required): Unique page identifier
- `title` (required): Page title
- `content` (required): Page body content

**Example:**
```bash
curl -X POST "http://localhost:8000/semantic-search/index-page" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "slug=machine-learning&title=Machine%20Learning&content=ML%20is%20..."
```

**Response:**
```json
{
  "status": "indexed",
  "slug": "machine-learning"
}
```

**Use When:** Creating or updating wiki pages (call after update)

---

## Integration with Wiki API

### Auto-Index on Page Create

Update your wiki route handler:

```python
from api.hybrid_search_service import HybridSearchService

@router.post("/pages")
async def create_wiki_page(request: WikiPageRequest):
    # Create page in database
    page = wiki_db.create_page(
        slug=request.slug,
        title=request.title,
        content=request.content
    )

    # Index for search
    search_service = HybridSearchService()
    search_service.index_wiki_page(
        page_slug=page.slug,
        title=page.title,
        content=page.content
    )

    return page
```

### Auto-Index on Page Update

```python
@router.put("/pages/{slug}")
async def update_wiki_page(slug: str, request: WikiPageUpdate):
    # Update page
    page = wiki_db.update_page(slug, **request.dict())

    # Re-index for search
    search_service = HybridSearchService()
    search_service.index_wiki_page(
        page_slug=page.slug,
        title=page.title,
        content=page.content
    )

    return page
```

---

## How Semantic Search Works

### Embeddings (768-dimensional vectors)

```
"Machine Learning" → [0.23, -0.41, 0.78, ..., 0.12] (768 values)
"Deep Learning"    → [0.25, -0.39, 0.81, ..., 0.10] (768 values)
"Cooking recipes"  → [0.02, -0.85, 0.12, ..., 0.92] (768 values)
                                    ↑
                        Similar numbers = Similar meaning!
```

### Cosine Similarity Scoring

```
ML vs Deep Learning:  0.98 (very similar ✓)
ML vs Cooking:        0.12 (very different ✗)
```

### BM25 Ranking (Keyword Search)

```
"Machine Learning Algorithms"
↓
Tokenize: ["machine", "learning", "algorithms"]
↓
Score pages by keyword frequency + document length
↓
Rank by relevance
```

---

## Configuration

### Adjust Search Weights

For more semantic results (find related concepts):
```json
{
  "query": "your query",
  "semantic_weight": 0.9,
  "keyword_weight": 0.1
}
```

For more keyword-focused results (exact matches):
```json
{
  "query": "your query",
  "semantic_weight": 0.3,
  "keyword_weight": 0.7
}
```

### Duplicate Detection Threshold

- **0.95+**: Exact duplicates only
- **0.85-0.95**: Very similar content (default)
- **0.75-0.85**: Similar topics/sections
- **0.60-0.75**: Related content

---

## Production Deployment

### Option 1: Docker Qdrant (Recommended)

```bash
# Create persistent volume
docker volume create qdrant_storage

# Run with persistence
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -v qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

### Option 2: Qdrant Cloud

```python
from qdrant_client import QdrantClient

client = QdrantClient(
    url="https://your-cluster.qdrant.io",
    api_key="your-api-key"
)
```

### Option 3: In-Memory (Development Only)

```python
# Already configured - uses memory by default
from storage.qdrant_db import QdrantVectorStore

vs = QdrantVectorStore(use_memory=True)  # No server needed!
```

---

## Troubleshooting

### "Socket connection closed"
- Make sure Qdrant is running: `docker run -d -p 6333:6333 qdrant/qdrant`
- Or use in-memory mode: automatically falls back if server unavailable

### "Module not found: qdrant_client"
- Install: `pip install qdrant-client rank-bm25`

### "Nomic embedding failed"
- Make sure nomic is installed: `pip install nomic`
- Check internet connection (nomic downloads model on first run)

### Slow search performance
- Use Qdrant server instead of in-memory for large datasets
- Reduce `top_k` parameter
- Batch index operations

---

## Example: Complete Workflow

```python
from api.hybrid_search_service import HybridSearchService

# Initialize
service = HybridSearchService(use_memory=True)

# 1. Index pages
service.index_wiki_pages_batch([
    {
        "slug": "ml-basics",
        "title": "Machine Learning Basics",
        "content": "Machine learning is...",
        "metadata": {"category": "ML"}
    },
    {
        "slug": "deep-learning",
        "title": "Deep Learning Guide",
        "content": "Deep learning uses neural networks...",
        "metadata": {"category": "ML"}
    }
])

# 2. Hybrid search
results = service.hybrid_search(
    query="neural networks",
    top_k=5,
    semantic_weight=0.7,
    keyword_weight=0.3
)

# 3. Find related pages
related = service.find_related_pages(
    page_slug="ml-basics",
    top_k=3
)

# 4. Detect duplicates
duplicates = service.detect_duplicate_content(
    page_slug="deep-learning",
    threshold=0.85
)
```

---

## Performance Tips

1. **Batch indexing** is 10x faster than single indexing
2. **Caching** is enabled by default (5 min TTL)
3. **Qdrant server** is faster for >1000 documents
4. **In-memory mode** works great for <500 documents

---

## Next Steps

1. ✅ Install dependencies
2. ✅ Start your app
3. ✅ Call the search endpoints
4. ✅ Integrate with wiki create/update handlers
5. ✅ Monitor performance and adjust weights

Happy searching! 🔍

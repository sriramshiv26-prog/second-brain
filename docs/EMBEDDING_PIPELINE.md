# Vector Embedding Pipeline

## Overview

The embedding pipeline generates semantic vector representations of documents and search queries using the `nomic-embed-text-v1.5` model. These embeddings enable fast, semantically-aware similarity search across your knowledge base.

## Components

### EmbeddingPipeline (`process/embed.py`)

Handles all embedding operations with support for single texts, batches, and search queries.

**Key Methods:**

- **`embed_single(text: str) -> List[float]`**
  - Embeds a single document or text chunk
  - Returns 768-dimensional vector
  - Task type: `search_document`

- **`embed_batch(texts: List[str]) -> List[List[float]]`**
  - Batch embed multiple texts for efficiency
  - Returns list of 768-dimensional vectors
  - Ideal for processing parsed documents

- **`embed_query(query: str) -> List[float]`**
  - Embeds search queries for semantic matching
  - Task type: `search_query` (optimized for query matching)
  - Returns single 768-dimensional vector

- **`chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]`**
  - Splits long documents into overlapping chunks
  - 500-word chunks with 50-word overlap preserve context at boundaries
  - Prevents token limits while maintaining semantic coherence

### VectorStore (`storage/vector_db.py`)

Wrapper around Chroma vector database for persistence and retrieval.

**Key Methods:**

- **`add_embedding(doc_id, embedding, document, metadata)`**
  - Store single embedding with metadata
  - Metadata includes source type, path, date

- **`add_embeddings_batch(ids, embeddings, documents, metadatas)`**
  - Batch store multiple embeddings
  - More efficient than individual adds

- **`search(query_embedding, n_results=10) -> List[Dict]`**
  - Semantic similarity search
  - Returns top N similar documents with distance scores

- **`get_document(doc_id) -> Dict`**
  - Retrieve stored document and embedding by ID

- **`delete_document(doc_id)`**
  - Remove document from vector store

## Workflow

```
Document Text
    ↓
[EmbeddingPipeline.chunk_text]
    ↓
List of Chunks (500 words each, 50-word overlap)
    ↓
[EmbeddingPipeline.embed_batch]
    ↓
List of 768-dim Vectors
    ↓
[VectorStore.add_embeddings_batch]
    ↓
Chroma Vector DB (persistent storage)
```

## Search Workflow

```
Search Query
    ↓
[EmbeddingPipeline.embed_query]
    ↓
768-dim Query Vector
    ↓
[VectorStore.search]
    ↓
Cosine Similarity (HNSW index)
    ↓
Top-K Similar Documents
```

## Configuration

See `config/constants.py`:

```python
EMBEDDING_MODEL = "nomic-embed-text-v1.5"
EMBEDDING_DIMENSION = 768
EMBEDDING_BATCH_SIZE = 32
```

## Notes

- Embeddings use nomic's official API (requires internet)
- Chunk overlap (50 words) ensures entity names at boundaries aren't split
- Cosine similarity is preferred for semantic matching (configured in Chroma)
- Vector store uses HNSW index for fast approximate nearest neighbor search

"""Qdrant vector database wrapper for semantic search and hybrid search."""

from typing import List, Dict, Any, Optional
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from rank_bm25 import BM25Okapi
import json
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


def _string_to_int_id(doc_id: str) -> int:
    """Convert string document ID to integer for Qdrant."""
    hash_obj = hashlib.md5(doc_id.encode())
    return int(hash_obj.hexdigest(), 16) % (2**31 - 1)


class QdrantVectorStore:
    """Persistent vector database using Qdrant for semantic search and hybrid search."""

    def __init__(
        self,
        url: str = "http://localhost:6333",
        collection_name: str = "wiki_pages",
        vector_size: int = 768,
        use_memory: bool = False,
    ):
        """
        Initialize Qdrant client.

        Args:
            url: Qdrant server URL
            collection_name: Collection name in Qdrant
            vector_size: Embedding dimension (nomic-embed-text-v1.5 uses 768)
            use_memory: If True, use in-memory mode (no server needed)
        """
        try:
            if use_memory:
                logger.info("Using in-memory Qdrant (no server needed)")
                self.client = QdrantClient(":memory:")
            else:
                logger.info(f"Connecting to Qdrant at {url}")
                self.client = QdrantClient(url=url, timeout=5.0)
                # Test connection
                self.client.get_collections()
        except Exception as e:
            logger.warning(f"Failed to connect to Qdrant at {url}: {e}")
            logger.info("Falling back to in-memory mode")
            self.client = QdrantClient(":memory:")

        self.collection_name = collection_name
        self.vector_size = vector_size
        self.bm25_index = {}
        self.doc_id_map = {}

        self._ensure_collection()
        self._rebuild_bm25_index()

    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        try:
            self.client.get_collection(self.collection_name)
            logger.info(f"Collection '{self.collection_name}' already exists")
        except Exception:
            logger.info(f"Creating collection '{self.collection_name}'")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE,  # Cosine similarity for embeddings
                ),
            )

    def _rebuild_bm25_index(self):
        """Rebuild BM25 index from all documents in collection."""
        try:
            # Fetch all documents
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                limit=10000,  # Adjust as needed
            )

            documents = []
            self.doc_id_map = {}  # Map doc_id to full document

            for point in scroll_result[0]:
                doc_id = point.id
                payload = point.payload
                content = payload.get("content", "")
                title = payload.get("title", "")

                # Combine title and content for BM25
                full_text = f"{title} {content}".lower()
                documents.append(full_text.split())
                self.doc_id_map[doc_id] = payload

            if documents:
                self.bm25_index = BM25Okapi(documents)
                logger.info(f"Built BM25 index for {len(documents)} documents")
            else:
                logger.info("No documents to index for BM25")
        except Exception as e:
            logger.warning(f"Could not rebuild BM25 index: {e}")
            self.bm25_index = {}

    def add_document(
        self,
        doc_id: str,
        embedding: List[float],
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        slug: Optional[str] = None,
    ):
        """Add a document with embedding to Qdrant."""
        if metadata is None:
            metadata = {}

        payload = {
            "title": title,
            "content": content,
            "slug": slug,
            "metadata": metadata,
            "created_at": datetime.utcnow().isoformat(),
        }

        point = PointStruct(
            id=_string_to_int_id(doc_id),  # Convert string ID to int
            vector=embedding,
            payload=payload,
        )

        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point],
            )
            logger.info(f"Added document {doc_id} to Qdrant")

            # Update BM25 index
            full_text = f"{title} {content}".lower()
            self.doc_id_map[doc_id] = payload
        except Exception as e:
            logger.error(f"Failed to add document {doc_id}: {e}")
            raise

    def add_documents_batch(
        self,
        doc_ids: List[str],
        embeddings: List[List[float]],
        titles: List[str],
        contents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        slugs: Optional[List[str]] = None,
    ):
        """Batch add documents to Qdrant."""
        if metadatas is None:
            metadatas = [{} for _ in doc_ids]
        if slugs is None:
            slugs = [None] * len(doc_ids)

        points = []
        for i, (doc_id, embedding, title, content, metadata, slug) in enumerate(
            zip(doc_ids, embeddings, titles, contents, metadatas, slugs)
        ):
            payload = {
                "title": title,
                "content": content,
                "slug": slug,
                "metadata": metadata,
                "created_at": datetime.utcnow().isoformat(),
            }

            point = PointStruct(
                id=_string_to_int_id(doc_id),
                vector=embedding,
                payload=payload,
            )
            points.append(point)
            self.doc_id_map[doc_id] = payload

        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
            logger.info(f"Added {len(doc_ids)} documents to Qdrant")
        except Exception as e:
            logger.error(f"Failed to add batch: {e}")
            raise

    def semantic_search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        score_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Search using vector similarity (semantic search).

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            score_threshold: Minimum similarity score (0-1)

        Returns:
            List of documents with scores
        """
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=score_threshold,
            )

            formatted_results = [
                {
                    "doc_id": str(result.id),
                    "score": result.score,
                    "title": result.payload.get("title", ""),
                    "content": result.payload.get("content", ""),
                    "slug": result.payload.get("slug"),
                    "metadata": result.payload.get("metadata", {}),
                    "search_type": "semantic",
                }
                for result in results
            ]

            logger.info(f"Semantic search found {len(formatted_results)} results")
            return formatted_results
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def keyword_search(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search using BM25 (keyword/lexical search).

        Args:
            query: Search query string
            top_k: Number of results to return

        Returns:
            List of documents ranked by BM25 score
        """
        if not self.bm25_index or not self.doc_id_map:
            logger.warning("BM25 index is empty")
            return []

        try:
            query_tokens = query.lower().split()
            scores = self.bm25_index.get_scores(query_tokens)

            # Get top-k by score
            scored_docs = [
                (doc_id, float(score))
                for doc_id, score in enumerate(scores)
                if score > 0
            ]
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            top_docs = scored_docs[:top_k]

            results = []
            for doc_id, score in top_docs:
                if doc_id in self.doc_id_map:
                    payload = self.doc_id_map[doc_id]
                    results.append({
                        "doc_id": str(doc_id),
                        "score": score,
                        "title": payload.get("title", ""),
                        "content": payload.get("content", ""),
                        "slug": payload.get("slug"),
                        "metadata": payload.get("metadata", {}),
                        "search_type": "keyword",
                    })

            logger.info(f"Keyword search found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []

    def hybrid_search(
        self,
        query: str,
        query_embedding: List[float],
        top_k: int = 10,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic and keyword search.

        Args:
            query: Search query string
            query_embedding: Query embedding vector
            top_k: Number of results to return
            semantic_weight: Weight for semantic search (0-1)
            keyword_weight: Weight for keyword search (0-1)

        Returns:
            Merged and ranked results
        """
        # Normalize weights
        total_weight = semantic_weight + keyword_weight
        semantic_weight /= total_weight
        keyword_weight /= total_weight

        # Get results from both searches
        semantic_results = self.semantic_search(query_embedding, top_k * 2)
        keyword_results = self.keyword_search(query, top_k * 2)

        # Normalize scores to 0-1
        if semantic_results:
            max_semantic_score = max(r["score"] for r in semantic_results)
            for r in semantic_results:
                r["score"] = r["score"] / max_semantic_score if max_semantic_score > 0 else 0

        if keyword_results:
            max_keyword_score = max(r["score"] for r in keyword_results)
            for r in keyword_results:
                r["score"] = r["score"] / max_keyword_score if max_keyword_score > 0 else 0

        # Merge results by doc_id
        merged = {}

        for result in semantic_results:
            doc_id = result["doc_id"]
            merged[doc_id] = result.copy()
            merged[doc_id]["semantic_score"] = result["score"]
            merged[doc_id]["keyword_score"] = 0

        for result in keyword_results:
            doc_id = result["doc_id"]
            if doc_id in merged:
                merged[doc_id]["keyword_score"] = result["score"]
            else:
                merged[doc_id] = result.copy()
                merged[doc_id]["semantic_score"] = 0
                merged[doc_id]["keyword_score"] = result["score"]

        # Calculate combined score
        for doc_id, result in merged.items():
            combined = (
                result.get("semantic_score", 0) * semantic_weight +
                result.get("keyword_score", 0) * keyword_weight
            )
            result["score"] = combined
            result["search_type"] = "hybrid"

        # Sort and return top-k
        results = sorted(merged.values(), key=lambda x: x["score"], reverse=True)[:top_k]
        logger.info(f"Hybrid search found {len(results)} results")
        return results

    def delete_document(self, doc_id: str):
        """Delete a document from Qdrant."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[_string_to_int_id(doc_id)],
            )
            if doc_id in self.doc_id_map:
                del self.doc_id_map[doc_id]
            logger.info(f"Deleted document {doc_id}")
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        try:
            point = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[_string_to_int_id(doc_id)],
            )
            if point:
                payload = point[0].payload
                return {
                    "doc_id": str(point[0].id),
                    "title": payload.get("title"),
                    "content": payload.get("content"),
                    "slug": payload.get("slug"),
                    "metadata": payload.get("metadata"),
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            return None

    def collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            collection = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": collection.points_count,
                "vector_size": self.vector_size,
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}

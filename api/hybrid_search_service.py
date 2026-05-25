"""Hybrid search service combining semantic and keyword search for wiki pages."""

from typing import List, Dict, Any, Optional
import logging
from process.embed import EmbeddingPipeline
from storage.qdrant_db import QdrantVectorStore
from storage.wiki_db import get_wiki_db

logger = logging.getLogger(__name__)


class HybridSearchService:
    """Service for hybrid search operations on wiki pages and documents."""

    def __init__(self, use_memory: bool = True):
        """
        Initialize search service with embeddings and vector store.

        Args:
            use_memory: If True, use in-memory Qdrant (no server needed).
                       If False, connect to Qdrant at localhost:6333
        """
        self.embedder = EmbeddingPipeline()
        self.vector_store = QdrantVectorStore(
            url="http://localhost:6333",
            collection_name="wiki_pages",
            vector_size=768,
            use_memory=use_memory,
        )
        self.wiki_db = get_wiki_db()

    def index_wiki_page(
        self,
        page_slug: str,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Index a wiki page for search.

        Args:
            page_slug: Wiki page slug (unique identifier)
            title: Page title
            content: Page content/body
            metadata: Additional metadata (optional)

        Returns:
            True if successful
        """
        try:
            # Generate embedding
            doc_id = f"wiki_{page_slug}"
            embedding = self.embedder.embed_single(f"{title}\n{content}")

            # Add to vector store
            self.vector_store.add_document(
                doc_id=doc_id,
                embedding=embedding,
                title=title,
                content=content,
                slug=page_slug,
                metadata=metadata or {},
            )

            logger.info(f"Indexed wiki page: {page_slug}")
            return True
        except Exception as e:
            logger.error(f"Failed to index wiki page {page_slug}: {e}")
            return False

    def index_wiki_pages_batch(
        self,
        pages: List[Dict[str, Any]],
    ) -> int:
        """
        Index multiple wiki pages at once.

        Args:
            pages: List of page dicts with 'slug', 'title', 'content', optional 'metadata'

        Returns:
            Number of pages successfully indexed
        """
        try:
            doc_ids = []
            embeddings = []
            titles = []
            contents = []
            metadatas = []
            slugs = []

            # Prepare batch
            texts_to_embed = []
            for page in pages:
                slug = page["slug"]
                title = page["title"]
                content = page["content"]

                doc_ids.append(f"wiki_{slug}")
                titles.append(title)
                contents.append(content)
                metadatas.append(page.get("metadata", {}))
                slugs.append(slug)
                texts_to_embed.append(f"{title}\n{content}")

            # Batch embed
            embeddings = self.embedder.embed_batch(texts_to_embed)

            # Batch add to vector store
            self.vector_store.add_documents_batch(
                doc_ids=doc_ids,
                embeddings=embeddings,
                titles=titles,
                contents=contents,
                metadatas=metadatas,
                slugs=slugs,
            )

            logger.info(f"Indexed {len(pages)} wiki pages in batch")
            return len(pages)
        except Exception as e:
            logger.error(f"Failed to batch index wiki pages: {e}")
            return 0

    def semantic_search(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for wiki pages.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of matching wiki pages
        """
        try:
            # Embed query
            query_embedding = self.embedder.embed_query(query)

            # Search
            results = self.vector_store.semantic_search(
                query_embedding=query_embedding,
                top_k=top_k,
            )

            logger.info(f"Semantic search for '{query}': {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def keyword_search(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Keyword (BM25) search for wiki pages.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of matching wiki pages
        """
        try:
            results = self.vector_store.keyword_search(query=query, top_k=top_k)
            logger.info(f"Keyword search for '{query}': {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []

    def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic and keyword search.

        Args:
            query: Search query
            top_k: Number of results
            semantic_weight: Weight for semantic search (0-1)
            keyword_weight: Weight for keyword search (0-1)

        Returns:
            List of matching wiki pages ranked by combined score
        """
        try:
            # Embed query
            query_embedding = self.embedder.embed_query(query)

            # Hybrid search
            results = self.vector_store.hybrid_search(
                query=query,
                query_embedding=query_embedding,
                top_k=top_k,
                semantic_weight=semantic_weight,
                keyword_weight=keyword_weight,
            )

            logger.info(f"Hybrid search for '{query}': {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

    def find_related_pages(
        self,
        page_slug: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Find semantically similar pages to a given page.

        Args:
            page_slug: Wiki page slug
            top_k: Number of related pages to return

        Returns:
            List of related pages
        """
        try:
            # Get page content
            page = self.wiki_db.get_page(page_slug)
            if not page or not page.content:
                logger.warning(f"Page not found: {page_slug}")
                return []

            # Embed page content
            embedding = self.embedder.embed_single(f"{page.title}\n{page.content}")

            # Find similar pages
            results = self.vector_store.semantic_search(
                query_embedding=embedding,
                top_k=top_k + 1,  # +1 to exclude the page itself
            )

            # Remove the page itself from results
            results = [r for r in results if r["slug"] != page_slug][:top_k]

            logger.info(f"Found {len(results)} related pages for {page_slug}")
            return results
        except Exception as e:
            logger.error(f"Failed to find related pages for {page_slug}: {e}")
            return []

    def detect_duplicate_content(
        self,
        page_slug: str,
        threshold: float = 0.85,
    ) -> List[Dict[str, Any]]:
        """
        Find potential duplicate or near-duplicate content.

        Args:
            page_slug: Wiki page slug
            threshold: Similarity threshold (0-1), higher = stricter

        Returns:
            List of potentially duplicate pages
        """
        try:
            page = self.wiki_db.get_page(page_slug)
            if not page or not page.content:
                return []

            embedding = self.embedder.embed_single(f"{page.title}\n{page.content}")
            results = self.vector_store.semantic_search(
                query_embedding=embedding,
                top_k=100,
                score_threshold=threshold,
            )

            # Remove the page itself
            duplicates = [r for r in results if r["slug"] != page_slug]
            logger.info(f"Found {len(duplicates)} potential duplicates for {page_slug}")
            return duplicates
        except Exception as e:
            logger.error(f"Duplicate detection failed: {e}")
            return []

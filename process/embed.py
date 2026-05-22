from nomic import embed
import logging
from typing import List

logger = logging.getLogger(__name__)

class EmbeddingPipeline:
    """Generate embeddings using nomic-embed-text."""

    def __init__(self, model_name: str = "nomic-embed-text-v1.5"):
        self.model_name = model_name

    def embed_single(self, text: str) -> List[float]:
        """Embed a single text."""
        try:
            result = embed.text(
                texts=[text],
                model=self.model_name,
                task_type="search_document"
            )
            return result["embeddings"][0]
        except Exception as e:
            logger.error(f"Failed to embed text: {e}")
            raise

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts."""
        try:
            result = embed.text(
                texts=texts,
                model=self.model_name,
                task_type="search_document"
            )
            return result["embeddings"]
        except Exception as e:
            logger.error(f"Failed to embed batch: {e}")
            raise

    def embed_query(self, query: str) -> List[float]:
        """Embed a search query."""
        try:
            result = embed.text(
                texts=[query],
                model=self.model_name,
                task_type="search_query"
            )
            return result["embeddings"][0]
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            raise

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks."""
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)

        return chunks

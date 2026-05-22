import chromadb
from config.chroma_config import init_chroma
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    """Wrapper for Chroma vector database operations."""

    def __init__(self):
        self.client, self.collection = init_chroma()

    def add_embedding(self, doc_id: str, embedding: List[float], document: str, metadata: Dict[str, Any]):
        """Add a document embedding to the vector store."""
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[metadata]
        )
        logger.info(f"Added embedding for document {doc_id}")

    def add_embeddings_batch(self, ids: List[str], embeddings: List[List[float]], documents: List[str], metadatas: List[Dict]):
        """Batch add document embeddings."""
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"Added {len(ids)} embeddings in batch")

    def search(self, query_embedding: List[float], n_results: int = 10) -> List[Dict]:
        """Search for similar documents."""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        return [
            {
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "distance": results["distances"][0][i],
                "metadata": results["metadatas"][0][i]
            }
            for i in range(len(results["ids"][0]))
        ]

    def get_document(self, doc_id: str) -> Dict:
        """Get a document by ID."""
        result = self.collection.get(ids=[doc_id])
        if result["ids"]:
            return {
                "id": result["ids"][0],
                "document": result["documents"][0],
                "metadata": result["metadatas"][0]
            }
        return None

    def delete_document(self, doc_id: str):
        """Delete a document from the vector store."""
        self.collection.delete(ids=[doc_id])
        logger.info(f"Deleted document {doc_id}")

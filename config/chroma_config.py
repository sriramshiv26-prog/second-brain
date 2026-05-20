"""Chroma vector database configuration and initialization."""

import os
from pathlib import Path


def init_chroma(data_dir=None):
    """Initialize Chroma persistent client and get or create the documents collection.

    Args:
        data_dir: Optional path override for Chroma DB storage.

    Returns:
        Tuple of (client, collection).
    """
    import chromadb

    if data_dir is None:
        data_dir = os.environ.get(
            "CHROMA_DB_PATH",
            os.path.expanduser("~/second-brain-data/vectors"),
        )

    data_dir = str(Path(data_dir).expanduser())
    os.makedirs(data_dir, exist_ok=True)

    client = chromadb.PersistentClient(path=data_dir)
    collection = client.get_or_create_collection(
        name=os.environ.get("CHROMA_COLLECTION_NAME", "documents"),
        metadata={"hnsw:space": "cosine"},
    )

    return client, collection


def get_collection(client):
    """Get the documents collection from an existing Chroma client.

    Args:
        client: An initialized Chroma PersistentClient.

    Returns:
        The documents collection.
    """
    return client.get_or_create_collection(
        name=os.environ.get("CHROMA_COLLECTION_NAME", "documents"),
        metadata={"hnsw:space": "cosine"},
    )

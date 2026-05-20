"""Tests for database initialization (SQLite graph DB and Chroma vector store)."""

import sqlite3
import tempfile
import os
import sys
from pathlib import Path

import pytest

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_graph_db_initialization():
    """Create a temp DB, run init_graph_db, and verify all 4 tables exist."""
    from storage.graph_db import init_graph_db

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_graph.db")
        conn = init_graph_db(db_path=db_path)

        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = {row["name"] for row in cursor.fetchall()}

            expected_tables = {"documents", "entities", "relationships", "document_entities"}
            assert expected_tables == tables, (
                f"Expected tables {expected_tables}, got {tables}"
            )
        finally:
            conn.close()


def test_chroma_initialization():
    """Create a temp Chroma DB, add a test vector (768-dim), and verify retrieval."""
    from config.chroma_config import init_chroma

    with tempfile.TemporaryDirectory() as tmpdir:
        client, collection = init_chroma(data_dir=tmpdir)

        # Add a 768-dimensional test vector
        test_embedding = [0.1] * 768
        collection.add(
            ids=["test-doc-1"],
            embeddings=[test_embedding],
            documents=["This is a test document for the second brain."],
            metadatas=[{"source": "unit-test"}],
        )

        # Verify retrieval
        results = collection.query(
            query_embeddings=[test_embedding],
            n_results=1,
        )

        assert results is not None
        assert len(results["ids"]) == 1
        assert results["ids"][0][0] == "test-doc-1"
        assert results["documents"][0][0] == "This is a test document for the second brain."

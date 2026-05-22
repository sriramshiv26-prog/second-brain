"""SQLite graph database initialization and connection management."""

import os
import sqlite3
import json
import uuid
from pathlib import Path
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def init_graph_db(db_path=None):
    """Initialize the SQLite graph database by executing the schema SQL.

    Args:
        db_path: Optional path override for the SQLite database file.

    Returns:
        sqlite3.Connection with row_factory set to sqlite3.Row.
    """
    if db_path is None:
        db_path = os.environ.get(
            "GRAPH_DB_PATH",
            os.path.expanduser("~/second-brain-data/graph.db"),
        )

    db_path = Path(db_path).expanduser()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    schema_path = Path(__file__).parent.parent / "config" / "db_schema.sql"
    schema_sql = schema_path.read_text()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(schema_sql)
    conn.commit()

    return conn


def get_graph_db(db_path=None):
    """Return a new SQLite connection, thread-safe for use in FastAPI.

    Opens a fresh connection on each call instead of caching, ensuring
    thread-safety in async contexts.

    Args:
        db_path: Optional path override.

    Returns:
        sqlite3.Connection with row_factory set to sqlite3.Row.
    """
    return init_graph_db(db_path)


class GraphDB:
    """High-level graph database operations."""

    def __init__(self, conn=None):
        if conn is None:
            conn = get_graph_db()
        self.conn = conn

    def add_document(self, doc_id: str, source_type: str, source_path: str, title: str, content_hash: str, metadata: dict = None) -> bool:
        """Add a document to the graph."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO documents (id, source_type, source_path, title, content_hash, metadata_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (doc_id, source_type, source_path, title, content_hash, json.dumps(metadata or {}))
            )
            self.conn.commit()
            logger.info(f"Added document {doc_id}")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Document {doc_id} already exists")
            return False

    def add_or_get_entity(self, name: str, entity_type: str, definition: str = None) -> str:
        """Add entity or return existing ID."""
        cursor = self.conn.cursor()

        # Check if exists
        cursor.execute("SELECT id FROM entities WHERE LOWER(name) = LOWER(?)", (name,))
        result = cursor.fetchone()
        if result:
            return result[0]

        # Create new
        entity_id = f"ent_{uuid.uuid4().hex[:12]}"
        cursor.execute(
            """INSERT INTO entities (id, name, type, definition)
               VALUES (?, ?, ?, ?)""",
            (entity_id, name, entity_type, definition)
        )
        self.conn.commit()
        logger.info(f"Created entity {entity_id}: {name}")
        return entity_id

    def add_relationship(self, source_entity_id: str, target_entity_id: str, rel_type: str, confidence: float = 1.0) -> bool:
        """Add a relationship between entities."""
        cursor = self.conn.cursor()
        rel_id = f"rel_{uuid.uuid4().hex[:12]}"

        try:
            cursor.execute(
                """INSERT INTO relationships (id, source_entity_id, target_entity_id, relationship_type, confidence)
                   VALUES (?, ?, ?, ?, ?)""",
                (rel_id, source_entity_id, target_entity_id, rel_type, confidence)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            logger.debug(f"Relationship already exists between {source_entity_id} and {target_entity_id}")
            return False

    def link_document_to_entities(self, doc_id: str, entity_ids: List[str]):
        """Link document to extracted entities."""
        cursor = self.conn.cursor()

        for entity_id in entity_ids:
            try:
                cursor.execute(
                    """INSERT INTO document_entities (document_id, entity_id, occurrence_count)
                       VALUES (?, ?, 1)
                       ON CONFLICT(document_id, entity_id) DO UPDATE SET occurrence_count = occurrence_count + 1""",
                    (doc_id, entity_id)
                )
            except sqlite3.Error as e:
                logger.error(f"Failed to link document {doc_id} to entity {entity_id}: {e}")

        self.conn.commit()

    def get_entity_documents(self, entity_id: str, limit: int = 10) -> List[Dict]:
        """Get all documents mentioning an entity."""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT d.id, d.title, d.source_path, de.occurrence_count
               FROM documents d
               JOIN document_entities de ON d.id = de.document_id
               WHERE de.entity_id = ?
               ORDER BY de.occurrence_count DESC
               LIMIT ?""",
            (entity_id, limit)
        )

        return [dict(row) for row in cursor.fetchall()]

    def get_entity_relationships(self, entity_id: str) -> List[Dict]:
        """Get all relationships for an entity."""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT e.name, e.type, r.relationship_type
               FROM relationships r
               JOIN entities e ON r.target_entity_id = e.id
               WHERE r.source_entity_id = ?
               UNION
               SELECT e.name, e.type, r.relationship_type
               FROM relationships r
               JOIN entities e ON r.source_entity_id = e.id
               WHERE r.target_entity_id = ?""",
            (entity_id, entity_id)
        )

        return [dict(row) for row in cursor.fetchall()]

"""SQLite graph database initialization and connection management."""

import os
import sqlite3
from pathlib import Path


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

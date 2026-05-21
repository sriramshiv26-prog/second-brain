"""Health and status endpoints for the Second Brain API."""

from datetime import datetime, timezone

from fastapi import APIRouter

from api.models import HealthResponse
from storage.graph_db import get_graph_db

router = APIRouter(prefix="", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Return server health status with document and entity counts."""
    db = get_graph_db()

    documents_indexed = db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    entities_count = db.execute("SELECT COUNT(*) FROM entities").fetchone()[0]

    return HealthResponse(
        status="healthy",
        version="0.1.0",
        documents_indexed=documents_indexed,
        entities_count=entities_count,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/status")
def status():
    """Return operational status with document breakdown by source type."""
    db = get_graph_db()

    total = db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]

    by_source_rows = db.execute(
        "SELECT source_type, COUNT(*) as cnt FROM documents GROUP BY source_type"
    ).fetchall()
    by_source = {row["source_type"]: row["cnt"] for row in by_source_rows}

    entities_count = db.execute("SELECT COUNT(*) FROM entities").fetchone()[0]

    return {
        "status": "operational",
        "documents": {
            "total": total,
            "by_source": {
                "url": by_source.get("url", 0),
                "file": by_source.get("file", 0),
                "voice": by_source.get("voice", 0),
            },
        },
        "entities": entities_count,
    }

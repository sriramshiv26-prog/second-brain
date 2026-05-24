"""
Contradictions Routes - Task 3
API endpoints for detecting and managing contradictions
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from api.contradiction_detector import get_contradiction_detector
from storage.wiki_db import get_wiki_db

router = APIRouter(prefix="/contradictions", tags=["contradictions"])


class ContradictionResponse(BaseModel):
    id: str
    entity_id: str
    wiki_slug: str
    statement_a: str
    statement_b: str
    confidence: float
    reason: Optional[str] = None
    resolved: Optional[bool] = False


class ContradictionsList(BaseModel):
    total: int
    contradictions: List[ContradictionResponse]


@router.post("/detect/{entity_id}")
async def detect_contradictions(entity_id: str):
    """Detect contradictions for an entity"""
    detector = get_contradiction_detector()

    try:
        contradictions = await detector.detect(entity_id)

        return {
            "entity_id": entity_id,
            "total": len(contradictions),
            "contradictions": [
                {
                    "id": c.id,
                    "entity_id": c.entity_id,
                    "wiki_slug": c.wiki_slug,
                    "statement_a": c.statement_a,
                    "statement_b": c.statement_b,
                    "confidence": c.confidence,
                    "reason": c.reason
                }
                for c in contradictions
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to detect contradictions: {str(e)}"
        )


@router.get("/unresolved")
async def get_unresolved_contradictions(wiki_slug: Optional[str] = None):
    """Get all unresolved contradictions"""
    db = get_wiki_db()

    try:
        contradictions = db.get_unresolved_contradictions(wiki_slug)

        return {
            "wiki_slug": wiki_slug,
            "total": len(contradictions),
            "contradictions": contradictions
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve contradictions: {str(e)}"
        )


@router.post("/{contradiction_id}/resolve")
async def resolve_contradiction(
    contradiction_id: str,
    resolution_note: Optional[str] = None
):
    """Mark a contradiction as resolved"""
    db = get_wiki_db()

    try:
        conn = db._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE contradictions
            SET resolved = TRUE,
                resolved_at = CURRENT_TIMESTAMP,
                resolution_note = ?
            WHERE id = ?
        """, (resolution_note, contradiction_id))

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Contradiction not found")

        conn.commit()
        conn.close()

        return {
            "status": "resolved",
            "contradiction_id": contradiction_id,
            "resolution_note": resolution_note
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resolve contradiction: {str(e)}"
        )


@router.get("/{contradiction_id}")
async def get_contradiction(contradiction_id: str):
    """Get a specific contradiction"""
    db = get_wiki_db()

    try:
        conn = db._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM contradictions WHERE id = ?",
            (contradiction_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Contradiction not found")

        return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve contradiction: {str(e)}"
        )

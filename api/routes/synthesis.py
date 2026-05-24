"""
Synthesis Routes - Tasks 4 & 5
API endpoints for periodic synthesis and sync
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from api.periodic_synthesis import get_periodic_synthesis
from api.sync_manager import get_sync_manager

router = APIRouter(prefix="/synthesis", tags=["synthesis"])


@router.post("/trigger")
async def trigger_synthesis():
    """Manually trigger synthesis job"""
    try:
        synthesis_service = get_periodic_synthesis()
        result = await synthesis_service.daily_synthesis()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Synthesis trigger failed: {str(e)}"
        )


@router.get("/logs")
async def get_synthesis_logs(limit: int = 30):
    """Get synthesis operation history"""
    try:
        synthesis_service = get_periodic_synthesis()
        history = synthesis_service.get_synthesis_history()
        return {
            "logs": history[-limit:],
            "total": len(history)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve logs: {str(e)}"
        )


@router.post("/sync/force")
async def force_sync():
    """Force immediate bidirectional sync"""
    try:
        sync_manager = get_sync_manager()
        report = await sync_manager.force_sync()
        return {
            "status": report.status,
            "timestamp": report.timestamp,
            "graph_to_wiki_synced": report.graph_to_wiki_synced,
            "wiki_to_graph_synced": report.wiki_to_graph_synced,
            "errors": report.errors
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Sync failed: {str(e)}"
        )


@router.get("/sync/status")
async def sync_status():
    """Get current sync status"""
    try:
        sync_manager = get_sync_manager()
        return sync_manager.get_sync_status()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sync status: {str(e)}"
        )


@router.get("/sync/conflicts")
async def check_sync_conflicts():
    """Check for sync conflicts"""
    try:
        sync_manager = get_sync_manager()
        conflicts = sync_manager.check_sync_conflicts()
        return {
            "total": len(conflicts),
            "conflicts": conflicts
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check conflicts: {str(e)}"
        )


@router.post("/sync/resolve/{conflict_id}")
async def resolve_conflict(conflict_id: str, resolution: str):
    """Resolve a sync conflict"""
    if resolution not in ["prefer_graph", "prefer_wiki"]:
        raise HTTPException(
            status_code=400,
            detail="Resolution must be 'prefer_graph' or 'prefer_wiki'"
        )

    try:
        sync_manager = get_sync_manager()
        success = sync_manager.resolve_conflict(conflict_id, resolution)

        if success:
            return {"status": "resolved", "conflict_id": conflict_id}
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to resolve conflict"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Conflict resolution failed: {str(e)}"
        )

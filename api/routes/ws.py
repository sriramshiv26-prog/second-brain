"""WebSocket endpoints for real-time graph updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from api.websockets.manager import manager

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/graph/{client_id}")
async def websocket_graph_updates(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time graph updates."""
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_json()

            if data.get("action") == "subscribe":
                entity_id = data.get("entity_id")
                if entity_id:
                    manager.subscribe_to_entity(client_id, entity_id)
                    await manager.send_personal_message(
                        {
                            "type": "subscription",
                            "entity_id": entity_id,
                            "status": "subscribed",
                        },
                        client_id,
                    )

            elif data.get("action") == "unsubscribe":
                entity_id = data.get("entity_id")
                if entity_id:
                    manager.unsubscribe_from_entity(client_id, entity_id)
                    await manager.send_personal_message(
                        {
                            "type": "subscription",
                            "entity_id": entity_id,
                            "status": "unsubscribed",
                        },
                        client_id,
                    )

            elif data.get("action") == "update":
                entity_id = data.get("entity_id")
                update_data = data.get("data", {})

                update_message = {
                    "type": "entity_update",
                    "entity_id": entity_id,
                    "timestamp": str(__import__("datetime").datetime.utcnow()),
                    "data": update_data,
                }

                await manager.broadcast(update_message, entity_id=entity_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id, websocket)
        await manager.broadcast(
            {
                "type": "client_disconnected",
                "client_id": client_id,
            }
        )


@router.post("/broadcast")
async def broadcast_update(message: dict):
    """Broadcast update to all connected clients (admin only)."""
    await manager.broadcast(message)
    return {"status": "broadcast_sent"}

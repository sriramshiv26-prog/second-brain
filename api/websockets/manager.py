"""WebSocket connection manager for real-time updates."""

from typing import Dict, List, Set
from fastapi import WebSocket


class ConnectionManager:
    """Manage WebSocket connections for real-time updates."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_subscriptions: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and store WebSocket connection."""
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)

    def disconnect(self, client_id: str, websocket: WebSocket):
        """Remove WebSocket connection."""
        if client_id in self.active_connections:
            self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]

    async def broadcast(self, message: dict, entity_id: str = None):
        """Broadcast message to all connected clients."""
        for client_id, connections in self.active_connections.items():
            if entity_id:
                if client_id not in self.user_subscriptions:
                    continue
                if entity_id not in self.user_subscriptions[client_id]:
                    continue

            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

    async def send_personal_message(self, message: dict, client_id: str):
        """Send message to specific client."""
        if client_id in self.active_connections:
            for connection in self.active_connections[client_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

    def subscribe_to_entity(self, client_id: str, entity_id: str):
        """Subscribe client to entity updates."""
        if client_id not in self.user_subscriptions:
            self.user_subscriptions[client_id] = set()
        self.user_subscriptions[client_id].add(entity_id)

    def unsubscribe_from_entity(self, client_id: str, entity_id: str):
        """Unsubscribe client from entity updates."""
        if client_id in self.user_subscriptions:
            self.user_subscriptions[client_id].discard(entity_id)


# Global connection manager instance
manager = ConnectionManager()

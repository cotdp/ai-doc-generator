import json
from typing import Dict, List, Set, Any

from fastapi import WebSocket


class ConnectionManager:
    """WebSocket connection manager."""

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, task_id: str):
        """Connect a new WebSocket client.

        Args:
            websocket: The WebSocket connection
            task_id: The task ID to subscribe to
        """
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = []
        self.active_connections[task_id].append(websocket)

    def disconnect(self, websocket: WebSocket, task_id: str):
        """Disconnect a WebSocket client.

        Args:
            websocket: The WebSocket connection
            task_id: The task ID the client was subscribed to
        """
        if task_id in self.active_connections:
            if websocket in self.active_connections[task_id]:
                self.active_connections[task_id].remove(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]

    async def send_update(self, task_id: str, data: Dict[str, Any]):
        """Send an update to all clients subscribed to a task.

        Args:
            task_id: The task ID to send the update to
            data: The update data
        """
        if task_id in self.active_connections:
            disconnected_websockets = []
            for websocket in self.active_connections[task_id]:
                try:
                    await websocket.send_json(data)
                except Exception:
                    disconnected_websockets.append(websocket)
            
            # Clean up disconnected websockets
            for websocket in disconnected_websockets:
                self.disconnect(websocket, task_id)
                
    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients.

        Args:
            message: The message to broadcast
        """
        for task_id in self.active_connections:
            await self.send_update(task_id, {"message": message})


# Singleton instance
_connection_manager = None


def get_connection_manager() -> ConnectionManager:
    """Get the singleton connection manager instance.

    Returns:
        ConnectionManager: The singleton connection manager instance
    """
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from typing import Optional

from src.auth.jwt import verify_token
from src.websockets import ConnectionManager, get_connection_manager

# Create router
router = APIRouter(prefix="/ws", tags=["WebSockets"])


@router.websocket("/report/{task_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    task_id: str,
    token: Optional[str] = None
):
    """WebSocket endpoint for report generation progress updates.
    
    Args:
        websocket: WebSocket connection
        task_id: Report task ID
        token: Optional JWT token for authentication
    """
    # Get connection manager
    connection_manager = get_connection_manager()
    
    # Authenticate if token is provided
    if token:
        token_data = verify_token(token)
        if not token_data:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    
    try:
        # Connect to WebSocket
        await connection_manager.connect(websocket, task_id)
        
        # Send initial connection message
        await websocket.send_json({"status": "connected", "task_id": task_id})
        
        # Wait for messages
        while True:
            data = await websocket.receive_text()
            # Echo back the message
            await websocket.send_json({"message": f"You sent: {data}"})
            
    except WebSocketDisconnect:
        # Disconnect when client disconnects
        connection_manager.disconnect(websocket, task_id)
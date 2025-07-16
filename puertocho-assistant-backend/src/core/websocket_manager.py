import time
from typing import List, Dict, Any
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print("WebSocket client connected")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print("WebSocket client disconnected")

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            await connection.send_json(message)

    async def broadcast_status(self, status: str):
        await self.broadcast({
            "type": "status_update",
            "payload": {"status": status}
        })

    async def broadcast_hardware_status(self, status: Dict[str, Any]):
        await self.broadcast({
            "type": "hardware_status_update",
            "payload": status
        })

    async def broadcast_command(self, command: str):
        await self.broadcast({
            "type": "command_log",
            "payload": {
                "command": command,
                "timestamp": int(time.time() * 1000)
            }
        })

# Instancia única (Singleton)
websocket_manager = WebSocketManager()

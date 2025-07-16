from typing import Dict, Any

class StateManager:
    def __init__(self):
        self.assistant_status: str = "idle"
        self.hardware_status: Dict[str, Any] = {}
        # Asegurarnos de que websocket_manager se inyecta después de su creación
        self.websocket_manager = None

    def set_websocket_manager(self, manager):
        self.websocket_manager = manager

    async def set_assistant_status(self, new_status: str):
        if self.assistant_status != new_status:
            self.assistant_status = new_status
            print(f"Assistant status changed to: {new_status}")
            if self.websocket_manager:
                await self.websocket_manager.broadcast_status(new_status)

    async def set_hardware_status(self, new_status: Dict[str, Any]):
        self.hardware_status = new_status
        print(f"Hardware status updated: {new_status}")
        if self.websocket_manager:
            await self.websocket_manager.broadcast_hardware_status(new_status)

    def get_assistant_status(self) -> str:
        return self.assistant_status

    def get_hardware_status(self) -> Dict[str, Any]:
        return self.hardware_status

# Instancia única (Singleton)
state_manager = StateManager()

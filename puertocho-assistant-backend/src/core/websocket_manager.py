"""
WebSocket Manager for PuertoCho Assistant Backend
===============================================

Maneja conexiones WebSocket con el frontend, distribuyendo eventos
en tiempo real desde hardware, backend y servicios remotos.
"""

import time
import logging
import uuid
from typing import List, Dict, Any
from fastapi import WebSocket


class WebSocketManager:
    """
    Gestor de conexiones WebSocket para el frontend.
    
    Responsabilidades:
    - Gestionar conexiones múltiples del frontend
    - Distribuir eventos en tiempo real (hardware, backend, remoto)
    - Manejar comandos del frontend hacia hardware
    - Logging de conexiones y eventos
    """
    
    def __init__(self):
        self.active_connections: List[Dict[str, Any]] = []
        self.logger = logging.getLogger("websocket_manager")
    
    async def connect(self, websocket: WebSocket) -> str:
        """
        Conectar nuevo cliente WebSocket.
        
        Returns:
            connection_id: ID único de la conexión
        """
        await websocket.accept()
        
        connection_id = str(uuid.uuid4())[:8]
        connection_info = {
            "id": connection_id,
            "websocket": websocket,
            "connected_at": time.time(),
            "client_ip": websocket.client.host if websocket.client else "unknown"
        }
        
        self.active_connections.append(connection_info)
        
        self.logger.info(
            f"🌐 WebSocket client connected: {connection_id} from {connection_info['client_ip']} "
            f"(total: {len(self.active_connections)})"
        )
        
        return connection_id
    
    def disconnect(self, websocket: WebSocket):
        """Desconectar cliente WebSocket"""
        # Buscar y remover la conexión
        for i, conn in enumerate(self.active_connections):
            if conn["websocket"] == websocket:
                connection_id = conn["id"]
                client_ip = conn["client_ip"]
                self.active_connections.pop(i)
                
                self.logger.info(
                    f"🌐 WebSocket client disconnected: {connection_id} from {client_ip} "
                    f"(remaining: {len(self.active_connections)})"
                )
                break
    
    async def broadcast(self, message: Dict[str, Any]):
        """
        Enviar mensaje a todos los clientes conectados.
        
        Args:
            message: Mensaje a enviar (debe ser serializable a JSON)
        """
        if not self.active_connections:
            return
        
        # Agregar timestamp si no existe
        if "timestamp" not in message:
            message["timestamp"] = int(time.time() * 1000)
        
        message_type = message.get("type", "unknown")
        self.logger.debug(f"📡 Broadcasting to {len(self.active_connections)} clients: {message_type}")
        
        # Lista de conexiones a remover (desconectadas)
        disconnected_connections = []
        
        for conn in self.active_connections:
            try:
                await conn["websocket"].send_json(message)
            except Exception as e:
                self.logger.warning(f"❌ Failed to send to {conn['id']}: {e}")
                disconnected_connections.append(conn)
        
        # Remover conexiones desconectadas
        for conn in disconnected_connections:
            self.active_connections.remove(conn)
            self.logger.info(f"🗑️ Removed disconnected client: {conn['id']}")
    
    async def send_to_client(self, connection_id: str, message: Dict[str, Any]):
        """
        Enviar mensaje a un cliente específico.
        
        Args:
            connection_id: ID de la conexión
            message: Mensaje a enviar
        """
        for conn in self.active_connections:
            if conn["id"] == connection_id:
                try:
                    await conn["websocket"].send_json(message)
                    return True
                except Exception as e:
                    self.logger.warning(f"❌ Failed to send to {connection_id}: {e}")
                    return False
        
        self.logger.warning(f"⚠️ Connection {connection_id} not found")
        return False
    
    # ===============================================
    # MÉTODOS ESPECÍFICOS PARA DIFERENTES EVENTOS
    # ===============================================
    
    async def broadcast_unified_state(self, state: Dict[str, Any]):
        """Enviar estado unificado del sistema"""
        await self.broadcast({
            "type": "unified_state_update",
            "payload": state
        })
    
    async def broadcast_hardware_event(self, event: Dict[str, Any]):
        """Enviar evento del hardware"""
        await self.broadcast({
            "type": "hardware_event",
            "payload": event
        })
    
    async def broadcast_audio_processing(self, audio_info: Dict[str, Any]):
        """Enviar información de procesamiento de audio"""
        await self.broadcast({
            "type": "audio_processing",
            "payload": audio_info
        })
    
    async def broadcast_remote_response(self, response: Dict[str, Any]):
        """Enviar respuesta del backend remoto"""
        await self.broadcast({
            "type": "remote_response",
            "payload": response
        })
    
    async def broadcast_error(self, error: str, details: Dict[str, Any] = None):
        """Enviar notificación de error"""
        await self.broadcast({
            "type": "error",
            "payload": {
                "message": error,
                "details": details or {},
                "timestamp": int(time.time() * 1000)
            }
        })
    
    async def broadcast_metrics(self, metrics: Dict[str, Any]):
        """Enviar métricas del sistema"""
        await self.broadcast({
            "type": "metrics_update",
            "payload": metrics
        })
    
    # ===============================================
    # MÉTODOS DE COMPATIBILIDAD (CÓDIGO ANTERIOR)
    # ===============================================
    
    async def broadcast_status(self, status: str):
        """Compatibilidad: enviar estado del asistente"""
        await self.broadcast({
            "type": "status_update",
            "payload": {"status": status}
        })
    
    async def broadcast_hardware_status(self, status: Dict[str, Any]):
        """Compatibilidad: enviar estado del hardware"""
        await self.broadcast({
            "type": "hardware_status_update",
            "payload": status
        })
    
    async def broadcast_command(self, command: str):
        """Compatibilidad: enviar comando/transcripción"""
        await self.broadcast({
            "type": "command_log",
            "payload": {
                "command": command,
                "timestamp": int(time.time() * 1000)
            }
        })
    
    # ===============================================
    # INFORMACIÓN Y ESTADÍSTICAS
    # ===============================================
    
    def get_connection_count(self) -> int:
        """Obtener número de conexiones activas"""
        return len(self.active_connections)
    
    def get_connection_info(self) -> List[Dict[str, Any]]:
        """Obtener información de todas las conexiones"""
        return [
            {
                "id": conn["id"],
                "client_ip": conn["client_ip"],
                "connected_at": conn["connected_at"],
                "duration_seconds": time.time() - conn["connected_at"]
            }
            for conn in self.active_connections
        ]
    
    def is_connected(self) -> bool:
        """Verificar si hay clientes conectados"""
        return len(self.active_connections) > 0


# Instancia única (Singleton)
websocket_manager = WebSocketManager()

"""
Cliente para comunicación con el backend del asistente PuertoCho.
"""

import asyncio
import json
import logging
from typing import Optional, Callable, Dict, Any
from urllib.parse import urlparse

# Import websockets with fallback
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("⚠️ websockets no disponible - funcionalidad WebSocket deshabilitada")

from utils.logging_config import get_logger

logger = get_logger('backend_client')

class BackendClient:
    """Cliente para comunicación con el backend vía WebSocket"""
    
    def __init__(self, websocket_url: str):
        self.websocket_url = websocket_url
        self.websocket = None
        self.is_connected = False
        self.connection_task: Optional[asyncio.Task] = None
        
        # Callbacks para eventos
        self.on_message_callback: Optional[Callable] = None
        self.on_connect_callback: Optional[Callable] = None
        self.on_disconnect_callback: Optional[Callable] = None
        
        # Verificar disponibilidad de websockets
        if not WEBSOCKETS_AVAILABLE:
            logger.warning("WebSocket no disponible - cliente deshabilitado")
    
    async def connect(self) -> bool:
        """
        Conectar al backend WebSocket.
        
        Returns:
            True si la conexión fue exitosa
        """
        if not WEBSOCKETS_AVAILABLE:
            logger.warning("WebSocket no disponible - conexión omitida")
            return False
            
        try:
            logger.info(f"Conectando a backend: {self.websocket_url}")
            
            # Verificar URL válida
            parsed_url = urlparse(self.websocket_url)
            if not parsed_url.scheme in ['ws', 'wss']:
                logger.error(f"URL WebSocket inválida: {self.websocket_url}")
                return False
            
            self.websocket = await websockets.connect(self.websocket_url)
            self.is_connected = True
            
            logger.info("✅ Conectado al backend")
            
            # Llamar callback de conexión
            if self.on_connect_callback:
                await self.on_connect_callback()
            
            # Iniciar tarea de escucha
            self.connection_task = asyncio.create_task(self._listen_messages())
            
            return True
            
        except Exception as e:
            logger.error(f"Error conectando al backend: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Desconectar del backend"""
        if self.connection_task:
            self.connection_task.cancel()
            try:
                await self.connection_task
            except asyncio.CancelledError:
                pass
        
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        self.is_connected = False
        logger.info("Desconectado del backend")
        
        # Llamar callback de desconexión
        if self.on_disconnect_callback:
            await self.on_disconnect_callback()
    
    async def send_status_update(self, status: str):
        """
        Enviar actualización de estado al backend.
        
        Args:
            status: Estado actual del asistente (idle, listening, processing, error)
        """
        if not self.is_connected:
            logger.warning("No conectado al backend, no se puede enviar estado")
            return
        
        message = {
            "type": "status_update",
            "payload": {"status": status}
        }
        
        await self._send_message(message)
        logger.debug(f"Estado enviado: {status}")
    
    async def send_command_log(self, command: str):
        """
        Enviar log de comando reconocido al backend.
        
        Args:
            command: Comando reconocido
        """
        if not self.is_connected:
            logger.warning("No conectado al backend, no se puede enviar comando")
            return
        
        import time
        message = {
            "type": "command_log",
            "payload": {
                "command": command,
                "timestamp": int(time.time() * 1000)
            }
        }
        
        await self._send_message(message)
        logger.info(f"Comando enviado: {command}")
    
    async def send_wake_word_detected(self, wake_word: str):
        """
        Enviar notificación de wake word detectada.
        
        Args:
            wake_word: Wake word detectada
        """
        if not self.is_connected:
            logger.warning("No conectado al backend, no se puede enviar wake word")
            return
        
        message = {
            "type": "wake_word_detected",
            "payload": {"wake_word": wake_word}
        }
        
        await self._send_message(message)
        logger.info(f"Wake word enviada: {wake_word}")
    
    async def _send_message(self, message: Dict[str, Any]):
        """Enviar mensaje al backend"""
        try:
            if self.websocket and self.is_connected:
                await self.websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}")
            # Marcar como desconectado para intentar reconexión
            self.is_connected = False
    
    async def _listen_messages(self):
        """Escuchar mensajes del backend"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    logger.debug(f"Mensaje recibido: {data}")
                    
                    # Llamar callback de mensaje
                    if self.on_message_callback:
                        await self.on_message_callback(data)
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Error decodificando mensaje: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Conexión cerrada por el servidor")
            self.is_connected = False
        except Exception as e:
            logger.error(f"Error en escucha de mensajes: {e}")
            self.is_connected = False
    
    def set_message_callback(self, callback: Callable):
        """Configurar callback para mensajes recibidos"""
        self.on_message_callback = callback
    
    def set_connect_callback(self, callback: Callable):
        """Configurar callback para conexión establecida"""
        self.on_connect_callback = callback
    
    def set_disconnect_callback(self, callback: Callable):
        """Configurar callback para desconexión"""
        self.on_disconnect_callback = callback

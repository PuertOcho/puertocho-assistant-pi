#!/usr/bin/env python3
"""
WebSocket client for PuertoCho Assistant Hardware Service
Handles real-time communication with the backend local service.
"""

import asyncio
import json
import logging
import time
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from utils.logger import get_logger

logger = get_logger(__name__)

class MessageType(Enum):
    """Tipos de mensajes WebSocket"""
    # Eventos desde hardware (mantener solo los esenciales)
    AUDIO_CAPTURED = "audio_captured"
    STATE_CHANGED = "state_changed"
    BUTTON_EVENT = "button_event"
    HARDWARE_METRICS = "hardware_metrics"
    
    # Comandos desde backend (simplificar)
    HARDWARE_COMMAND = "hardware_command"  # Comando genérico con subtipo
    
    # Control de conexión
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    PING = "ping"
    PONG = "pong"
    HEARTBEAT = "heartbeat"

@dataclass
class WebSocketMessage:
    """Estructura de mensaje WebSocket"""
    type: str
    data: Dict[str, Any]
    timestamp: float
    request_id: Optional[str] = None
    
    def to_json(self) -> str:
        """Convertir a JSON"""
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, json_str: str) -> 'WebSocketMessage':
        """Crear desde JSON"""
        raw_data = json.loads(json_str)
        
        # Manejar diferentes formatos de mensaje del backend
        # El backend puede enviar 'payload' en lugar de 'data'
        if 'payload' in raw_data and 'data' not in raw_data:
            raw_data['data'] = raw_data.pop('payload')
        
        # Asegurar que tenemos los campos requeridos
        required_fields = {
            'type': raw_data.get('type', 'unknown'),
            'data': raw_data.get('data', {}),
            'timestamp': raw_data.get('timestamp', time.time()),
            'request_id': raw_data.get('request_id', None)
        }
        
        return cls(**required_fields)

class ConnectionState(Enum):
    """Estados de conexión WebSocket"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"

class WebSocketClient:
    """Cliente WebSocket para comunicación con backend local"""
    
    def __init__(self, ws_url: str, reconnect_interval: float = 5.0, max_reconnect_attempts: int = 0):
        """
        Inicializar cliente WebSocket
        
        Args:
            ws_url: URL del servidor WebSocket
            reconnect_interval: Intervalo inicial de reconexión en segundos
            max_reconnect_attempts: Máximo número de intentos (0 = infinito)
        """
        self.ws_url = ws_url
        self.reconnect_interval = reconnect_interval
        self.max_reconnect_attempts = max_reconnect_attempts
        
        # Estado de conexión
        self.state = ConnectionState.DISCONNECTED
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.reconnect_attempts = 0
        self.last_heartbeat = 0.0
        self.is_running = False
        
        # Callbacks para eventos
        self.message_handlers: Dict[str, List[Callable]] = {}
        self.connection_handlers: List[Callable] = []
        self.disconnection_handlers: List[Callable] = []
        
        # Queue de mensajes pendientes
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.max_queue_size = 1000
        
        # Tasks asyncio
        self.connection_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.message_processor_task: Optional[asyncio.Task] = None
        
        logger.info(f"WebSocket client initialized for {ws_url}")
    
    async def start(self):
        """Iniciar cliente WebSocket"""
        if self.is_running:
            logger.warning("WebSocket client already running")
            return
        
        self.is_running = True
        logger.info("Starting WebSocket client...")
        
        # Iniciar tareas
        self.connection_task = asyncio.create_task(self._connection_manager())
        self.heartbeat_task = asyncio.create_task(self._heartbeat_manager())
        self.message_processor_task = asyncio.create_task(self._message_processor())
        
        # Intentar conexión inicial
        await self._connect()
    
    async def stop(self):
        """Detener cliente WebSocket"""
        if not self.is_running:
            return
        
        logger.info("Stopping WebSocket client...")
        self.is_running = False
        
        # Cancelar tareas
        if self.connection_task:
            self.connection_task.cancel()
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.message_processor_task:
            self.message_processor_task.cancel()
        
        # Cerrar conexión
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        self.state = ConnectionState.DISCONNECTED
        logger.info("WebSocket client stopped")
    
    async def _connect(self) -> bool:
        """Conectar al servidor WebSocket"""
        try:
            self.state = ConnectionState.CONNECTING
            logger.info(f"Connecting to WebSocket server: {self.ws_url}")
            
            # Conectar con timeout
            self.websocket = await asyncio.wait_for(
                websockets.connect(self.ws_url), 
                timeout=10.0
            )
            
            self.state = ConnectionState.CONNECTED
            self.reconnect_attempts = 0
            self.last_heartbeat = time.time()
            
            logger.info("WebSocket connected successfully")
            
            # Notificar conexión establecida
            await self._notify_connection_handlers(True)
            
            # Enviar mensaje de conexión
            await self._send_internal_message(MessageType.CONNECT, {
                "client_id": "hardware_service",
                "timestamp": time.time()
            })
            
            return True
            
        except asyncio.TimeoutError:
            logger.error("WebSocket connection timeout")
            self.state = ConnectionState.ERROR
            return False
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            self.state = ConnectionState.ERROR
            return False
    
    async def _disconnect(self):
        """Desconectar del servidor WebSocket"""
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.debug(f"Error closing WebSocket: {e}")
            finally:
                self.websocket = None
        
        was_connected = self.state == ConnectionState.CONNECTED
        self.state = ConnectionState.DISCONNECTED
        
        if was_connected:
            await self._notify_connection_handlers(False)
            logger.info("WebSocket disconnected")
    
    async def _connection_manager(self):
        """Gestor de conexión con reconexión automática"""
        while self.is_running:
            try:
                if self.state == ConnectionState.CONNECTED and self.websocket:
                    # Escuchar mensajes entrantes
                    try:
                        message = await self.websocket.recv()
                        await self._handle_incoming_message(message)
                    except ConnectionClosed:
                        logger.warning("WebSocket connection closed by server")
                        await self._disconnect()
                    except WebSocketException as e:
                        logger.error(f"WebSocket error: {e}")
                        await self._disconnect()
                
                elif self.state in [ConnectionState.DISCONNECTED, ConnectionState.ERROR]:
                    # Intentar reconexión
                    if self._should_reconnect():
                        self.state = ConnectionState.RECONNECTING
                        logger.info(f"Attempting reconnection #{self.reconnect_attempts + 1}")
                        
                        if await self._connect():
                            continue
                        else:
                            self.reconnect_attempts += 1
                            await self._wait_for_reconnect()
                    else:
                        await asyncio.sleep(1.0)
                
                else:
                    await asyncio.sleep(0.1)
                    
            except asyncio.CancelledError:
                logger.debug("Connection manager cancelled")
                break
            except Exception as e:
                logger.error(f"Unexpected error in connection manager: {e}")
                await asyncio.sleep(1.0)
    
    def _should_reconnect(self) -> bool:
        """Determinar si debe intentar reconexión"""
        if not self.is_running:
            return False
        
        if self.max_reconnect_attempts > 0:
            return self.reconnect_attempts < self.max_reconnect_attempts
        
        return True
    
    async def _wait_for_reconnect(self):
        """Esperar antes del siguiente intento de reconexión con backoff exponencial"""
        delay = min(self.reconnect_interval * (2 ** min(self.reconnect_attempts, 6)), 60.0)
        logger.info(f"Waiting {delay:.1f}s before next reconnection attempt")
        await asyncio.sleep(delay)
    
    async def _heartbeat_manager(self):
        """Gestor de heartbeat para mantener conexión activa"""
        while self.is_running:
            try:
                if self.state == ConnectionState.CONNECTED:
                    current_time = time.time()
                    
                    # Enviar heartbeat cada 30 segundos
                    if current_time - self.last_heartbeat > 30.0:
                        await self._send_internal_message(MessageType.HEARTBEAT, {
                            "timestamp": current_time
                        })
                        self.last_heartbeat = current_time
                
                await asyncio.sleep(10.0)  # Verificar cada 10 segundos
                
            except asyncio.CancelledError:
                logger.debug("Heartbeat manager cancelled")
                break
            except Exception as e:
                logger.error(f"Error in heartbeat manager: {e}")
                await asyncio.sleep(5.0)
    
    async def _message_processor(self):
        """Procesador de cola de mensajes salientes"""
        while self.is_running:
            try:
                # Esperar mensaje en cola
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                
                if self.state == ConnectionState.CONNECTED and self.websocket:
                    try:
                        await self.websocket.send(message.to_json())
                        logger.debug(f"Sent message: {message.type}")
                    except Exception as e:
                        logger.error(f"Failed to send message: {e}")
                        # Volver a encolar si es importante
                        if message.type in [MessageType.AUDIO_CAPTURED, MessageType.BUTTON_EVENT]:
                            if self.message_queue.qsize() < self.max_queue_size:
                                await self.message_queue.put(message)
                else:
                    # Reencolar mensaje si no hay conexión
                    if self.message_queue.qsize() < self.max_queue_size:
                        await self.message_queue.put(message)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                logger.debug("Message processor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in message processor: {e}")
                await asyncio.sleep(1.0)
    
    async def _handle_incoming_message(self, message_str: str):
        """Manejar mensaje entrante del servidor"""
        try:
            message = WebSocketMessage.from_json(message_str)
            logger.debug(f"Received message: {message.type}")
            
            # Manejar mensajes internos
            if message.type == MessageType.PING.value:
                await self._send_internal_message(MessageType.PONG, message.data)
                return
            
            # Notificar handlers registrados
            handlers = self.message_handlers.get(message.type, [])
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(message)
                    else:
                        handler(message)
                except Exception as e:
                    logger.error(f"Error in message handler for {message.type}: {e}")
            
            # Handler genérico
            generic_handlers = self.message_handlers.get("*", [])
            for handler in generic_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(message)
                    else:
                        handler(message)
                except Exception as e:
                    logger.error(f"Error in generic message handler: {e}")
                    
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON message received: {e}")
        except Exception as e:
            logger.error(f"Error handling incoming message: {e}")
    
    async def _send_internal_message(self, msg_type: MessageType, data: Dict[str, Any]):
        """Enviar mensaje interno (ping, pong, heartbeat)"""
        message = WebSocketMessage(
            type=msg_type.value,
            data=data,
            timestamp=time.time()
        )
        
        if self.state == ConnectionState.CONNECTED and self.websocket:
            try:
                await self.websocket.send(message.to_json())
            except Exception as e:
                logger.error(f"Failed to send internal message {msg_type.value}: {e}")
    
    async def send_message(self, msg_type: MessageType, data: Dict[str, Any], request_id: Optional[str] = None) -> bool:
        """
        Enviar mensaje al servidor
        
        Args:
            msg_type: Tipo de mensaje
            data: Datos del mensaje
            request_id: ID opcional de request
            
        Returns:
            True si el mensaje fue encolado exitosamente
        """
        message = WebSocketMessage(
            type=msg_type.value,
            data=data,
            timestamp=time.time(),
            request_id=request_id
        )
        
        try:
            if self.message_queue.qsize() >= self.max_queue_size:
                logger.warning("Message queue full, dropping oldest message")
                try:
                    self.message_queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            
            await self.message_queue.put(message)
            return True
            
        except Exception as e:
            logger.error(f"Failed to queue message: {e}")
            return False
    
    def add_message_handler(self, message_type: str, handler: Callable):
        """Añadir handler para tipo de mensaje específico"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
        logger.debug(f"Added handler for message type: {message_type}")
    
    def remove_message_handler(self, message_type: str, handler: Callable):
        """Remover handler para tipo de mensaje específico"""
        if message_type in self.message_handlers:
            try:
                self.message_handlers[message_type].remove(handler)
                logger.debug(f"Removed handler for message type: {message_type}")
            except ValueError:
                logger.warning(f"Handler not found for message type: {message_type}")
    
    def add_connection_handler(self, handler: Callable):
        """Añadir handler para eventos de conexión/desconexión"""
        self.connection_handlers.append(handler)
    
    async def _notify_connection_handlers(self, connected: bool):
        """Notificar cambios de estado de conexión"""
        for handler in self.connection_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(connected)
                else:
                    handler(connected)
            except Exception as e:
                logger.error(f"Error in connection handler: {e}")
    
    @property
    def is_connected(self) -> bool:
        """Verificar si está conectado"""
        return self.state == ConnectionState.CONNECTED and self.websocket is not None
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Obtener información de estado de conexión"""
        return {
            "state": self.state.value,
            "url": self.ws_url,
            "connected": self.is_connected,
            "reconnect_attempts": self.reconnect_attempts,
            "queue_size": self.message_queue.qsize(),
            "last_heartbeat": self.last_heartbeat
        }

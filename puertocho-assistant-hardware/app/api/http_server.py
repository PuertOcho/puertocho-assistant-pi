"""
HTTP Server for PuertoCho Assistant Hardware Service
Provides REST API endpoints for hardware control and monitoring
"""

from fastapi import FastAPI, HTTPException, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import uvicorn
import psutil
import os
import glob
import time
import uuid
from datetime import datetime
from pathlib import Path

# Importar el StateManager existente
from core.state_manager import StateManager, AssistantState
from core.led_controller import LEDController, LEDState, LEDColor
from core.button_handler import ButtonHandler, ButtonEvent

class StateChangeRequest(BaseModel):
    """Modelo para cambiar estado manualmente"""
    state: str

class LEDPatternRequest(BaseModel):
    """Modelo para cambiar patrón de LED"""
    pattern_type: str  # 'solid', 'pulse', 'rotating', 'blink', 'rainbow'
    color: Optional[str] = None  # Color predefinido o RGB hex
    duration: Optional[float] = 1.0
    brightness: Optional[int] = None

class ButtonSimulateRequest(BaseModel):
    """Modelo para simular eventos de botón"""
    event_type: str  # 'short', 'long'
    duration: Optional[float] = None  # Duración personalizada

class HTTPServer:
    """
    Servidor HTTP para la API REST del hardware.
    Proporciona endpoints para control y monitoreo del hardware.
    """
    
    def __init__(self, state_manager: StateManager, port: int = 8080):
        self.state_manager = state_manager
        self.port = port
        self.logger = logging.getLogger("http_server")
        
        # Crear la app FastAPI
        self.app = FastAPI(
            title="PuertoCho Hardware API",
            description="REST API for hardware control and monitoring",
            version="1.0.0",
            docs_url="/docs",  # Swagger UI
            redoc_url="/redoc"  # ReDoc
        )
        
        # Configurar CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # En producción, especificar orígenes permitidos
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Configurar middleware de logging
        self._setup_logging_middleware()
        
        # Registrar endpoints
        self._register_endpoints()
    
    def _setup_logging_middleware(self):
        """Configurar middleware de logging para peticiones HTTP"""
        
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            # Generar ID único para la petición
            request_id = str(uuid.uuid4())[:8]
            
            # Registrar inicio de petición
            start_time = time.time()
            client_ip = request.client.host if request.client else "unknown"
            
            self.logger.info(
                f"🌐 HTTP Request [{request_id}]: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": client_ip,
                    "user_agent": request.headers.get("user-agent", "unknown"),
                    "event_type": "http_request_start"
                }
            )
            
            # Procesar petición
            try:
                response = await call_next(request)
                
                # Calcular tiempo de procesamiento
                process_time = time.time() - start_time
                
                # Registrar respuesta
                self.logger.info(
                    f"🌐 HTTP Response [{request_id}]: {response.status_code} in {process_time:.3f}s",
                    extra={
                        "request_id": request_id,
                        "status_code": response.status_code,
                        "process_time_seconds": round(process_time, 3),
                        "event_type": "http_request_complete"
                    }
                )
                
                # Agregar headers de respuesta
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Process-Time"] = f"{process_time:.3f}"
                
                return response
                
            except Exception as e:
                # Registrar error
                process_time = time.time() - start_time
                self.logger.error(
                    f"🌐 HTTP Error [{request_id}]: {str(e)} after {process_time:.3f}s",
                    extra={
                        "request_id": request_id,
                        "error": str(e),
                        "process_time_seconds": round(process_time, 3),
                        "event_type": "http_request_error"
                    }
                )
                raise

    def _register_endpoints(self):
        """Registrar todos los endpoints de la API"""
        
        @self.app.get("/health", 
                     summary="Health Check",
                     description="Verificar estado de salud del servicio de hardware")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "service": "puertocho-hardware",
                "version": "1.0.0",
                "hardware_state": self.state_manager.get_current_state().name
            }
        
        @self.app.get("/state", 
                     summary="Get Current State",
                     description="Obtener el estado actual del StateManager")
        async def get_state():
            """Obtener estado actual del StateManager"""
            # Usar la nueva API del StateManager refactorizado
            current_state = self.state_manager.get_current_state()
            time_in_current_state = self.state_manager.get_time_in_current_state()
            stats = self.state_manager.get_stats()
            
            return {
                "state": current_state.name,
                "timestamp": datetime.now().isoformat(),
                "time_in_current_state_seconds": time_in_current_state,
                "previous_state": self.state_manager.get_previous_state().name if self.state_manager.get_previous_state() else None,
                "stats": {
                    "total_transitions": stats["total_transitions"],
                    "current_state_duration": stats["current_state_duration"],
                    "registered_components": stats["registered_components"],
                    "component_count": stats["component_count"]
                }
            }
        
        @self.app.post("/state", 
                      summary="Change State",
                      description="Cambiar estado manualmente (para testing)")
        async def change_state(request: StateChangeRequest):
            """Cambiar estado manualmente (para testing)"""
            try:
                # Validar que el estado existe
                new_state = AssistantState[request.state.upper()]
                
                # Cambiar estado usando la nueva API
                old_state = self.state_manager.get_current_state().name
                success = self.state_manager.set_state(new_state, {
                    "source": "http_api",
                    "manual_change": True
                })
                
                if success:
                    self.logger.info(f"Manual state change: {old_state} -> {new_state.name}")
                    
                    return {
                        "success": True,
                        "old_state": old_state,
                        "new_state": new_state.name,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"State transition rejected: {old_state} -> {new_state.name}"
                    )
                
            except KeyError:
                valid_states = [state.name for state in AssistantState]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": f"Invalid state: {request.state}",
                        "valid_states": valid_states
                    }
                )
            except Exception as e:
                self.logger.error(f"Error changing state: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error changing state: {str(e)}"
                )

        # ========================
        # ENDPOINTS DE GESTIÓN DE AUDIO (HW-API-03)
        # ========================
        
        @self.app.get("/audio/capture",
                     summary="Get Latest Captured Audio",
                     description="Obtener el último archivo de audio capturado por VAD")
        async def get_latest_captured_audio():
            """Obtener último archivo de audio capturado"""
            try:
                captured_dir = Path("/app/captured_audio")
                if not captured_dir.exists():
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No captured audio directory found"
                    )
                
                # Buscar archivos WAV ordenados por fecha de modificación
                audio_files = list(captured_dir.glob("captured_*.wav"))
                
                if not audio_files:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No captured audio files found"
                    )
                
                # Obtener el más reciente
                latest_file = max(audio_files, key=lambda f: f.stat().st_mtime)
                
                # Información del archivo
                file_info = {
                    "filename": latest_file.name,
                    "path": str(latest_file),
                    "size_bytes": latest_file.stat().st_size,
                    "created_at": datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat(),
                    "download_url": f"/audio/download/{latest_file.name}"
                }
                
                return {
                    "success": True,
                    "latest_audio": file_info,
                    "total_files": len(audio_files),
                    "timestamp": datetime.now().isoformat()
                }
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error getting captured audio: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error retrieving captured audio: {str(e)}"
                )
        
        @self.app.get("/audio/download/{filename}",
                     summary="Download Audio File",
                     description="Descargar un archivo de audio específico")
        async def download_audio_file(filename: str):
            """Descargar archivo de audio específico"""
            try:
                # Validar filename para seguridad
                if not filename.endswith('.wav') or '..' in filename or '/' in filename:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid filename"
                    )
                
                file_path = Path("/app/captured_audio") / filename
                
                if not file_path.exists():
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Audio file not found: {filename}"
                    )
                
                return FileResponse(
                    path=str(file_path),
                    media_type="audio/wav",
                    filename=filename
                )
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error downloading audio file: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error downloading audio file: {str(e)}"
                )
        
        @self.app.get("/audio/status",
                     summary="Get Audio Status",
                     description="Estado del audio, VAD y grabación")
        async def get_audio_status():
            """Estado de audio, VAD y grabación"""
            try:
                # Información básica del estado usando nueva API
                current_state = self.state_manager.get_current_state()
                stats = self.state_manager.get_stats()
                
                audio_status = {
                    "hardware_state": current_state.name,
                    "is_listening": current_state == AssistantState.LISTENING,
                    "time_in_current_state": self.state_manager.get_time_in_current_state(),
                    "timestamp": datetime.now().isoformat(),
                    "total_transitions": stats.get("total_transitions", 0),
                    "registered_components": stats.get("registered_components", [])
                }
                
                # Información del VAD no está disponible directamente desde StateManager refactorizado
                # El StateManager ahora es un coordinador puro sin referencias a componentes específicos
                audio_status["vad"] = {
                    "note": "VAD info not available through StateManager - use /components endpoint",
                    "registered_components": stats.get("registered_components", [])
                }
                
                # Estadísticas de archivos capturados
                captured_dir = Path("/app/captured_audio")
                if captured_dir.exists():
                    audio_files = list(captured_dir.glob("captured_*.wav"))
                    total_size = sum(f.stat().st_size for f in audio_files)
                    
                    audio_status["captured_files"] = {
                        "count": len(audio_files),
                        "total_size_bytes": total_size,
                        "total_size_mb": round(total_size / (1024 * 1024), 2)
                    }
                else:
                    audio_status["captured_files"] = {
                        "count": 0,
                        "total_size_bytes": 0,
                        "total_size_mb": 0
                    }
                
                # Información de tiempo de escucha usando nueva API
                if current_state == AssistantState.LISTENING:
                    listening_duration = self.state_manager.get_time_in_current_state()
                    audio_status["listening_duration_seconds"] = round(listening_duration, 2)
                else:
                    audio_status["listening_duration_seconds"] = 0
                
                return {
                    "success": True,
                    "audio_status": audio_status
                }
                
            except Exception as e:
                self.logger.error(f"Error getting audio status: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error getting audio status: {str(e)}"
                )

        # ========================
        # ENDPOINTS DE CONTROL DE HARDWARE (HW-API-04)
        # ========================
        
        @self.app.post("/led/pattern",
                      summary="Control LED Pattern",
                      description="Cambiar patrón de LED manualmente")
        async def set_led_pattern(request: LEDPatternRequest):
            """Control manual de patrones LED"""
            try:
                # Verificar que tenemos LEDController disponible
                if not hasattr(self.state_manager, 'led_controller') or not self.state_manager.led_controller:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="LED controller not available"
                    )
                
                led_controller = self.state_manager.led_controller
                
                # Configurar brillo si se especifica
                if request.brightness is not None:
                    if not 0 <= request.brightness <= 255:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Brightness must be between 0 and 255"
                        )
                    led_controller.set_brightness(request.brightness)
                
                # Procesar según tipo de patrón
                if request.pattern_type.lower() == "solid":
                    if request.color:
                        if request.color.startswith('#'):
                            # Color hex
                            hex_color = request.color[1:]
                            if len(hex_color) != 6:
                                raise HTTPException(
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid hex color format"
                                )
                            try:
                                r = int(hex_color[0:2], 16)
                                g = int(hex_color[2:4], 16)
                                b = int(hex_color[4:6], 16)
                                color = LEDColor(r, g, b)
                            except ValueError:
                                raise HTTPException(
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid hex color values"
                                )
                        else:
                            # Color predefinido
                            if request.color.lower() not in led_controller.COLORS:
                                available_colors = list(led_controller.COLORS.keys())
                                raise HTTPException(
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"Invalid color. Available: {available_colors}"
                                )
                            color = led_controller.COLORS[request.color.lower()]
                    else:
                        # Color blanco por defecto
                        color = led_controller.COLORS['white']
                    
                    led_controller.set_custom_color(color)
                    
                elif request.pattern_type.lower() == "rainbow":
                    led_controller.set_rainbow_pattern(duration=request.duration)
                    
                elif request.pattern_type.lower() == "off":
                    led_controller.turn_off()
                    
                else:
                    # Estados predefinidos
                    state_mapping = {
                        'idle': LEDState.IDLE,
                        'listening': LEDState.LISTENING,
                        'processing': LEDState.PROCESSING,
                        'speaking': LEDState.SPEAKING,
                        'error': LEDState.ERROR
                    }
                    
                    if request.pattern_type.lower() in state_mapping:
                        led_state = state_mapping[request.pattern_type.lower()]
                        led_controller.set_state(led_state)
                    else:
                        available_patterns = ['solid', 'rainbow', 'off'] + list(state_mapping.keys())
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid pattern type. Available: {available_patterns}"
                        )
                
                self.logger.info(f"LED pattern changed to: {request.pattern_type}")
                
                return {
                    "success": True,
                    "pattern_set": request.pattern_type,
                    "color": request.color,
                    "brightness": led_controller.brightness,
                    "timestamp": datetime.now().isoformat()
                }
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error setting LED pattern: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error setting LED pattern: {str(e)}"
                )
        
        @self.app.get("/metrics",
                     summary="System Metrics",
                     description="Obtener métricas del sistema y hardware")
        async def get_system_metrics():
            """Métricas del sistema (CPU, memoria, eventos)"""
            try:
                # Métricas del sistema
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                boot_time = psutil.boot_time()
                uptime = time.time() - boot_time
                
                # Temperatura (si está disponible)
                temperature = None
                try:
                    # Intentar obtener temperatura del CPU en Raspberry Pi
                    if os.path.exists('/sys/class/thermal/thermal_zone0/temp'):
                        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                            temp_raw = int(f.read().strip())
                            temperature = temp_raw / 1000.0  # Convertir a Celsius
                except:
                    pass
                
                # Métricas de hardware (si están disponibles)
                hardware_metrics = {}
                
                # StateManager status usando nueva API
                if self.state_manager:
                    current_state = self.state_manager.get_current_state()
                    stats = self.state_manager.get_stats()
                    
                    hardware_metrics["state_manager"] = {
                        "current_state": current_state.name,
                        "is_listening": current_state == AssistantState.LISTENING,
                        "time_in_current_state": self.state_manager.get_time_in_current_state(),
                        "total_transitions": stats.get("total_transitions", 0),
                        "registered_components": stats.get("registered_components", []),
                        "component_count": stats.get("component_count", 0)
                    }
                    
                    if current_state == AssistantState.LISTENING:
                        listening_duration = self.state_manager.get_time_in_current_state()
                        hardware_metrics["state_manager"]["listening_duration_seconds"] = round(listening_duration, 2)
                
                # LED Controller status
                # En la nueva arquitectura, el StateManager no mantiene referencias directas
                # El LED Controller es gestionado a través de adaptadores
                hardware_metrics["led_controller"] = {
                    "note": "LED Controller managed through StateManager adapters",
                    "registered_components": stats.get("registered_components", []),
                    "led_adapter_registered": "LEDController" in stats.get("registered_components", [])
                }
                
                # Audio status
                captured_dir = Path("/app/captured_audio")
                if captured_dir.exists():
                    audio_files = list(captured_dir.glob("captured_*.wav"))
                    total_size = sum(f.stat().st_size for f in audio_files)
                    hardware_metrics["audio"] = {
                        "captured_files_count": len(audio_files),
                        "total_audio_size_mb": round(total_size / (1024 * 1024), 2)
                    }
                
                # Procesos del sistema
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        if proc.info['cpu_percent'] > 1.0 or proc.info['memory_percent'] > 1.0:
                            processes.append(proc.info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Ordenar por uso de CPU
                processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
                top_processes = processes[:5]  # Top 5 procesos
                
                return {
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "system": {
                        "cpu_percent": cpu_percent,
                        "memory": {
                            "total_gb": round(memory.total / (1024**3), 2),
                            "available_gb": round(memory.available / (1024**3), 2),
                            "used_percent": memory.percent,
                            "used_gb": round(memory.used / (1024**3), 2)
                        },
                        "disk": {
                            "total_gb": round(disk.total / (1024**3), 2),
                            "free_gb": round(disk.free / (1024**3), 2),
                            "used_percent": round((disk.used / disk.total) * 100, 1)
                        },
                        "uptime_hours": round(uptime / 3600, 1),
                        "temperature_celsius": temperature,
                        "top_processes": top_processes
                    },
                    "hardware": hardware_metrics
                }
                
            except Exception as e:
                self.logger.error(f"Error getting system metrics: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error getting system metrics: {str(e)}"
                )
        
        @self.app.post("/button/simulate",
                      summary="Simulate Button Press",
                      description="Simular eventos de botón para testing")
        async def simulate_button_press(request: ButtonSimulateRequest):
            """Simular eventos de botón para testing"""
            try:
                # Validar tipo de evento
                if request.event_type.lower() not in ['short', 'long']:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="event_type must be 'short' or 'long'"
                    )
                
                # Determinar duración
                if request.duration is not None:
                    if request.duration < 0.01 or request.duration > 10.0:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="duration must be between 0.01 and 10.0 seconds"
                        )
                    duration = request.duration
                else:
                    # Duraciones por defecto
                    duration = 0.1 if request.event_type.lower() == 'short' else 2.5
                
                # Simular el evento directamente en StateManager
                # (esto activará los callbacks apropiados)
                press_type = request.event_type.lower()
                
                self.logger.info(f"🔘 Simulating {press_type} button press (duration: {duration}s)")
                
                # Notificar al StateManager como si fuera un evento real
                if hasattr(self.state_manager, 'handle_button_press'):
                    self.state_manager.handle_button_press(press_type)
                else:
                    self.logger.warning("StateManager does not have handle_button_press method")
                
                return {
                    "success": True,
                    "simulated_event": press_type,
                    "duration_seconds": duration,
                    "timestamp": datetime.now().isoformat(),
                    "message": f"Simulated {press_type} button press successfully"
                }
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error simulating button press: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error simulating button press: {str(e)}"
                )

    def start(self):
        """Iniciar el servidor HTTP"""
        self.logger.info(f"🌐 Starting HTTP server on port {self.port}")
        self.logger.info(f"📖 API documentation available at: http://0.0.0.0:{self.port}/docs")
        uvicorn.run(self.app, host="0.0.0.0", port=self.port, log_level="info")

    def start_async(self, host: str = "0.0.0.0"):
        """
        Iniciar el servidor de forma asíncrona (para integración con otros servicios)
        Devuelve la configuración para uvicorn
        """
        return {
            "app": self.app,
            "host": host,
            "port": self.port,
            "log_level": "info"
        }

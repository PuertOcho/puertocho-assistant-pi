"""
Logging Middleware for PuertoCho Assistant Backend
=================================================

Middleware de logging estructurado siguiendo el patrón implementado
en el hardware para mantener consistencia.
"""

import time
import uuid
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware de logging para peticiones HTTP.
    
    Registra todas las peticiones con información detallada,
    siguiendo el mismo patrón que el hardware.
    """
    
    def __init__(self, app, logger_name: str = "http_requests"):
        super().__init__(app)
        self.logger = logging.getLogger(logger_name)
    
    async def dispatch(self, request: Request, call_next):
        """Procesar petición HTTP con logging"""
        
        # Generar ID único para la petición
        request_id = str(uuid.uuid4())[:8]
        
        # Información del cliente
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Registrar inicio de petición
        start_time = time.time()
        
        self.logger.info(
            f"🌐 HTTP Request [{request_id}]: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": client_ip,
                "user_agent": user_agent,
                "event_type": "http_request_start"
            }
        )
        
        # Procesar petición
        try:
            # Agregar request_id al request para que esté disponible en endpoints
            request.state.request_id = request_id
            
            response = await call_next(request)
            
            # Calcular tiempo de procesamiento
            process_time = time.time() - start_time
            
            # Registrar respuesta exitosa
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
            response.headers["X-Service"] = "puertocho-backend-gateway"
            
            return response
            
        except Exception as e:
            # Calcular tiempo hasta el error
            process_time = time.time() - start_time
            
            # Registrar error
            self.logger.error(
                f"🌐 HTTP Error [{request_id}]: {str(e)} after {process_time:.3f}s",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "process_time_seconds": round(process_time, 3),
                    "event_type": "http_request_error"
                },
                exc_info=True
            )
            
            # Re-lanzar la excepción para que FastAPI la maneje
            raise


def setup_logging():
    """
    Configurar sistema de logging estructurado.
    
    Configura loggers para diferentes componentes del sistema
    siguiendo las mejores prácticas.
    """
    
    # Configuración básica de logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configurar niveles para diferentes componentes
    loggers_config = {
        "hardware_client": logging.INFO,
        "state_manager_gateway": logging.INFO,
        "websocket_manager": logging.INFO,
        "audio_processor": logging.INFO,
        "gateway_api": logging.INFO,
        "http_requests": logging.INFO,
        
        # Bibliotecas externas
        "httpx": logging.WARNING,
        "uvicorn.access": logging.WARNING,
        "fastapi": logging.WARNING
    }
    
    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
    
    # Logger principal del backend
    backend_logger = logging.getLogger("backend_gateway")
    backend_logger.setLevel(logging.INFO)
    
    backend_logger.info("📝 Logging system configured")
    
    return backend_logger


def get_request_id(request: Request) -> str:
    """
    Obtener request ID de la petición actual.
    
    Args:
        request: Request objeto de FastAPI
        
    Returns:
        Request ID único o "unknown" si no está disponible
    """
    return getattr(request.state, "request_id", "unknown")

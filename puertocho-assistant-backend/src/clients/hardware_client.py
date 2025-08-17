"""
Hardware Client for PuertoCho Assistant Backend
==============================================

Cliente HTTP para comunicarse con el hardware del asistente (puerto 8080).
Consume la API REST implementada en puertocho-assistant-hardware.
"""

import httpx
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime


class HardwareClient:
    """
    Cliente HTTP para comunicarse con el hardware del asistente.
    
    Este cliente consume la API REST del hardware implementada en
    puertocho-assistant-hardware (puerto 8080).
    """
    
    def __init__(
        self, 
        base_url: str = "http://hardware:8080",
        timeout: float = 30.0,
        retry_attempts: int = 3,
        retry_delay: float = 1.0
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.logger = logging.getLogger("hardware_client")
        
        # Configurar cliente HTTP
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "User-Agent": "PuertoCho-Backend-Gateway/1.0",
                "Accept": "application/json"
            }
        )
    
    async def close(self):
        """Cerrar sesión HTTP"""
        await self.session.aclose()
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Realizar petición HTTP con reintentos y manejo de errores.
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.retry_attempts):
            try:
                self.logger.debug(f"🔌 {method.upper()} {url} (attempt {attempt + 1})")
                
                response = await self.session.request(method, url, **kwargs)
                response.raise_for_status()
                
                # Log successful request
                self.logger.info(
                    f"✅ Hardware API: {method.upper()} {endpoint} -> {response.status_code}"
                )
                
                if response.headers.get("content-type", "").startswith("application/json"):
                    return response.json()
                else:
                    return {"content": response.content, "headers": dict(response.headers)}
                    
            except httpx.TimeoutException:
                self.logger.warning(f"⏰ Timeout in {method.upper()} {url} (attempt {attempt + 1})")
                if attempt == self.retry_attempts - 1:
                    raise Exception(f"Hardware timeout after {self.retry_attempts} attempts")
                    
            except httpx.ConnectError:
                self.logger.warning(f"🔌 Connection error to {url} (attempt {attempt + 1})")
                if attempt == self.retry_attempts - 1:
                    raise Exception(f"Hardware connection failed after {self.retry_attempts} attempts")
                    
            except httpx.HTTPStatusError as e:
                self.logger.error(f"❌ HTTP {e.response.status_code} in {method.upper()} {url}")
                if e.response.status_code >= 500:
                    # Retry on server errors
                    if attempt == self.retry_attempts - 1:
                        raise Exception(f"Hardware server error: {e.response.status_code}")
                else:
                    # Don't retry on client errors (4xx)
                    raise Exception(f"Hardware client error: {e.response.status_code} - {e.response.text}")
                    
            except Exception as e:
                self.logger.error(f"❌ Unexpected error in {method.upper()} {url}: {e}")
                if attempt == self.retry_attempts - 1:
                    raise Exception(f"Hardware request failed: {str(e)}")
            
            # Wait before retry
            if attempt < self.retry_attempts - 1:
                await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
    
    # ===========================================
    # ENDPOINTS BÁSICOS (Health, State, etc.)
    # ===========================================
    
    async def get_health(self) -> Dict[str, Any]:
        """GET /health - Verificar estado del servicio hardware"""
        return await self._make_request("GET", "/health")
    
    async def get_state(self) -> Dict[str, Any]:
        """GET /state - Obtener estado actual del StateManager"""
        return await self._make_request("GET", "/state")
    
    async def set_state(self, state: str) -> Dict[str, Any]:
        """POST /state - Cambiar estado manualmente (para testing)"""
        return await self._make_request(
            "POST", 
            "/state", 
            json={"state": state}
        )
    
    # ===========================================
    # ENDPOINTS DE AUDIO
    # ===========================================
    
    async def get_latest_audio(self) -> Dict[str, Any]:
        """GET /audio/capture - Obtener último archivo de audio capturado"""
        return await self._make_request("GET", "/audio/capture")
    
    async def download_audio(self, filename: str) -> bytes:
        """GET /audio/download/{filename} - Descargar archivo de audio específico"""
        response = await self._make_request("GET", f"/audio/download/{filename}")
        return response.get("content", b"")
    
    async def get_audio_status(self) -> Dict[str, Any]:
        """GET /audio/status - Estado de audio, VAD y grabación"""
        return await self._make_request("GET", "/audio/status")
    
    async def send_audio_to_backend(self, backend_url: Optional[str] = None, compress: bool = True) -> Dict[str, Any]:
        """POST /audio/send - Enviar audio al backend local (nosotros)"""
        payload = {"compress": compress}
        if backend_url:
            payload["backend_url"] = backend_url
            
        return await self._make_request("POST", "/audio/send", json=payload)
    
    # ===========================================
    # ENDPOINTS DE CONTROL DE HARDWARE
    # ===========================================
    
    async def set_led_pattern(
        self, 
        pattern_type: str, 
        color: Optional[str] = None,
        duration: Optional[float] = 1.0,
        brightness: Optional[int] = None
    ) -> Dict[str, Any]:
        """POST /led/pattern - Cambiar patrón LED manualmente"""
        payload = {
            "pattern_type": pattern_type,
            "duration": duration
        }
        if color:
            payload["color"] = color
        if brightness is not None:
            payload["brightness"] = brightness
            
        return await self._make_request("POST", "/led/pattern", json=payload)
    
    async def simulate_button_press(
        self, 
        event_type: str, 
        duration: Optional[float] = None
    ) -> Dict[str, Any]:
        """POST /button/simulate - Simular eventos de botón para testing"""
        payload = {"event_type": event_type}
        if duration is not None:
            payload["duration"] = duration
            
        return await self._make_request("POST", "/button/simulate", json=payload)
    
    async def get_metrics(self) -> Dict[str, Any]:
        """GET /metrics - Métricas del sistema (CPU, memoria, eventos)"""
        return await self._make_request("GET", "/metrics")
    
    # ===========================================
    # MÉTODOS DE UTILIDAD
    # ===========================================
    
    async def is_hardware_available(self) -> bool:
        """Verificar si el hardware está disponible y respondiendo"""
        try:
            health = await self.get_health()
            return health.get("status") == "healthy"
        except Exception as e:
            self.logger.warning(f"Hardware not available: {e}")
            return False
    
    async def wait_for_hardware(self, max_wait_time: float = 60.0) -> bool:
        """
        Esperar a que el hardware esté disponible.
        
        Args:
            max_wait_time: Tiempo máximo a esperar en segundos
            
        Returns:
            True si hardware está disponible, False si timeout
        """
        start_time = datetime.now().timestamp()
        check_interval = 5.0
        
        self.logger.info(f"🔍 Waiting for hardware at {self.base_url} (max {max_wait_time}s)")
        
        while (datetime.now().timestamp() - start_time) < max_wait_time:
            if await self.is_hardware_available():
                self.logger.info("✅ Hardware is now available!")
                return True
                
            self.logger.debug(f"⏳ Hardware not ready, checking again in {check_interval}s...")
            await asyncio.sleep(check_interval)
        
        self.logger.error(f"❌ Hardware not available after {max_wait_time}s timeout")
        return False
    
    async def get_audio_files_list(self) -> List[str]:
        """
        Obtener lista de archivos de audio disponibles.
        Utiliza el endpoint /audio/capture para obtener información.
        """
        try:
            audio_info = await self.get_latest_audio()
            # El hardware podría retornar información sobre archivos disponibles
            # Por ahora retornamos el último archivo si existe
            if audio_info.get("success") and audio_info.get("latest_audio"):
                filename = audio_info["latest_audio"].get("filename")
                return [filename] if filename else []
            return []
        except Exception as e:
            self.logger.warning(f"Could not get audio files list: {e}")
            return []
    
    async def play_audio(self, audio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enviar audio al hardware para reproducción.
        
        Args:
            audio_data: Dict con:
                - audio_data: string base64 con datos de audio
                - format: formato del audio (ej: 'wav')
                - sample_rate: tasa de muestreo (opcional)
        
        Returns:
            Dict con resultado de la operación
        """
        self.logger.info("🔊 Sending audio to hardware for playback...")
        
        try:
            response = await self._make_request(
                "POST",
                "/audio/play",
                json=audio_data
            )
            
            if response.get("success"):
                self.logger.info("✅ Audio sent to hardware successfully")
            else:
                self.logger.warning(f"⚠️ Hardware audio playback warning: {response.get('message', 'Unknown')}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send audio to hardware: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Instancia singleton del cliente hardware (se inicializa en main.py)
hardware_client: Optional[HardwareClient] = None


def get_hardware_client() -> HardwareClient:
    """Obtener instancia del cliente hardware"""
    global hardware_client
    if hardware_client is None:
        raise Exception("Hardware client not initialized. Call init_hardware_client() first.")
    return hardware_client


def init_hardware_client(base_url: str = "http://hardware:8080") -> HardwareClient:
    """Inicializar cliente hardware"""
    global hardware_client
    hardware_client = HardwareClient(base_url=base_url)
    return hardware_client


async def close_hardware_client():
    """Cerrar cliente hardware"""
    global hardware_client
    if hardware_client:
        await hardware_client.close()
        hardware_client = None

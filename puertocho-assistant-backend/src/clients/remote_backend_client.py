"""
Remote Backend Client for PuertoCho Assistant Backend
====================================================

Cliente HTTP para comunicarse con el backend remoto que procesa el audio con IA/LLM.
Maneja autenticación automática, renovación de tokens y envío de audio para procesamiento.
"""

import httpx
import asyncio
import logging
import os
import base64
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class RemoteBackendClient:
    """
    Cliente HTTP para comunicarse con el backend remoto de procesamiento.
    
    Features:
    - Autenticación automática con email/password
    - Renovación automática de tokens JWT
    - Envío de audio con metadata en formato multipart/form-data
    - Manejo robusto de errores y reintentos
    - Configuración por variables de entorno
    """
    
    def __init__(self):
        self.logger = logging.getLogger("remote_backend_client")
        
        # Configuración del backend remoto desde variables de entorno
        self.base_url = os.getenv("REMOTE_BACKEND_URL", "http://192.168.1.88:10002")
        self.email = os.getenv("REMOTE_BACKEND_EMAIL", "service@puertocho.local")
        self.password = os.getenv("REMOTE_BACKEND_PASSWORD", "servicepass123")
        
        # Configuración de timeouts y reintentos
        self.timeout = float(os.getenv("REMOTE_BACKEND_TIMEOUT", "60.0"))
        self.retry_attempts = int(os.getenv("REMOTE_BACKEND_RETRY_ATTEMPTS", "3"))
        self.retry_delay = float(os.getenv("REMOTE_BACKEND_RETRY_DELAY", "2.0"))
        
        # Estado de autenticación
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.refresh_token: Optional[str] = None
        self.is_authenticated = False
        
        # Cliente HTTP con configuración extendida para audio
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=10.0,     # Timeout de conexión
                read=self.timeout, # Timeout de lectura (para audio)
                write=30.0,       # Timeout de escritura
                pool=5.0          # Timeout del pool
            ),
            headers={
                "User-Agent": "PuertoCho-Assistant-Backend/1.0",
                "Accept": "application/json"
            },
            follow_redirects=True,
            limits=httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10
            )
        )
        
        # Task de renovación automática de token
        self.auth_refresh_task: Optional[asyncio.Task] = None
        self._shutdown_requested = False
        
    async def start(self):
        """Inicializar cliente y autenticación"""
        self.logger.info("🚀 Starting Remote Backend Client...")
        self.logger.info(f"Backend URL: {self.base_url}")
        self.logger.info(f"User Email: {self.email}")
        
        try:
            # Autenticación inicial
            success = await self._authenticate()
            if not success:
                raise Exception("Failed to authenticate with remote backend")
            
            # Iniciar renovación automática de token
            self.auth_refresh_task = asyncio.create_task(self._auto_refresh_token())
            
            self.logger.info("✅ Remote Backend Client started successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start Remote Backend Client: {e}")
            raise
            
    async def stop(self):
        """Detener cliente y limpiar recursos"""
        self.logger.info("🛑 Stopping Remote Backend Client...")
        
        self._shutdown_requested = True
        
        # Cancelar tarea de renovación
        if self.auth_refresh_task and not self.auth_refresh_task.done():
            self.auth_refresh_task.cancel()
            try:
                await self.auth_refresh_task
            except asyncio.CancelledError:
                pass
        
        # Cerrar sesión HTTP
        await self.session.aclose()
        
        self.logger.info("✅ Remote Backend Client stopped")
        
    async def _authenticate(self) -> bool:
        """
        Autenticar con el backend remoto usando email/password.
        
        Returns:
            bool: True si la autenticación fue exitosa
        """
        try:
            self.logger.info("🔐 Authenticating with remote backend...")
            
            auth_payload = {
                "email": self.email,
                "password": self.password
            }
            
            response = await self.session.post(
                f"{self.base_url}/api/auth/login",
                json=auth_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                auth_data = response.json()
                
                # Extraer tokens
                self.access_token = auth_data.get("access_token") or auth_data.get("token")
                self.refresh_token = auth_data.get("refresh_token")
                
                if not self.access_token:
                    self.logger.error("❌ No access token received from backend")
                    return False
                
                # Calcular expiración del token
                expires_in = auth_data.get("expires_in", 3600)  # Default 1 hora
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)  # Renovar 5 min antes
                
                self.is_authenticated = True
                
                self.logger.info("✅ Authentication successful")
                self.logger.info(f"🔑 Access token: {self.access_token[:20]}...{self.access_token[-10:] if len(self.access_token) > 30 else self.access_token}")
                self.logger.info(f"🕒 Token expires at: {self.token_expires_at}")
                if self.refresh_token:
                    self.logger.info(f"🔄 Refresh token available: {self.refresh_token[:15]}...{self.refresh_token[-5:] if len(self.refresh_token) > 20 else self.refresh_token}")
                
                return True
                
            else:
                error_detail = "Unknown error"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", error_data.get("message", str(error_data)))
                except:
                    error_detail = response.text
                
                self.logger.error(f"❌ Authentication failed ({response.status_code}): {error_detail}")
                return False
                
        except httpx.TimeoutException:
            self.logger.error("❌ Authentication timeout - check backend connectivity")
            return False
        except httpx.ConnectError:
            self.logger.error(f"❌ Cannot connect to remote backend at {self.base_url}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Authentication error: {e}")
            return False
            
    async def _refresh_auth_token(self) -> bool:
        """
        Renovar token de autenticación usando refresh_token.
        
        Returns:
            bool: True si la renovación fue exitosa
        """
        try:
            if not self.refresh_token:
                self.logger.info("🔄 No refresh token available, re-authenticating...")
                return await self._authenticate()
                
            self.logger.info("🔄 Refreshing authentication token...")
            self.logger.info(f"🕒 Current token expires at: {self.token_expires_at}")
            
            response = await self.session.post(
                f"{self.base_url}/api/auth/refresh",
                json={"refresh_token": self.refresh_token}
            )
            
            if response.status_code == 200:
                auth_data = response.json()
                
                self.access_token = auth_data.get("access_token") or auth_data.get("token")
                new_refresh = auth_data.get("refresh_token")
                if new_refresh:
                    self.refresh_token = new_refresh
                
                expires_in = auth_data.get("expires_in", 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
                
                self.logger.info("✅ Token refreshed successfully")
                self.logger.info(f"🔑 New access token: {self.access_token[:20]}...{self.access_token[-10:] if len(self.access_token) > 30 else self.access_token}")
                self.logger.info(f"🕒 New expiration time: {self.token_expires_at}")
                return True
            else:
                self.logger.warning(f"⚠️ Token refresh failed with status {response.status_code}, re-authenticating...")
                return await self._authenticate()
                
        except Exception as e:
            self.logger.error(f"❌ Token refresh error: {e}")
            self.logger.info("🔄 Falling back to full re-authentication...")
            return await self._authenticate()
            
    async def _auto_refresh_token(self):
        """Task en background para renovar token automáticamente"""
        while not self._shutdown_requested:
            try:
                if self.token_expires_at:
                    # Calcular tiempo hasta renovación
                    time_until_refresh = (self.token_expires_at - datetime.now()).total_seconds()
                    
                    if time_until_refresh > 0:
                        sleep_time = min(time_until_refresh, 300)  # Max 5 min
                        next_refresh = datetime.now() + timedelta(seconds=sleep_time)
                        self.logger.debug(f"🔄 Next token refresh check scheduled for: {next_refresh}")
                        
                        # Esperar hasta que sea momento de renovar
                        await asyncio.sleep(sleep_time)
                    
                    if not self._shutdown_requested:
                        self.logger.info("🔄 Token refresh time reached, refreshing...")
                        await self._refresh_auth_token()
                else:
                    # Sin token, esperar y reintentar autenticación
                    await asyncio.sleep(60)
                    if not self._shutdown_requested:
                        await self._authenticate()
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Error in auto refresh task: {e}")
                await asyncio.sleep(60)
                
    async def _ensure_authenticated(self) -> bool:
        """Asegurar que tenemos un token válido"""
        if not self.is_authenticated or not self.access_token:
            return await self._authenticate()
            
        # Verificar si el token expira pronto
        if self.token_expires_at and datetime.now() >= self.token_expires_at:
            return await self._refresh_auth_token()
            
        return True
        
    async def send_audio_for_processing(
        self, 
        audio_data: bytes,
        metadata: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Enviar audio al backend remoto para procesamiento con IA/LLM.
        
        Args:
            audio_data: Datos de audio en bytes (formato WAV)
            metadata: Metadata del audio (sample_rate, channels, duration, etc.)
            context: Contexto adicional para el procesamiento (configuración, historial, etc.)
            
        Returns:
            Dict con la respuesta del backend remoto:
            {
                "success": bool,
                "response_type": "audio" | "text" | "action",
                "text": str,           # Transcripción o respuesta de texto
                "audio_data": str,     # Audio de respuesta en Base64 (si aplica)
                "audio_duration": float, # Duración del audio de respuesta
                "action": dict,        # Acción específica a ejecutar (si aplica)
                "error": str           # Error si success=False
            }
        """
        # Asegurar autenticación válida
        if not await self._ensure_authenticated():
            return {
                "success": False,
                "error": "Failed to authenticate with remote backend"
            }
        
        for attempt in range(self.retry_attempts):
            try:
                self.logger.info(f"📡 Sending audio to remote backend (attempt {attempt + 1})...")
                self.logger.info(f"🔑 Using token: {self.access_token[:20]}...{self.access_token[-10:] if len(self.access_token) > 30 else self.access_token}")
                self.logger.info(f"🕒 Token expires at: {self.token_expires_at}")
                
                # Preparar headers de autenticación
                headers = {
                    "Authorization": f"Bearer {self.access_token}"
                }
                
                # Preparar archivo de audio
                files = {
                    "audio": ("audio.wav", audio_data, "audio/wav")
                }
                
                # Preparar metadata y contexto como campos del formulario
                form_data = {
                    "metadata": json.dumps(metadata),
                    "context": json.dumps(context or {})
                }
                
                # Enviar petición multipart/form-data
                response = await self.session.post(
                    f"{self.base_url}/api/audio/process",
                    files=files,
                    data=form_data,
                    headers=headers
                )
                
                # Manejar respuesta de autenticación expirada
                if response.status_code == 401:
                    self.logger.warning(f"🔒 Token expired during request (attempt {attempt + 1}), refreshing...")
                    if await self._refresh_auth_token():
                        continue  # Reintentar con nuevo token
                    else:
                        return {
                            "success": False,
                            "error": "Authentication expired and refresh failed"
                        }
                
                # Verificar respuesta exitosa
                if response.status_code == 200:
                    result = response.json()
                    
                    self.logger.info(f"✅ Remote backend response received")
                    self.logger.info(f"Response type: {result.get('response_type', 'unknown')}")
                    
                    if result.get("text"):
                        self.logger.info(f"Text response: {result['text'][:100]}...")
                    
                    return {
                        "success": True,
                        **result
                    }
                else:
                    error_detail = "Unknown error"
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("detail", error_data.get("message", str(error_data)))
                    except:
                        error_detail = response.text
                    
                    self.logger.error(f"❌ Remote backend error ({response.status_code}): {error_detail}")
                    
                    # No reintentar errores 4xx (excepto 401 ya manejado)
                    if 400 <= response.status_code < 500:
                        return {
                            "success": False,
                            "error": f"Backend error {response.status_code}: {error_detail}"
                        }
                    
                    # Reintentar errores 5xx
                    if attempt < self.retry_attempts - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue
                    
                    return {
                        "success": False,
                        "error": f"Backend error after {self.retry_attempts} attempts: {error_detail}"
                    }
                    
            except httpx.TimeoutException:
                self.logger.error(f"❌ Timeout sending audio to remote backend (attempt {attempt + 1})")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                return {
                    "success": False,
                    "error": "Timeout communicating with remote backend"
                }
                
            except httpx.ConnectError:
                self.logger.error(f"❌ Connection error to remote backend (attempt {attempt + 1})")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                return {
                    "success": False,
                    "error": "Cannot connect to remote backend"
                }
                
            except Exception as e:
                self.logger.error(f"❌ Unexpected error sending audio (attempt {attempt + 1}): {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                return {
                    "success": False,
                    "error": f"Unexpected error: {str(e)}"
                }
        
        return {
            "success": False,
            "error": f"Failed after {self.retry_attempts} attempts"
        }
        
    async def health_check(self) -> Dict[str, Any]:
        """
        Verificar estado de salud del backend remoto.
        
        Returns:
            Dict con información de estado
        """
        try:
            response = await self.session.get(
                f"{self.base_url}/health",
                timeout=10.0
            )
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "authenticated": self.is_authenticated,
                    "token_expires_at": self.token_expires_at.isoformat() if self.token_expires_at else None
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "authenticated": self.is_authenticated
                }
                
        except Exception as e:
            return {
                "status": "unreachable",
                "error": str(e),
                "authenticated": False
            }


# Instancia singleton global
_remote_client: Optional[RemoteBackendClient] = None

def get_remote_client() -> RemoteBackendClient:
    """
    Obtener instancia global del cliente remoto.
    
    Returns:
        RemoteBackendClient: Instancia del cliente
        
    Raises:
        RuntimeError: Si el cliente no ha sido inicializado
    """
    global _remote_client
    if not _remote_client:
        raise RuntimeError("Remote client not initialized. Call init_remote_client() first.")
    return _remote_client
    
async def init_remote_client() -> RemoteBackendClient:
    """
    Inicializar cliente remoto global.
    
    Returns:
        RemoteBackendClient: Instancia inicializada
    """
    global _remote_client
    if not _remote_client:
        _remote_client = RemoteBackendClient()
        await _remote_client.start()
    return _remote_client
    
async def close_remote_client():
    """Cerrar cliente remoto global"""
    global _remote_client
    if _remote_client:
        await _remote_client.stop()
        _remote_client = None

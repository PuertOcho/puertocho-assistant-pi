# Epic 4 – Integración Backend Local ↔ Backend Remoto (Tarea 4.3)

Objetivo: documentar el contrato y la ruta de implementación para “4.3 Actualizar AudioProcessor para Backend Remoto” entre:
- Backend Local (puertocho-assistant-backend, FastAPI, puerto 8000)
- Backend Remoto (gatewayms + intentmanagerms, expuesto en 10002)

Estado: los microservicios en `Backend_Remoto_copia/*` son copias solo para referencia; cambios ahí no afectan al remoto real.

---

## 1) Visión general de arquitectura remota

- API Gateway: `gatewayms` (Spring Cloud Gateway)
  - Rutas declaradas en `Backend_Remoto_copia/gatewayms/.../RouteConfig.java`:
    - `/api/auth/**` → USER service (autenticación)
    - `/api/v1/conversation/**` → INTENT_MANAGER service (conversación/IA)
    - `/api/auth-test/**` → INTENT_MANAGER service (utilidades de prueba)
- Servicio conversacional: `intentmanagerms`
  - Controlador principal: `ConversationManagerController.java`
  - Endpoints de conversación (texto y audio), transcripción (Whisper), TTS, estado de sesión, etc.
- Configuración central del intent manager: `intent-manager.yml` (límite de audio, formatos, etc.)

Base URL Gateway Remoto (por docker-compose/.env local):
- `REMOTE_BACKEND_URL=http://192.168.1.88:10002`
- Credenciales de servicio: `service@puertocho.local` / `servicepass123`

---

## 2) Autenticación

Gestionada por el gateway con ruta `/api/auth/**` (USER service detrás). El backend local usa tokens Bearer.

- Login: `POST {REMOTE_BACKEND_URL}/api/auth/login`
  - Body JSON: `{ "email": string, "password": string }`
  - Respuesta real (ejemplo):
    ```json
    {
      "token": "<JWT>",
      "type": "Bearer",
      "username": "PuertochoService",
      "email": "service@puertocho.local",
      "fullName": "Puertocho Service Account"
    }
    ```
  - Nota: la clave es `token` (no `access_token`). No se devuelve `expires_in` ni `refresh_token` en este entorno.
- Refresh: `POST {REMOTE_BACKEND_URL}/api/auth/refresh` (disponible, pero puede no devolver `refresh_token`/`expires_in`).

Notas:
- El cliente local (`RemoteBackendClient`) ya soporta `token` y reautentica ante 401.
- Se envía `Authorization: Bearer <token>` en peticiones protegidas.

---

## 3) Endpoints de procesamiento de audio (conversacionales)

El API conversacional de `intentmanagerms` expone (en el servicio) bajo `@RequestMapping("/api/v1/conversation")`:
- `POST /process` (texto)
- `POST /process/audio` (audio multipart/form-data)
- `POST /process/audio/simple` (audio simple, sin respuesta de audio)

A través del gateway (sin reescritura de path), la ruta efectiva desde el backend local es:

- Conversación con audio:
  - `POST {REMOTE_BACKEND_URL}/api/v1/conversation/process/audio`
- Conversación con audio (simple):
  - `POST {REMOTE_BACKEND_URL}/api/v1/conversation/process/audio/simple`

### 3.1) Request multipart/form-data (process/audio)
Campos:
- `audio` (file): WAV/MP3/M4A/FLAC
- `sessionId` (string): ID de sesión de conversación
- `userId` (string): ID del usuario (o cuenta de servicio)
- `language` (string, opcional, default="es")
- `generateAudioResponse` (boolean, opcional, default=true)
- `metadata` (string JSON, opcional): metadatos adicionales

Sugerencia de `metadata` (JSON):
```
{
  "audio": {
    "audio_id": "audio_YYYYMMDD_HHMMSS_mmm",
    "filename": "...",
    "format": "wav",
    "size_bytes": 12345,
    "sample_rate_hz": 44100,
    "channels": 1,
    "bits_per_sample": 16,
    "estimated_duration_seconds": 2.34,
    "captured_at": "2025-08-09T12:34:56.789Z",
    "integrity_check": { "is_valid": true, "format_detected": "wav", "issues": [] }
  },
  "device": {
    "device_id": "puertocho-rpi-01",
    "room": "salon",
    "temperature": 22,
    "network": "wifi"
  },
  "flags": { "debug": true }
}
```

### 3.2) Respuesta esperada (ConversationAudioResponse)
El controlador Java indica los campos (Jackson serializa `byte[]` como Base64):
- `success` (bool)
- `sessionId` (string)
- `transcribedText` (string)
- `systemResponse` (string) → texto final de respuesta
- `detectedIntent` (string)
- `confidenceScore` (double)
- `extractedEntities` (object)
- `sessionState` (string)
- `turnCount` (int)
- `processingTimeMs` (long)
- `audioResponse` (base64) → audio de respuesta (si `audioResponseGenerated=true`)
- `audioResponseGenerated` (bool)
- `whisperConfidence` (double)
- `whisperLanguage` (string)
- `errorMessage` (string)

Notas de audio de respuesta:
- El microservicio `azure-tts-ms` genera MP3 24kHz y lo convierte a WAV; típico `sample_rate` de salida: 24000 Hz (mono, 16-bit).
- Si el hardware exige 44100 Hz, se deberá remuestrear en 4.4/4.5.

### 3.3) Límites y validaciones (según `intent-manager.yml`)
- Tamaño máximo: `AUDIO_MAX_FILE_SIZE=10485760` (10 MB)
- Formatos soportados: `AUDIO_SUPPORTED_FORMATS=wav,mp3,m4a,flac`
- Rango sample-rate: `AUDIO_SAMPLE_RATE_RANGE=8000-48000`
- Duración máx: `AUDIO_MAX_DURATION=60` (s)

El backend local validará/pre-chequeará (cuando sea posible) para reducir errores 4xx.

---

## 4) Endpoints alternativos (pipeline técnico)
Existen endpoints técnicos documentados en Epic 5 (p. ej. `/api/v1/audio/process`). Se recomienda priorizar el endpoint conversacional anterior. El uso del pipeline técnico dependerá de que exista una ruta en gateway para ese path.

---

## 5) Contrato efectivo entre Backend Local ↔ Remoto

### 5.1) Petición desde Backend Local
- URL: `{REMOTE_BACKEND_URL}/api/v1/conversation/process/audio`
- Auth: `Authorization: Bearer <token>`
- Multipart:
  - `audio`: bytes del último WAV/MP3 capturado por hardware (44100 Hz preferido)
  - `sessionId`: p. ej., persistido por el backend local (o generado si no existe)
  - `userId`: `service@puertocho.local` o usuario real, según escenario
  - `language`: `es` (por defecto)
  - `generateAudioResponse`: `true` (para obtener TTS de retorno)
  - `metadata`: JSON string con métricas/contexto

### 5.2) Respuesta del Remoto
- HTTP 200 con JSON `ConversationAudioResponse` (ver 3.2)
- Errores 4xx/5xx con `{ success:false, errorMessage|detail|message }`

### 5.3) Manejo en Backend Local
- Clasificar respuesta:
  - `audio`: decodificar base64 (WAV habitual 24kHz); en 4.4/4.5 se reproducirá y/o remuestreará a 44100 Hz si es necesario
  - `text`: publicar al WebSocket para UI (y TTS local futuro, si aplica)
- Emitir eventos WebSocket:
  - `audio_processing` (received/started/completed)
  - `remote_response` con `audio_id`, `response_type`, `text`, `intent`, `confidence`, `playback` (duración estimada)

---

## 6) Plan de cambios en el Backend Local

### 6.1) AudioProcessor (`src/services/audio_processor.py`)
- Reemplazar `_send_to_remote_backend(entry)` para usar el cliente remoto conversacional
  - Construir `metadata` desde `entry` (métricas/integridad/tiempos)
  - Aportar `sessionId` y `userId` (ver 7.1)
  - Enviar multipart al endpoint definido (3)
- Añadir handlers por tipo:
  - `_handle_audio_response(response)` → coordina reproducción en hardware (cuando 4.4/4.5 estén listos)
  - `_handle_text_response(response)` → notificaciones WebSocket
- Completar notificaciones WebSocket coherentes con la UI

### 6.2) RemoteBackendClient (`src/clients/remote_backend_client.py`)
- Añadir `send_audio_for_conversation(audio_data, session_id, user_id, language, metadata_json, generate_audio_response=True)` que haga POST a `{REMOTE_BACKEND_URL}/api/v1/conversation/process/audio`
- Configuración por variables de entorno (ruta configurable):
  - `REMOTE_BACKEND_CONVERSATION_PATH=/api/v1/conversation/process/audio`
  - Modo alternativo: `REMOTE_BACKEND_API_MODE=conversation|pipeline`
- Reutilizar autenticación existente y reintento en 5xx/timeout; re-login en 401

---

## 7) Configuración y variables

- `.env` y `docker-compose.yml` locales ya incluyen:
  - `REMOTE_BACKEND_URL`, `REMOTE_BACKEND_EMAIL`, `REMOTE_BACKEND_PASSWORD`
  - Timeouts y reintentos del cliente remoto
- Nuevas (propuestas):
  - `REMOTE_BACKEND_CONVERSATION_PATH=/api/v1/conversation/process/audio`
  - `REMOTE_BACKEND_LANGUAGE=es`
  - `REMOTE_BACKEND_API_MODE=conversation`
  - `CONVERSATION_DEFAULT_USER_ID=service@puertocho.local`
  - `CONVERSATION_SESSION_ID=` (opcional; si se define, fuerza el sessionId)
  - `DEVICE_ID=` (opcional; si no hay CONVERSATION_SESSION_ID, se usa `device-{DEVICE_ID}`)
  - `CONVERSATION_SESSION_STRATEGY=per-request|sticky-per-device`

### 7.1) Gestión de sesión (sticky por dispositivo)
- Estrategia recomendada: `sticky-per-device`.
- Resolución de `sessionId` en backend local:
  1) Si existe `CONVERSATION_SESSION_ID`, usarla directamente.
  2) En su defecto, si existe `DEVICE_ID`, usar `device-{DEVICE_ID}` (p. ej. `device-puertocho-rpi-01`).
  3) Si no hay ninguna, usar `device-{hostname}` (fallback con hostname del sistema).

---

## 8) Ejemplos de uso

### 8.1) cURL – Conversación con audio (vía gateway)
```
curl -X POST "http://192.168.1.88:10002/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"service@puertocho.local","password":"servicepass123"}'
# → tomar campo "token"

curl -X POST "http://192.168.1.88:10002/api/v1/conversation/process/audio" \
  -H "Authorization: Bearer <TOKEN>" \
  -F "audio=@test.wav" \
  -F "sessionId=device-puertocho-rpi-01" \
  -F "userId=service@puertocho.local" \
  -F "language=es" \
  -F "generateAudioResponse=true" \
  -F "metadata={\"audio\":{\"format\":\"wav\",\"sample_rate_hz\":44100}}"
```

Respuesta (ejemplo abreviado):
```
{
  "success": true,
  "sessionId": "device-puertocho-rpi-01",
  "transcribedText": "¿Qué tiempo hace?",
  "systemResponse": "Hoy en Madrid 30ºC y soleado.",
  "detectedIntent": "weather.query",
  "confidenceScore": 0.91,
  "processingTimeMs": 850,
  "audioResponseGenerated": true,
  "audioResponse": "<BASE64>"
}
```

---

## 9) Gestión de errores y reintentos
- 401: re-login y reintentar
- 4xx (≠401): no reintentar, devolver detalle al frontend
- 5xx / timeouts: reintentos exponenciales (configurados en cliente remoto)
- Validaciones previas en local (tamaño/formato/duración) para evitar 4xx

---

## 10) Estado y decisiones (cerrado)
- Ruta efectiva conversación via gateway: `POST {REMOTE_BACKEND_URL}/api/v1/conversation/process/audio` ✔️
- Login/refresh siguen en `{REMOTE_BACKEND_URL}/api/auth/*` ✔️ (respuesta de login usa `token`)
- Idioma soportado: español (`language=es`) ✔️
- Audio capturado se envía tal cual: 44100 Hz preferido ✔️ (límite remoto hasta 48kHz)
- Audio de respuesta típico: WAV 24kHz mono (producido por `azure-tts-ms`) ✔️ (posible remuestreo en 4.4/4.5)
- Acciones explícitas: previstas para el futuro; no implementadas aún ✔️
- Identidad de sesión sticky: usar `CONVERSATION_SESSION_ID` o `device-{DEVICE_ID}` ✔️

---

## 11) Siguientes pasos (implementación 4.3)
- Actualizar `RemoteBackendClient` con método conversacional y ruta configurable
- Actualizar `AudioProcessor._send_to_remote_backend`
- Emitir eventos WebSocket con el nuevo esquema
- Preparar `playback` en hardware (se completará en 4.4/4.5)

---

## 12) Checklist de implementación 4.3

- [x] Contrato y rutas definidos en Epic4
- [x] Variables en .env y docker-compose actualizadas
- [ ] Implementar RemoteBackendClient.send_audio_for_conversation (`src/clients/remote_backend_client.py`)
- [ ] Actualizar AudioProcessor._send_to_remote_backend (`src/services/audio_processor.py`)
- [ ] Resolver sessionId/userId desde entorno (estrategia sticky-per-device)
- [ ] Validaciones de audio (tamaño, formato, duración) antes de enviar
- [ ] Manejo de 401/5xx con reintentos y re-login automático
- [ ] Eventos WebSocket actualizados (audio_processing, remote_response)
- [ ] Verificar endpoints /remote/status y /remote/test-auth
- [ ] Pruebas E2E: hardware → backend local → backend remoto
- [ ] Documentar resultados y cerrar Epic4

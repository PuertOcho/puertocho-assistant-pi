# 🎤 Asistente de Voz Puertocho - Raspberry Pi 4

Asistente de voz activado por wake word "Hola Puertocho" u "Oye Puertocho" que puede controlar LEDs mediante comandos de voz usando **servicio de transcripción HTTP local** para convertir voz a texto.

## 📋 Características

- ✅ **Wake Word personalizado**: "Hola Puertocho" u "Oye Puertocho"  
- ✅ **Detección de silencio**: Para terminar grabación automáticamente
- ✅ **Control por botón**: Activación manual con GPIO 22
- ✅ **LEDs indicadores**: Verde (listo) y Rojo (escuchando)
- ✅ **Transcripción HTTP**: Usa servicio local de transcripción (rápido y privado)
- ✅ **Ejecuta en Docker**: Fácil despliegue

## 🔧 Hardware requerido

- Raspberry Pi 4
- Micrófono (conexión jack)
- LED Verde conectado a GPIO 17
- LED Rojo conectado a GPIO 27  
- Botón conectado a GPIO 22
- Resistencias apropiadas para LEDs

## ⚙️ Configuración previa

> 🆕 **NUEVO**: Ahora usamos archivo `.env` para una configuración más sencilla y segura. Ver [CONFIGURACION_ENV.md](CONFIGURACION_ENV.md) para detalles.

### 1. Requisitos

**🎯 Porcupine ACCESS_KEY (para wake word):**

**📱 MÉTODO FÁCIL (Recomendado):**
```bash
python3 configurar_access_key.py
```

Este script es inteligente y:
1. 🔍 **Verifica** si ya tienes configuración válida
2. ❓ **Te pregunta** si quieres mantenerla o cambiarla
3. 🔑 **Solo pide** nueva clave si es necesario
4. 💾 **Preserva** otras configuraciones existentes

**⚙️ MÉTODO MANUAL:**

1. Ve a [Picovoice Console](https://console.picovoice.ai/)
2. Crea una cuenta gratuita
3. En el dashboard, copia tu **AccessKey**
4. Crea un archivo `.env` en la raíz del proyecto:

```bash
cp env.example .env
nano .env
```

Completa con tu ACCESS_KEY:
```env
PORCUPINE_ACCESS_KEY=tu_access_key_real_aqui
TRANSCRIPTION_SERVICE_URL=http://localhost:5000/transcribe
BUTTON_PIN=22
LED_IDLE_PIN=17
LED_RECORD_PIN=27
```

**🤖 Servicio de Transcripción:**

El asistente requiere que tengas un servicio de transcripción ejecutándose en `http://localhost:5000/transcribe`. 

Puedes cambiar la URL del servicio editando:
```yaml
- TRANSCRIPTION_SERVICE_URL=http://localhost:5000/transcribe
```

## 🚀 Instalación y uso

### 🎯 Opción 1: INSTALACIÓN AUTOMÁTICA (Recomendado)

**¡Todo en un solo comando!**
```bash
python3 instalar_asistente.py
```

Este script automatiza **todo el proceso**:
1. ✅ Configurar API Keys (Porcupine)
2. ✅ Descargar modelo en español
3. ✅ Verificar configuración  
4. ✅ Ejecutar asistente **en segundo plano**
5. ✅ Mostrar logs en tiempo real (opcional)

**⏱️ Tiempo: 3-5 minutos**

---

### 🔧 Opción 2: INSTALACIÓN MANUAL (Paso a paso)

#### 1. Clonar y configurar

```bash
git clone <tu-repo>
cd assistant
```

#### 2. Configurar API Keys

```bash
python3 configurar_access_key.py
```

#### 3. Descargar modelo en español (Recomendado)

```bash
python3 descargar_modelo_espanol.py
```

Este paso descarga el modelo base en español para que puedas usar tu wake word personalizado "Hola Puertocho" u "Oye Puertocho".

**Si no ejecutas este paso:** El asistente funcionará, pero usará wake words genéricos como "Hey Google" o "Alexa".

#### 4. Verificar configuración

```bash
python3 verificar_configuracion.py
```

#### 5. Ejecutar con Docker

```bash
# Construir y ejecutar (nueva sintaxis)
docker compose up --build

# Si tienes docker-compose antiguo
docker-compose up --build

# Ejecutar en background
docker compose up -d --build
```

---

### 🎮 Gestión del Asistente (cuando ya está configurado)

#### 🚀 Ejecutor Rápido
```bash
python3 ejecutar_asistente.py
```

**Opciones del menú interactivo:**
1. Ejecutar asistente (primer plano)
2. Ejecutar asistente (segundo plano) 
3. Ver estado del asistente
4. Ver logs en tiempo real
5. Detener asistente

**Opciones por línea de comandos:**
```bash
python3 ejecutar_asistente.py run      # Primer plano
python3 ejecutar_asistente.py start    # Segundo plano
python3 ejecutar_asistente.py stop     # Detener
python3 ejecutar_asistente.py status   # Ver estado
python3 ejecutar_asistente.py logs     # Ver logs
```

#### 6. Ver logs

```bash
python3 ejecutar_asistente.py logs
# o manualmente:
docker compose logs -f puertocho-assistant
```

## 🎯 Wake Words disponibles

### ✅ Con modelo en español (Recomendado)
Si ejecutaste `python3 descargar_modelo_espanol.py`:
- **"Hola Puertocho"**
- **"Oye Puertocho"**

### 🔄 Fallback (keywords genéricos)
Si no se puede usar el modelo en español:
- **"Hey Google"**
- **"Alexa"**

El asistente te indicará qué wake words está usando al iniciar.

## 🎯 Comandos disponibles

Los comandos están definidos en `app/commands.json`:

```json
{
  "enciende luz verde": { "pin": 17, "state": "on" },
  "apaga luz verde": { "pin": 17, "state": "off" },
  "enciende luz rojo": { "pin": 27, "state": "on" },
  "apaga luz rojo": { "pin": 27, "state": "off" }
}
```

## 💡 Cómo usar

1. **Wake Word**: Di "Hola Puertocho" u "Oye Puertocho"
2. **LED Verde** se apaga, **LED Rojo** se enciende
3. **Habla tu comando**: "enciende luz verde"
4. **Detección automática** de fin de comando por silencio
5. **Comando ejecutado** y vuelta al estado de espera

### Activación manual
- Presiona el **botón** (GPIO 22) para activar sin wake word
- Presiona nuevamente durante grabación para **cancelar**

## 🔧 Solución de problemas

### Error: "Necesitas configurar API Keys"
```bash
python3 configurar_access_key.py
```

### Error: "Failed to add edge detection" o "This channel is already in use"
✅ **CORREGIDO**: El nuevo código maneja estos errores automáticamente con:
- Cleanup inicial de GPIO
- Monitoreo por polling en lugar de interrupciones
- Manejo robusto de errores

### Error: "Keyword file (.ppn) and model file (.pv) should belong to the same language"
✅ **CORREGIDO**: El código ahora usa el modelo en español para Porcupine automáticamente

### Error de conexión con servicio de transcripción
- Verifica que el servicio de transcripción esté ejecutándose en `http://localhost:5000/transcribe`
- Revisa que el servicio responda correctamente con formato JSON: `{"transcription": "texto"}`
- Ejecuta `python3 verificar_configuracion.py` para diagnosticar

### Problemas de audio
- Verifica que el micrófono esté conectado correctamente
- Revisa permisos de Docker para acceder a `/dev/snd`

### LEDs no funcionan
- Verifica conexiones de hardware en GPIOs 17 y 27
- Asegúrate que Docker tenga acceso a GPIO con `privileged: true`

## 💰 Ventajas del servicio local

El asistente usa **servicio de transcripción HTTP local**:
- **Sin costos** por uso de API externa
- **Mayor privacidad**: Tu audio no sale de tu red local
- **Baja latencia**: Respuesta más rápida
- **Control total**: Puedes personalizar el servicio según tus necesidades

## 🚀 Modo segundo plano (Background)

El asistente se ejecuta en **segundo plano** por defecto:
- **🔄 Persistente**: Sigue funcionando aunque cierres la terminal
- **📋 Logs controlados**: Ve logs cuando quieras con `docker compose logs -f`
- **⚡ No bloquea**: Tu terminal queda libre para otros comandos
- **🎮 Control total**: Detener/reiniciar sin interrumpir otras tareas
- **📊 Monitoreo**: Verificar estado en cualquier momento

## 📁 Estructura del proyecto

```
assistant/
├── app/
│   ├── main.py                           # Código principal
│   ├── commands.json                     # Comandos disponibles
│   ├── requirements.txt                  # Dependencias Python
│   ├── LICENSE.txt                      # Licencia Porcupine
│   ├── Puerto-ocho_es_raspberry-pi_v3_0_0.ppn  # Modelo wake word personalizado
│   └── porcupine_params_es.pv           # Modelo base en español (descargado)
├── .env                                 # 🔑 CONFIGURACIÓN PERSONAL (crear desde env.example)
├── env.example                          # Plantilla de configuración
├── docker-compose.yml                   # Configuración Docker
├── Dockerfile                          # Imagen Docker
├── instalar_asistente.py               # 🚀 INSTALADOR AUTOMÁTICO
├── ejecutar_asistente.py               # 🎮 GESTOR DEL ASISTENTE
├── configurar_access_key.py            # Script configuración API Keys
├── descargar_modelo_espanol.py         # Script descarga modelo español
├── verificar_configuracion.py          # Script de verificación
├── CONFIGURACION_ENV.md                # 🔑 Guía configuración .env
├── INICIO_RAPIDO.md                    # Guía de inicio rápido
└── README.md                          # Documentación completa
```

### 🎯 Scripts principales

- **`instalar_asistente.py`** - Instalador automático completo
- **`ejecutar_asistente.py`** - Gestor para ejecutar/detener/monitorear
- **`configurar_access_key.py`** - Configurar API Keys
- **`descargar_modelo_espanol.py`** - Descargar modelo español
- **`verificar_configuracion.py`** - Verificar configuración

### 📋 Prerequisitos

**Asegúrate de tener el servicio de transcripción ejecutándose antes de iniciar el asistente:**

```bash
# El servicio debe estar disponible en:
curl -X POST http://localhost:5000/transcribe \
  -F "audio=@archivo.wav"

# Respuesta esperada:
{"transcription": "texto transcrito"}
```

## 🔄 Personalización

### Agregar nuevos comandos

Edita `app/commands.json`:

```json
{
  "tu nuevo comando": { "pin": 18, "state": "on" }
}
```

### Cambiar GPIOs

Edita `docker-compose.yml`:

```yaml
environment:
  - BUTTON_PIN=22        # GPIO del botón
  - LED_IDLE_PIN=17      # GPIO LED verde  
  - LED_RECORD_PIN=27    # GPIO LED rojo
```

## 📞 Soporte

Si tienes problemas:
1. Ejecuta: `python3 verificar_configuracion.py`
2. Revisa los logs: `docker compose logs -f`
3. Verifica la configuración de hardware
4. Asegúrate que tengas créditos en OpenAI 
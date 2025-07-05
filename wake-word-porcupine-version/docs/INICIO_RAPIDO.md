# 🚀 Inicio Rápido - Asistente Puertocho

Guía de 5 pasos para tener tu asistente funcionando en minutos.

## 🎯 Opción 1: INSTALACIÓN AUTOMÁTICA (Recomendado)

**¡Todo en un solo comando!**
```bash
python3 instalar_asistente.py
```

Este script hará automáticamente:
1. 🔍 Verificar si ya tienes configuración (si la tienes, te pregunta si quieres cambiarla)
2. 🔑 Configurar API Keys (Porcupine) solo si es necesario
3. 🌍 Descargar modelo en español
4. ✅ Verificar configuración
5. 🚀 Ejecutar asistente **en segundo plano**
6. 📋 Mostrar logs en tiempo real (opcional)

**⏱️ Tiempo: 3-5 minutos**

---

## 🔧 Opción 2: INSTALACIÓN MANUAL (Paso a paso)

### ✅ Paso 1: Configurar API Keys y Servicio de Transcripción
```bash
python3 configurar_access_key.py
```
**El script verifica automáticamente:**
- 🔍 Si ya tienes configuración válida (la mantiene si quieres)
- 🔑 Solo te pide Porcupine ACCESS_KEY si es necesario: [https://console.picovoice.ai/](https://console.picovoice.ai/)
- 🤖 Servicio de transcripción en: `http://localhost:5000/transcribe`

### ✅ Paso 2: Descargar modelo en español
```bash
python3 descargar_modelo_espanol.py
```
**Permite usar:** "Hola Puertocho" u "Oye Puertocho"

### ✅ Paso 3: Verificar todo está bien
```bash
python3 verificar_configuracion.py
```

### ✅ Paso 4: Verificar servicio de transcripción
Asegúrate de que el servicio esté ejecutándose:
```bash
curl -X POST http://localhost:5000/transcribe -F "audio=@test.wav"
```

### ✅ Paso 5: ¡Ejecutar!
```bash
# Opción 1: Instalador automático (recomendado - ejecuta en segundo plano)
python3 instalar_asistente.py

# Opción 2: Manualmente en segundo plano
docker compose up -d --build

# Ver logs en tiempo real
docker compose logs -f puertocho-assistant
```

---

## 🎮 Gestión del Asistente

### 🚀 Ejecutor Rápido (cuando ya está configurado)
```bash
python3 ejecutar_asistente.py
```

**Opciones disponibles:**
- `python3 ejecutar_asistente.py start` - ⭐ **Segundo plano (recomendado)**
- `python3 ejecutar_asistente.py logs` - 📋 **Ver logs en tiempo real**
- `python3 ejecutar_asistente.py status` - 📊 Ver estado
- `python3 ejecutar_asistente.py stop` - 🛑 Detener
- `python3 ejecutar_asistente.py run` - Primer plano (bloquea terminal)

### ✅ Paso 6: ¡Usar el asistente!

1. **🟢 LED Verde**: Listo para escuchar
2. **🎯 Di**: "Hola Puertocho" (o "Hey Google" si usas fallback)
3. **🔴 LED Rojo**: Grabando tu comando
4. **🎤 Habla**: "enciende luz verde"
5. **⚡ Ejecutado**: El comando se ejecuta automáticamente

## 🔧 Comandos disponibles

- "enciende luz verde"
- "apaga luz verde" 
- "enciende luz rojo"
- "apaga luz rojo"

## 🆘 Si algo falla

**Instalación completa:**
```bash
python3 instalar_asistente.py
```

**Solo configurar API Keys:**
```bash
python3 configurar_access_key.py
```

**Solo verificar:**
```bash
python3 verificar_configuracion.py
```

**Ver qué está pasando:**
```bash
python3 ejecutar_asistente.py logs
```

## 💡 Tips

- **Activación manual**: Presiona el **botón** (GPIO 22)
- **Segundo plano**: `python3 ejecutar_asistente.py start`
- **Detener**: `python3 ejecutar_asistente.py stop`

---
**¡Con el instalador automático tendrás tu asistente funcionando en 5 minutos!** 🎤✨ 
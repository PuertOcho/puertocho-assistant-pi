# 🛠️ Scripts Directory - Context Index

## 📋 Descripción General
Esta carpeta contiene scripts utilitarios y de prueba para el servicio de hardware de PuertoCho Assistant. Estos scripts están diseñados para facilitar el desarrollo, el debugging y la verificación de componentes de hardware específicos de forma interactiva.

---

## 📁 Archivos de Script

### `test_audio_manager.py` 🎙️
**Propósito**: Script interactivo para pruebas rápidas y debugging del `AudioManager` en tiempo real. Es ideal para verificar la configuración del micrófono y los niveles de audio.

**Funcionalidades**:
- **Prueba Completa**: Inicializa el `AudioManager`, graba durante unos segundos y muestra una visualización del volumen en tiempo real, junto con estadísticas del audio capturado.
- **Listado de Dispositivos**: Muestra todos los dispositivos de audio disponibles en el sistema para ayudar a identificar el hardware correcto.

**Uso**:
```bash
# Desde la carpeta raíz del proyecto
python3 puertocho-assistant-hardware/app/scripts/test_audio_manager.py
```

---

### `test_led_controller.py` 💡
**Propósito**: Script para probar visualmente los diferentes patrones y estados del `LEDController`. Permite verificar que las animaciones y colores funcionan como se espera.

**Funcionalidades**:
- **Prueba de Colores Básicos**: Recorre una serie de colores sólidos (rojo, verde, azul, etc.).
- **Prueba de Estados**: Muestra las animaciones de LED para cada estado del asistente (`IDLE`, `LISTENING`, `PROCESSING`, `ERROR`, etc.).
- **Prueba de Brillo**: Cambia el brillo de los LEDs para verificar el control de intensidad.
- **Prueba de Arcoíris**: Activa un patrón de arcoíris dinámico.

**Uso**:
```bash
# Desde la carpeta raíz del proyecto
python3 puertocho-assistant-hardware/app/scripts/test_led_controller.py
```

---

## 🎯 Diferencia con Tests Unitarios (`/tests`)

- **Scripts (`/scripts`)**: Diseñados para **pruebas interactivas y visuales** por un desarrollador. Requieren intervención manual y su salida es para consumo humano.
- **Tests Unitarios (`/tests`)**: Diseñados para **validación automatizada** (CI/CD). Se ejecutan sin intervención y producen reportes de éxito/fallo.

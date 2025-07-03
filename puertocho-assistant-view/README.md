# 🤖 PuertoCho Assistant Dashboard

Una aplicación QML moderna y funcional para controlar y monitorear el asistente de voz PuertoCho en Raspberry Pi.

## 📋 Características

- **🎯 Dashboard interactivo** con métricas del sistema en tiempo real
- **📊 Medidores visuales** (CPU, memoria, temperatura)
- **🎛️ Controles táctiles** optimizados para pantallas touch
- **⚡ Configuración rápida** de parámetros del asistente
- **🎨 Interfaz moderna** con animaciones fluidas
- **📱 Diseño responsive** adaptable a diferentes resoluciones

## 🛠️ Requisitos del Sistema

### Software necesario:
- **Qt 6.2 o superior** con módulos QML y Quick
- **CMake 3.16+**
- **GCC 7.0+ o Clang**
- **OpenGL ES** (para aceleración por GPU en Raspberry Pi)

### Para Raspberry Pi:
```bash
# Instalar Qt6 en Raspberry Pi OS
sudo apt update
sudo apt install qt6-base-dev qt6-declarative-dev qt6-tools-dev cmake build-essential

# Opcional: Para mejor rendimiento gráfico
sudo apt install libraspberrypi-dev
```

### Para Ubuntu/Debian:
```bash
sudo apt update
sudo apt install qt6-base-dev qt6-declarative-dev qt6-quick-dev cmake build-essential
```

### Para otras distribuciones:
Consulta la documentación de Qt6 para tu distribución específica.

## 🚀 Compilación e Instalación

### 1. Clonar/Acceder al proyecto
```bash
cd puertocho-assistant-view
```

### 2. Crear directorio de compilación
```bash
mkdir build
cd build
```

### 3. Configurar con CMake
```bash
# Configuración estándar
cmake ..

# O con configuraciones específicas para Raspberry Pi
cmake .. -DCMAKE_BUILD_TYPE=Release
```

### 4. Compilar
```bash
make -j$(nproc)
```

### 5. Ejecutar la aplicación
```bash
./PuertoChoAssistantView
```

## 📊 Funcionalidades del Dashboard

### Métricas del Sistema
- **💻 CPU**: Uso del procesador en tiempo real
- **💾 Memoria**: Uso de RAM del sistema
- **🌡️ Temperatura**: Temperatura del procesador

### Controles del Asistente
- **▶️ Iniciar/Pausar**: Control principal del asistente
- **🔄 Reiniciar**: Reinicio completo del sistema
- **⚙️ Configuración**: Acceso a ajustes avanzados

### Configuración Rápida
- **🔊 Volumen**: Control de volumen de salida
- **💬 Sensibilidad**: Sensibilidad del micrófono
- **🌙 Modo nocturno**: Tema oscuro/claro
- **🔔 Notificaciones**: Habilitar/deshabilitar alertas

## 🎨 Componentes Personalizados

El proyecto incluye componentes QML reutilizables:

### SystemGauge.qml
Medidor circular animado para mostrar métricas:
```qml
SystemGauge {
    title: "CPU"
    value: 65
    maxValue: 100
    gaugeColor: "#2196F3"
    units: "%"
}
```

### StatusCard.qml
Tarjeta de estado con animaciones:
```qml
StatusCard {
    title: "Asistente"
    value: "ACTIVO"
    icon: "🤖"
    isActive: true
}
```

## ⚙️ Configuración Avanzada

### Optimización para Raspberry Pi

Para mejorar el rendimiento en Raspberry Pi, edita `/boot/config.txt`:
```
# Habilitar aceleración GPU
gpu_mem=128
dtoverlay=vc4-kms-v3d

# Para pantallas táctiles
dtoverlay=rpi-display
```

### Variables de entorno útiles:
```bash
# Forzar OpenGL ES
export QT_OPENGL=es2

# Deshabilitar vsync si hay problemas de rendimiento
export QT_QPA_EGLFS_DISABLE_INPUT=1

# Para depuración
export QT_LOGGING_RULES="qt.qml.debug=true"
```

## 🐛 Solución de Problemas

### Error: "No se encuentra Qt6"
```bash
# Asegurarse de que Qt6 esté instalado
which qmake6

# Si no está disponible, instalar:
sudo apt install qt6-base-dev
```

### Error: "OpenGL no disponible"
```bash
# Verificar soporte OpenGL
glxinfo | grep OpenGL

# En Raspberry Pi, habilitar GPU en config.txt
sudo raspi-config
# Advanced Options > GL Driver > Enable
```

### Error de permisos de pantalla
```bash
# Agregar usuario al grupo de video
sudo usermod -a -G video $USER

# Logout y login nuevamente
```

### Rendimiento lento
```bash
# Verificar aceleración por hardware
export QT_LOGGING_RULES="qt.qpa.*=true"
./PuertoChoAssistantView

# Buscar en la salida: "Using OpenGL ES"
```

## 📝 Estructura del Proyecto

```
puertocho-assistant-view/
├── main.cpp              # Punto de entrada de la aplicación
├── main.qml              # Interfaz principal del dashboard
├── SystemGauge.qml       # Componente de medidor circular
├── StatusCard.qml        # Componente de tarjeta de estado
├── CMakeLists.txt        # Configuración de compilación
├── resources.qrc         # Archivo de recursos Qt
└── README.md            # Esta documentación
```

## 🔧 Desarrollo y Personalización

### Agregar nuevos componentes:
1. Crear archivo `.qml` con tu componente
2. Agregarlo a `resources.qrc`
3. Importarlo en `main.qml`

### Modificar estilos:
Los colores y estilos están definidos como propiedades en `main.qml`:
```qml
readonly property color primaryColor: "#2196F3"
readonly property color secondaryColor: "#FF9800"
```

### Conectar datos reales:
Reemplaza las simulaciones en `Timer` con datos reales del sistema:
```qml
// Reemplazar esto:
cpuUsage = Math.random() * 100

// Con llamadas reales al sistema
```

## 🤝 Contribuir

1. Fork del proyecto
2. Crear una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit de los cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

## 🎯 Próximas Funcionalidades

- [ ] **📈 Gráficas históricas** de métricas del sistema
- [ ] **🔊 Visualizador de audio** en tiempo real
- [ ] **📱 Aplicación móvil** complementaria
- [ ] **🌐 Panel web** de administración remota
- [ ] **🤖 Integración con APIs** de IA
- [ ] **📊 Exportación de datos** y reportes

## 📞 Soporte

¿Problemas o preguntas? 
- 📧 Email: soporte@puertocho.local
- 🐛 Issues: GitHub Issues
- 💬 Discord: PuertoCho Community

---

**¡Disfruta usando PuertoCho Assistant Dashboard! 🚀** 
# Documentación del módulo ReSpeaker 2-Mic Pi HAT V1.0

## Información del módulo

- **Modelo**: keyestudio ReSpeaker 2-Mic Pi HAT V1.0
- **Documentación**: https://docs.keyestudio.com/projects/KS0314/en/latest/docs/KS0314.html
- **Compatibilidad**: Raspberry Pi 3B, 4B (probado en 4B)

## Características del módulo

### Componentes integrados:
- **Codec de audio**: WM8960 (Low Power Stereo Codec)
- **Micrófonos**: 2 micrófonos estéreo (Mic L y Mic R)
- **LEDs RGB**: 3 LEDs APA102 RGB conectados al SPI
- **Botón**: 1 botón de usuario conectado a GPIO17
- **Conectores Grove**: 2 conectores para expansión
- **Salida de audio**: Jack 3.5mm y conector XH2.54-2P

### Alimentación:
- **Puerto Micro USB**: Para alimentar el módulo cuando se usan altavoces
- **Alimentación desde RPi**: El módulo también se alimenta desde los pines de la RPi

## Pinout y conexiones

### Pines ocupados por el módulo:
- **Audio (I2S)**: Usado por el codec WM8960
- **SPI**: Usado por los 3 LEDs APA102 RGB
- **GPIO17**: Botón integrado del módulo

### Pines disponibles para expansión:

#### 1. Grove I2C (Conector I2C-1)
- **GPIO2**: SDA (Data)
- **GPIO3**: SCL (Clock)
- **Uso**: Sensores I2C, pantallas, expansiones

#### 2. Grove GPIO12 (Puerto digital)
- **GPIO12**: Pin digital disponible
- **GPIO13**: Pin digital disponible
- **Uso**: LEDs externos, sensores digitales, relés

#### 3. Salidas de audio
- **Jack 3.5mm**: Para auriculares/altavoces
- **XH2.54-2P**: Para altavoces con conector específico

## Configuración de audio

### Instalación del driver:
```bash
# Descargar el driver desde:
# https://www.dropbox.com/scl/fo/4x60kwe9gpr3no0h6s2xl/AP9QcnN3ApKXkGh9CJPLDzU?rlkey=1sjn1xxr114zviozu0pguwpnd&e=1&dl=0

# Instalar
sudo apt-get update
sudo apt-get upgrade
unzip seeed-voicecard-6.1.zip
cd seeed-voicecard-6.1
sudo ./install.sh
sudo reboot
```

### Verificación de la instalación:
```bash
# Verificar dispositivos de audio
aplay -l
arecord -l

# Debe aparecer algo como "seeed-voicecard" o similar
```

### Prueba de audio:
```bash
# Grabar audio (5 segundos)
arecord -D "plughw:X,0" -f S16_LE -r 16000 -d 5 -t wav test.wav

# Reproducir audio
aplay -D "plughw:X,0" test.wav

# Nota: X es el número del dispositivo, puede variar (0, 1, 2, 3, etc.)
```

## Configuración para PuertoCho Assistant

### Variables de entorno recomendadas:
```bash
# Botón integrado del módulo
BUTTON_PIN=17

# LEDs externos en pines Grove disponibles
LED_IDLE_PIN=12
LED_RECORD_PIN=13

# Audio se detecta automáticamente
# El dispositivo aparecerá como "seeed-voicecard"
```

### Pines disponibles para expansión:
- **GPIO2, GPIO3**: I2C para sensores adicionales
- **GPIO12, GPIO13**: Puertos digitales para LEDs externos, sensores
- **LEDs RGB integrados**: 3 APA102 (requiere programación SPI)

## Ejemplos de uso

### 1. Usar LEDs externos en pines Grove
```python
import RPi.GPIO as GPIO

# Configurar LEDs externos
GPIO.setmode(GPIO.BCM)
GPIO.setup(12, GPIO.OUT)  # LED idle
GPIO.setup(13, GPIO.OUT)  # LED record

# Encender LED idle
GPIO.output(12, GPIO.HIGH)
GPIO.output(13, GPIO.LOW)
```

### 2. Leer botón integrado
```python
import RPi.GPIO as GPIO

# Configurar botón (pull-up interno)
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Leer estado (LOW cuando se presiona)
button_state = GPIO.input(17)
```

### 3. Usar I2C para sensores
```python
import smbus

# Crear objeto I2C
i2c = smbus.SMBus(1)  # I2C-1 (Grove I2C)

# Ejemplo: leer sensor en dirección 0x48
data = i2c.read_byte(0x48)
```

## Notas importantes

1. **Compatibilidad**: Probado principalmente en Raspberry Pi 4B
2. **Alimentación**: Usar puerto Micro USB cuando se conecten altavoces
3. **LEDs RGB**: Los LEDs APA102 integrados requieren programación SPI específica
4. **Estabilidad**: Los LEDs RGB pueden ser inestables cuando hay altavoces conectados
5. **Número de dispositivo**: El número del dispositivo de audio puede variar según el sistema

## Troubleshooting

### Audio no funciona:
1. Verificar que el driver esté instalado correctamente
2. Comprobar con `aplay -l` y `arecord -l`
3. Probar diferentes números de dispositivo (0, 1, 2, 3)

### LEDs no funcionan:
1. Verificar conexiones en pines GPIO12 y GPIO13
2. Los LEDs RGB integrados requieren programación SPI
3. Revisar alimentación del módulo

### Botón no responde:
1. Verificar que esté conectado a GPIO17
2. Usar pull-up interno en la configuración
3. El botón da LOW cuando se presiona

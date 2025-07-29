# Dockerfile para PuertoCho Assistant Hardware Service
# Optimizado para Raspberry Pi 4B con ARM64

# Etapa de compilación para descargar artefactos
FROM python:3.11-slim-bullseye as build-stage

# Instalar wget
RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*

# Crear directorio para modelos
WORKDIR /tmp/models

# Descargar modelos de Porcupine (ejemplos, reemplaza con tus URLs)
# RUN wget -q https://github.com/Picovoice/porcupine/raw/master/resources/keyword_files/raspberry-pi/porcupine_raspberry-pi.ppn -O porcupine.ppn
# RUN wget -q https://github.com/Picovoice/porcupine/raw/master/resources/keyword_files/raspberry-pi/blueberry_raspberry-pi.ppn -O blueberry.ppn

# --- Etapa final ---
FROM python:3.11-slim-bullseye

# Metadatos del contenedor
LABEL maintainer="PuertOcho <puertocho@example.com>"
LABEL version="1.0.0"
LABEL description="Hardware service for PuertoCho Assistant on Raspberry Pi"

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Madrid

# Crear usuario no-root para seguridad
RUN groupadd -r puertocho && useradd -r -g puertocho puertocho

# Agregar usuario al grupo audio para acceso a dispositivos de audio
RUN usermod -a -G audio puertocho

# Agregar usuario al grupo gpio para acceso a dispositivos GPIO
RUN groupadd -f gpio && usermod -a -G gpio puertocho

# Agregar usuario al grupo spi para acceso a dispositivos SPI
RUN groupadd -f spi && usermod -a -G spi puertocho

# Agregar usuario al grupo i2c para acceso a dispositivos I2C
RUN groupadd -f i2c && usermod -a -G i2c puertocho

# Actualizar sistema y instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    # Audio dependencies
    alsa-utils \
    libasound2-dev \
    pulseaudio \
    pulseaudio-utils \
    portaudio19-dev \
    # Hardware dependencies
    i2c-tools \
    libi2c-dev \
    spi-tools \
    # Build dependencies
    build-essential \
    gcc \
    g++ \
    pkg-config \
    libffi-dev \
    # System utilities
    curl \
    wget \
    git \
    nano \
    # Python dependencies
    python3-dev \
    python3-pip \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configurar timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Crear directorio de trabajo
WORKDIR /app

# Upgrade pip una sola vez
RUN pip install --upgrade pip

# Crear directorio requirements
RUN mkdir -p /app/requirements

# Copiar e instalar cada archivo de requirements individualmente para aprovechar el cache
COPY app/requirements/requirements-core.txt /app/requirements/
RUN pip install -r /app/requirements/requirements-core.txt

COPY app/requirements/requirements-logging.txt /app/requirements/
RUN pip install -r /app/requirements/requirements-logging.txt

COPY app/requirements/requirements-audio.txt /app/requirements/
RUN pip install -r /app/requirements/requirements-audio.txt

COPY app/requirements/requirements-hardware.txt /app/requirements/
RUN pip install -r /app/requirements/requirements-hardware.txt

COPY app/requirements/requirements-wakeword.txt /app/requirements/
RUN pip install -r /app/requirements/requirements-wakeword.txt

COPY app/requirements/requirements-http.txt /app/requirements/
RUN pip install -r /app/requirements/requirements-http.txt

COPY app/requirements/requirements-nfc.txt /app/requirements/
RUN pip install -r /app/requirements/requirements-nfc.txt

COPY app/requirements/requirements-test.txt /app/requirements/
RUN pip install -r /app/requirements/requirements-test.txt

COPY app/requirements/requirements-dev.txt /app/requirements/
RUN pip install -r /app/requirements/requirements-dev.txt

# Crear estructura de directorios
RUN mkdir -p /app/logs \
    /app/config \
    /app/data \
    /app/models \
    /app/scripts \
    /app/tests 

# Copiar scripts primero
COPY scripts/ /app/scripts/

# Copiar código fuente de la aplicación
COPY app/ /app/

# Copiar modelos de Porcupine (si existen) desde la etapa de compilación
COPY --from=build-stage /tmp/models/ /app/models/

# Configurar permisos
RUN chown -R puertocho:puertocho /app && \
    chmod +x /app/scripts/*.py 2>/dev/null || true && \
    chmod +x /app/scripts/*.sh 2>/dev/null || true

# Exponer puertos
EXPOSE 8080
EXPOSE 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Configurar punto de entrada
# Para acceso a GPIO necesitamos ejecutar como root
# USER puertocho
CMD ["python", "main.py"]
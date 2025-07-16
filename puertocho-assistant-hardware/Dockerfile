# Dockerfile simplificado - usando imagen base completa
FROM python:3.11

# Configurar variables de entorno
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONUNBUFFERED=1

# Solución específica para Raspberry Pi 32-bit - configurar repositorios confiables
RUN echo "deb [trusted=yes] http://deb.debian.org/debian bookworm main" > /etc/apt/sources.list && \
    echo "deb [trusted=yes] http://deb.debian.org/debian bookworm-updates main" >> /etc/apt/sources.list && \
    echo "deb [trusted=yes] http://deb.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y \
    libasound2-dev \
    libffi-dev \
    portaudio19-dev \
    python3-dev \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY app /app

CMD ["python", "-u", "main.py"]

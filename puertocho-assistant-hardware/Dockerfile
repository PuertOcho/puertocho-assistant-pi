# Dockerfile para Raspberry Pi 32-bit - Alpine Linux
FROM python:3.11-alpine

# Configurar variables de entorno
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema con apk (Alpine)
RUN apk add --no-cache \
    gcc \
    g++ \
    musl-dev \
    alsa-lib-dev \
    libffi-dev \
    portaudio-dev \
    linux-headers \
    && rm -rf /var/cache/apk/*

WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY app /app

CMD ["python", "-u", "main.py"]

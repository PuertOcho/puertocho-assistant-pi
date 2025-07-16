# Dockerfile simplificado - usando imagen base completa
FROM python:3.11

# Configurar variables de entorno
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema necesarias para audio, GPIO y compilación
# La imagen python:3.11 ya tiene build-essential, gcc, etc.
RUN apt-get update && apt-get install -y \
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

# Dockerfile simplificado
FROM python:3.11-slim

# Instalar dependencias del sistema necesarias para audio, GPIO y compilación
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libasound2-dev \
    libffi-dev \
    portaudio19-dev \
    python3-dev \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app

# Desactivar buffering de Python para logs en tiempo real
ENV PYTHONUNBUFFERED=1

CMD ["python", "-u", "main.py"]

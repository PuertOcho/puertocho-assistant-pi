# Dockerfile para PuertoCho Assistant Backend
FROM python:3.11-slim

# Configurar variables de entorno
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1

# Instalar solo las dependencias básicas necesarias
RUN apt-get update --allow-releaseinfo-change --allow-unauthenticated || \
    apt-get update --allow-unauthenticated && \
    apt-get install -y --no-install-recommends --allow-unauthenticated \
    gcc \
    g++ \
    libc-dev \
    make \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt .

# Actualizar pip y instalar dependencias con preferencia por wheels
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --prefer-binary -r requirements.txt

# Copiar código fuente
COPY src/ ./src/

# Exponer puerto
EXPOSE 8765

# Comando por defecto
CMD ["python", "src/main.py"]

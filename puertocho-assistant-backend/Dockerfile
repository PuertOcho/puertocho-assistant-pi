# Dockerfile simple para PuertoCho Assistant Backend Gateway
# Usar imagen base Python estándar para evitar problemas de compilación
FROM python:3.11-slim

# Configurar variables de entorno
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Instalar dependencias del sistema y herramientas de compilación
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gcc \
    g++ \
    make \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Limpiar herramientas de compilación para reducir tamaño de imagen
RUN apt-get purge -y \
    gcc \
    g++ \
    make \
    build-essential \
    python3-dev \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar código fuente
COPY src/ ./src/

# Crear directorio para logs y datos temporales
RUN mkdir -p /app/logs /app/temp

# Exponer puerto del backend gateway
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:8000/health || exit 1

# Comando por defecto
CMD ["python", "src/main.py"]

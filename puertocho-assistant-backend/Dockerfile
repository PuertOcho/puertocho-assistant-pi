# Dockerfile para PuertoCho Assistant Backend
FROM python:3.11-slim

# Instalar dependencias del sistema necesarias para compilar paquetes nativos
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libc-dev \
    make \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt .

# Actualizar pip y instalar dependencias
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY src/ ./src/

# Exponer puerto
EXPOSE 8765

# Comando por defecto
CMD ["python", "src/main.py"]

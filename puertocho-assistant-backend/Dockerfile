# Dockerfile para PuertoCho Assistant Backend
# Usar imagen base que ya tiene herramientas de compilación
FROM python:3.11

# Configurar variables de entorno
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1

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

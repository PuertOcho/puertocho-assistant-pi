# Dockerfile simplificado para desarrollo en Raspberry Pi
FROM nginx:alpine

# Instalar Node.js para servir como fallback
RUN apk add --no-cache nodejs npm

# Crear directorio para la aplicación
WORKDIR /app

# Copiar archivos de desarrollo directamente
COPY package*.json ./
COPY src/ ./src/
COPY static/ ./static/
COPY svelte.config.js ./
COPY vite.config.ts ./
COPY tsconfig.json ./

# Copiar configuración de nginx optimizada
COPY nginx.conf /etc/nginx/nginx.conf

# Crear directorio build temporal (se llenará en runtime)
RUN mkdir -p /usr/share/nginx/html && \
    echo '<!DOCTYPE html><html><head><title>Loading...</title></head><body><h1>Starting PuertoCho Assistant...</h1><script>setTimeout(() => location.reload(), 3000);</script></body></html>' > /usr/share/nginx/html/index.html

# Instalar dependencias para modo kiosko
RUN apk add --no-cache \
    curl \
    bash \
    xorg-server \
    xf86-video-fbdev \
    chromium \
    xdotool \
    xset \
    supervisor \
    && mkdir -p /var/log/supervisor

# Copiar scripts de kiosko
COPY scripts/ /opt/kiosk/
RUN chmod +x /opt/kiosk/*.sh

# Crear directorios para logs
RUN mkdir -p /var/log/kiosk && \
    chmod 755 /var/log/kiosk

# Configuración de supervisor para gestionar servicios
COPY supervisor.conf /etc/supervisor/conf.d/puertocho-kiosk.conf

# Variables de entorno por defecto para kiosko
ENV KIOSK_MODE=false \
    KIOSK_RESOLUTION=1920x1080 \
    DASHBOARD_URL=http://localhost:3000 \
    KIOSK_BROWSER=chromium-browser \
    KIOSK_RESTART_DELAY=5 \
    DISPLAY=:0

# Exponer puerto 3000 (coincide con desarrollo)
EXPOSE 3000

# Script de entrada que soporta tanto modo normal como kiosko
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Comando para ejecutar el contenedor
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx"]

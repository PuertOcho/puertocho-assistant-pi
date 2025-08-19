# Dockerfile para PuertoCho Assistant Web Dashboard
# Soporta tanto hot-reload como producción según variables de entorno

FROM node:18-alpine

# Instalar dependencias del sistema necesarias
RUN apk add --no-cache \
    curl \
    bash \
    xorg-server \
    xf86-video-fbdev \
    chromium \
    xdotool \
    xset \
    supervisor \
    nginx \
    && mkdir -p /var/log/supervisor /var/log/kiosk

WORKDIR /app

# Copiar archivos de configuración del proyecto
COPY package*.json ./
COPY svelte.config.js ./
COPY vite.config.ts ./
COPY tsconfig.json ./

# Instalar dependencias de Node.js
RUN npm install

# Copiar código fuente
COPY src/ ./src/
COPY static/ ./static/

# Crear directorios necesarios
RUN mkdir -p /usr/share/nginx/html /var/log/kiosk /tmp/chromium-data && \
    chmod 755 /var/log/kiosk && \
    chmod 755 /tmp/chromium-data

# Copiar scripts y configuraciones
COPY scripts/ /opt/kiosk/
COPY supervisor.conf /etc/supervisor/conf.d/puertocho-kiosk.conf
COPY nginx.conf /etc/nginx/nginx.conf
COPY docker-entrypoint.sh /docker-entrypoint.sh

RUN chmod +x /opt/kiosk/*.sh /docker-entrypoint.sh

# Variables de entorno por defecto
ENV HOT_RELOAD_ENABLED=false \
    VITE_HMR_PORT=24678 \
    CHOKIDAR_USEPOLLING=true \
    CHOKIDAR_INTERVAL=1000 \
    KIOSK_MODE=false \
    KIOSK_RESOLUTION=1920x1080 \
    DASHBOARD_URL=http://localhost:3000 \
    KIOSK_BROWSER=chromium-browser \
    KIOSK_RESTART_DELAY=5 \
    DISPLAY=:0

EXPOSE 3000 24678

ENTRYPOINT ["/docker-entrypoint.sh"]

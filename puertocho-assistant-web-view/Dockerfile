# Multi-stage build optimizado para Raspberry Pi con soporte para modo kiosko
# Etapa 1: Build de la aplicación
FROM node:20-alpine AS builder

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de configuración
COPY package*.json ./
COPY svelte.config.js ./
COPY vite.config.ts ./
COPY tsconfig.json ./

# Instalar dependencias
RUN npm ci

# Copiar código fuente
COPY src/ ./src/
COPY static/ ./static/

# Construir la aplicación para producción
RUN npm run build

# Etapa 2: Servidor de producción con soporte kiosko
FROM nginx:alpine

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

# Copiar archivos construidos al directorio de nginx
COPY --from=builder /app/build /usr/share/nginx/html

# Copiar configuración personalizada de nginx
COPY nginx.conf /etc/nginx/nginx.conf

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

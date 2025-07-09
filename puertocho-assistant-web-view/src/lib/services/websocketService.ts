import { browser } from '$app/environment';
import { assistantStatus, commandHistory, isConnected } from '$lib/stores/assistantStore';

let socket: WebSocket | null = null;

const WEBSOCKET_URL = 'ws://localhost:8765/ws'; // URL del backend WebSocket

export function connect() {
  // Solo conectar en el navegador, no en el servidor (SSR)
  if (!browser) return;
  
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    return;
  }

  socket = new WebSocket(WEBSOCKET_URL);

  socket.onopen = () => {
    console.log('WebSocket connection established');
    isConnected.set(true);
  };

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'status_update') {
      assistantStatus.set(data.payload.status);
    }

    if (data.type === 'command_log') {
      const newCommand = {
        timestamp: new Date(data.payload.timestamp).toLocaleTimeString(),
        command: data.payload.command,
      };
      commandHistory.update(history => [...history, newCommand]);
    }
  };

  socket.onclose = () => {
    console.log('WebSocket connection closed. Reconnecting...');
    isConnected.set(false);
    setTimeout(connect, 3000); // Reintentar conexión cada 3 segundos
  };

  socket.onerror = (error) => {
    console.error('WebSocket error:', error);
    isConnected.set(false);
    assistantStatus.set('error');
    socket?.close();
  };
}

export function sendMessage(message: object) {
  if (!browser) return;
  
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(message));
  } else {
    console.error('WebSocket is not connected.');
  }
}

// Iniciar la conexión al cargar el módulo solo en el navegador
if (browser) {
  connect();
}

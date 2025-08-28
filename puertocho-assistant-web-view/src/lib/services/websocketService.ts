import { browser } from '$app/environment';
import { assistantStatus, commandHistory, isConnected, audioProcessingState, audioHistory } from '$lib/stores/assistantStore';
import { addUserMessage, addAssistantMessage, updateMessageTranscription } from '$lib/stores/chatStore';

let socket: WebSocket | null = null;

const WEBSOCKET_URL = 'ws://localhost:8000/ws'; // URL del backend WebSocket

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
    console.log('WebSocket message received:', data.type, data);
    
    // Unified state updates from backend
    if (data.type === 'unified_state_update') {
      const payload = data.payload;
      
      // Update assistant status based on hardware state
      if (payload.hardware?.state) {
        const hardwareState = payload.hardware.state.toLowerCase();
        if (hardwareState.includes('listening')) {
          assistantStatus.set('listening');
        } else if (hardwareState.includes('processing')) {
          assistantStatus.set('processing');
        } else {
          assistantStatus.set('idle');
        }
      }
      
      // Update audio processing state
      if (payload.backend?.audio_processor) {
        audioProcessingState.update(current => ({
          ...current,
          status: payload.backend.audio_processor.status || 'idle',
          queue_length: payload.backend.audio_processor.queue_length || 0,
          total_processed: payload.backend.audio_processor.total_processed || current.total_processed
        }));
      }
    }

    // Audio processing events
    if (data.type === 'audio_processing') {
      const payload = data.payload;
      
      audioProcessingState.update(current => ({
        ...current,
        status: payload.status || current.status,
        current_audio: payload.current_audio ? {
          id: payload.current_audio.id || Date.now().toString(),
          filename: payload.current_audio.filename || 'unknown',
          timestamp: payload.current_audio.timestamp || new Date().toISOString(),
          duration: payload.current_audio.duration || 0,
          size: payload.current_audio.size || 0,
          status: payload.current_audio.status || 'processing',
          quality_score: payload.current_audio.quality_score
        } : current.current_audio
      }));
      
      // Add to history if completed
      if (payload.status === 'completed' && payload.current_audio) {
        const audioItem = {
          id: payload.current_audio.id || Date.now().toString(),
          filename: payload.current_audio.filename || 'unknown',
          timestamp: payload.current_audio.timestamp || new Date().toISOString(),
          duration: payload.current_audio.duration || 0,
          size: payload.current_audio.size || 0,
          status: 'completed' as const,
          quality_score: payload.current_audio.quality_score,
          url: payload.current_audio.url
        };
        
        audioHistory.update(history => [audioItem, ...history].slice(0, 50)); // Keep last 50 items
        
        // Add to chat if it has URL (verification file)
        if (payload.current_audio.url) {
          addUserMessage(
            payload.current_audio.url,
            payload.current_audio.filename,
            payload.current_audio.transcription || payload.transcription
          );
        }
      }
      
      // Handle transcription updates
      if (payload.transcription && payload.current_audio?.id) {
        updateMessageTranscription(`user_${payload.current_audio.id}`, payload.transcription);
      }
    }

    // Hardware events (eventos en tiempo real con mayor prioridad)
    if (data.type === 'hardware_event') {
      const payload = data.payload;
      
      if (payload.event_type === 'voice_activity_start') {
        assistantStatus.set('listening');
      } else if (payload.event_type === 'voice_activity_end') {
        assistantStatus.set('processing');
      } else if (payload.event_type === 'audio_sent_to_backend') {
        audioProcessingState.update(current => ({
          ...current,
          status: 'receiving'
        }));
      }
    }

    // Legacy message handling
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

    // Assistant response events
    if (data.type === 'assistant_response') {
      const payload = data.payload;
      
      if (payload.text && payload.audio_url) {
        // Complete response with both text and audio
        addAssistantMessage(payload.text, payload.audio_url, payload.audio_filename);
      } else if (payload.text) {
        // Text-only response
        addAssistantMessage(payload.text);
      }
    }

    // Connection info
    if (data.type === 'connection_info') {
      console.log('Backend connection established:', data.payload.message);
    }

    // Initial state
    if (data.type === 'initial_state') {
      const payload = data.payload;
      
      // Set initial hardware state
      if (payload.hardware?.state) {
        const hardwareState = payload.hardware.state.toLowerCase();
        if (hardwareState.includes('listening')) {
          assistantStatus.set('listening');
        } else if (hardwareState.includes('processing')) {
          assistantStatus.set('processing');
        } else {
          assistantStatus.set('idle');
        }
      }
      
      // Set initial audio processing state
      if (payload.backend?.audio_processor) {
        audioProcessingState.set({
          status: payload.backend.audio_processor.status || 'idle',
          queue_length: payload.backend.audio_processor.queue_length || 0,
          total_processed: payload.backend.audio_processor.total_processed || 0,
          verification_files: []
        });
      }
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

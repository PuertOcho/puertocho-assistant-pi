// Tipos centralizados para la aplicación

export interface AudioState {
  isRecording: boolean;
  isPlaying: boolean;
  volume: number;
  currentFile?: string;
}

export interface AssistantState {
  status: 'listening' | 'processing' | 'idle' | 'error';
  isActive: boolean;
  isListening: boolean;
  lastCommand: string | null;
  response: string | null;
}

export interface WebSocketMessage {
  type: 'command' | 'response' | 'status' | 'audio';
  payload: any;
  timestamp?: number;
}

export interface CommandHistoryItem {
  id: string;
  command: string;
  response?: string;
  timestamp: number;
  status: 'success' | 'error' | 'pending';
}

export interface AudioProcessingState {
  status: 'idle' | 'receiving' | 'processing' | 'completed';
  queue_length: number;
  current_file?: string;
  error?: string;
}

export type StatusType = 'listening' | 'processing' | 'idle' | 'error';

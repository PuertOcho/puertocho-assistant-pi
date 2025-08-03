import { writable } from 'svelte/store';

type AssistantStatus = 'listening' | 'processing' | 'idle' | 'error';
type Command = {
  timestamp: string;
  command: string;
};

// Audio processing types
type AudioProcessingStatus = 'idle' | 'receiving' | 'processing' | 'completed' | 'error';
type AudioFile = {
  id: string;
  filename: string;
  timestamp: string;
  duration: number;
  size: number;
  status: 'processing' | 'completed' | 'error';
  quality_score?: number;
  url?: string;
};

type AudioProcessingState = {
  status: AudioProcessingStatus;
  current_audio?: AudioFile;
  queue_length: number;
  total_processed: number;
  verification_files: AudioFile[];
};

export const assistantStatus = writable<AssistantStatus>('idle');
export const commandHistory = writable<Command[]>([]);
export const isConnected = writable<boolean>(false);

// Audio processing stores
export const audioProcessingState = writable<AudioProcessingState>({
  status: 'idle',
  queue_length: 0,
  total_processed: 0,
  verification_files: []
});

export const audioHistory = writable<AudioFile[]>([]);

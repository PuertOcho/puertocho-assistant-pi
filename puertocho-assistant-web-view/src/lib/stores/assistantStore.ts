import { writable } from 'svelte/store';

type AssistantStatus = 'listening' | 'processing' | 'idle' | 'error';
type Command = {
  timestamp: string;
  command: string;
};

export const assistantStatus = writable<AssistantStatus>('idle');
export const commandHistory = writable<Command[]>([]);
export const isConnected = writable<boolean>(false);

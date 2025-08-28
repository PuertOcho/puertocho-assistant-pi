import { writable } from 'svelte/store';

export interface ChatMessage {
  id: string;
  timestamp: Date;
  type: 'user' | 'assistant';
  text?: string;
  audioUrl?: string;
  audioFilename?: string;
  transcription?: string;
  response?: string;
  isPlaying?: boolean;
  status?: 'processing' | 'completed' | 'error';
}

export interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  currentPlayingId: string | null;
}

const initialState: ChatState = {
  messages: [],
  isLoading: false,
  currentPlayingId: null
};

export const chatStore = writable<ChatState>(initialState);

export function addUserMessage(audioUrl: string, audioFilename: string, transcription?: string) {
  chatStore.update(state => ({
    ...state,
    messages: [
      ...state.messages,
      {
        id: `user_${Date.now()}`,
        timestamp: new Date(),
        type: 'user',
        audioUrl,
        audioFilename,
        transcription,
        status: transcription ? 'completed' : 'processing',
        isPlaying: false
      }
    ]
  }));
}

export function addAssistantMessage(text: string, audioUrl?: string, audioFilename?: string) {
  chatStore.update(state => ({
    ...state,
    messages: [
      ...state.messages,
      {
        id: `assistant_${Date.now()}`,
        timestamp: new Date(),
        type: 'assistant',
        text,
        response: text,
        audioUrl,
        audioFilename,
        status: 'completed',
        isPlaying: false
      }
    ]
  }));
}

export function updateMessageTranscription(messageId: string, transcription: string) {
  chatStore.update(state => ({
    ...state,
    messages: state.messages.map(msg => 
      msg.id === messageId 
        ? { ...msg, transcription, status: 'completed' as const }
        : msg
    )
  }));
}

export function setAudioPlaying(messageId: string | null) {
  chatStore.update(state => ({
    ...state,
    currentPlayingId: messageId,
    messages: state.messages.map(msg => ({
      ...msg,
      isPlaying: msg.id === messageId
    }))
  }));
}

export function clearChat() {
  chatStore.update(state => ({
    ...state,
    messages: []
  }));
}

export function setLoading(loading: boolean) {
  chatStore.update(state => ({
    ...state,
    isLoading: loading
  }));
}
/**
 * Audio Store - Centralized audio state management
 * Separates audio logic from main assistant store for better scalability
 */

import { writable, derived, get } from 'svelte/store';
import { refreshAudioData, type AudioFile, type AudioVerificationStatus, type AudioProcessingHistory } from '$lib/services/audioApiService';

// Audio processing types
export type AudioProcessingStatus = 'idle' | 'receiving' | 'processing' | 'completed' | 'error';

export interface AudioProcessingState {
  status: AudioProcessingStatus;
  current_audio?: AudioFile;
  queue_length: number;
  total_processed: number;
  last_update: Date;
}

export interface AudioStoreState {
  processing: AudioProcessingState;
  verification: AudioVerificationStatus | null;
  history: AudioFile[];
  isLoading: boolean;
  error: string | null;
  lastSync: Date | null;
}

// Initial state
const initialState: AudioStoreState = {
  processing: {
    status: 'idle',
    queue_length: 0,
    total_processed: 0,
    last_update: new Date()
  },
  verification: null,
  history: [],
  isLoading: false,
  error: null,
  lastSync: null
};

// Main audio store
export const audioStore = writable<AudioStoreState>(initialState);

// Derived stores for easy component access
export const audioProcessingState = derived(audioStore, $store => $store.processing);
export const audioHistory = derived(audioStore, $store => $store.history);
export const audioVerificationStatus = derived(audioStore, $store => $store.verification);
export const audioIsLoading = derived(audioStore, $store => $store.isLoading);
export const audioError = derived(audioStore, $store => $store.error);

// Actions
export const audioActions = {
  /**
   * Update processing state from WebSocket messages
   */
  updateProcessingState: (update: Partial<AudioProcessingState>) => {
    audioStore.update(state => ({
      ...state,
      processing: {
        ...state.processing,
        ...update,
        last_update: new Date()
      },
      error: null
    }));
  },

  /**
   * Add new audio file to history
   */
  addToHistory: (audioFile: AudioFile) => {
    audioStore.update(state => ({
      ...state,
      history: [audioFile, ...state.history.filter(f => f.id !== audioFile.id)].slice(0, 100), // Keep last 100
      error: null
    }));
  },

  /**
   * Update audio file in history
   */
  updateHistoryFile: (fileId: string, updates: Partial<AudioFile>) => {
    audioStore.update(state => ({
      ...state,
      history: state.history.map(file => 
        file.id === fileId ? { ...file, ...updates } : file
      )
    }));
  },

  /**
   * Set loading state
   */
  setLoading: (loading: boolean) => {
    audioStore.update(state => ({
      ...state,
      isLoading: loading
    }));
  },

  /**
   * Set error state
   */
  setError: (error: string | null) => {
    audioStore.update(state => ({
      ...state,
      error,
      isLoading: false
    }));
  },

  /**
   * Sync with backend API
   */
  syncWithBackend: async () => {
    try {
      audioActions.setLoading(true);
      audioActions.setError(null);

      const data = await refreshAudioData();
      
      audioStore.update(state => ({
        ...state,
        verification: data.status,
        history: data.files.map(file => ({
          ...file,
          // Ensure required fields
          status: 'completed' as const,
          timestamp: file.created_at
        })),
        processing: {
          ...state.processing,
          total_processed: data.history.total_processed,
          queue_length: data.history.processing_queue_length
        },
        lastSync: new Date(),
        isLoading: false,
        error: null
      }));

    } catch (error) {
      console.error('Failed to sync audio data:', error);
      audioActions.setError(error instanceof Error ? error.message : 'Failed to sync audio data');
    }
  },

  /**
   * Clear all data
   */
  reset: () => {
    audioStore.set(initialState);
  },

  /**
   * Get current state (for debugging)
   */
  getCurrentState: () => get(audioStore)
};

// Auto-sync functionality
let syncInterval: number | null = null;

export const audioSync = {
  /**
   * Start automatic syncing with backend
   */
  start: (intervalMs: number = 30000) => { // Default 30 seconds
    if (syncInterval) audioSync.stop();
    
    // Initial sync
    audioActions.syncWithBackend();
    
    // Periodic sync
    syncInterval = setInterval(() => {
      audioActions.syncWithBackend();
    }, intervalMs);
  },

  /**
   * Stop automatic syncing
   */
  stop: () => {
    if (syncInterval) {
      clearInterval(syncInterval);
      syncInterval = null;
    }
  },

  /**
   * Force immediate sync
   */
  forceSync: () => {
    audioActions.syncWithBackend();
  }
};

// Cleanup on module unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    audioSync.stop();
  });
}

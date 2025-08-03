<script lang="ts">
  import { audioProcessingState } from '$lib/stores/assistantStore';
  
  export let status: 'listening' | 'processing' | 'idle' | 'error' = 'idle';

  const statusInfo = {
    idle: { text: 'Esperando', color: '#6b7280', icon: '⏸️' },
    listening: { text: 'Escuchando...', color: '#3b82f6', icon: '🎙️' },
    processing: { text: 'Procesando...', color: '#f59e0b', icon: '⚡' },
    error: { text: 'Error', color: '#ef4444', icon: '❌' },
  };

  $: currentStatus = statusInfo[status] || statusInfo.idle;
  $: audioStatus = $audioProcessingState.status;
  $: audioQueueLength = $audioProcessingState.queue_length;
</script>

<div class="status-container">
  <!-- Main status -->
  <div class="status-indicator">
    <span class="status-icon">{currentStatus.icon}</span>
    <span class="status-dot" style="background-color: {currentStatus.color};"></span>
    <span class="status-text">{currentStatus.text}</span>
  </div>
  
  <!-- Audio processing status -->
  {#if audioStatus !== 'idle' || audioQueueLength > 0}
    <div class="audio-status">
      <span class="audio-icon">
        {#if audioStatus === 'receiving'}
          📥
        {:else if audioStatus === 'processing'}
          ⚡
        {:else if audioStatus === 'completed'}
          ✅
        {:else if audioStatus === 'error'}
          ❌
        {:else}
          🎵
        {/if}
      </span>
      <span class="audio-text">
        {#if audioQueueLength > 0}
          Audio: {audioQueueLength} en cola
        {:else}
          Audio: {audioStatus}
        {/if}
      </span>
    </div>
  {/if}
</div>

<style>
  .status-container {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    align-items: center;
  }
  
  .status-indicator {
    display: flex;
    align-items: center;
    padding: 0.75rem 1.25rem;
    border-radius: 9999px;
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    font-family: sans-serif;
  }

  .status-icon {
    font-size: 1.2em;
    margin-right: 0.5rem;
  }

  .status-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 0.75rem;
    animation: pulse 2s infinite;
  }

  .status-text {
    font-weight: 500;
    color: #374151;
    font-size: 0.95rem;
  }
  
  .audio-status {
    display: flex;
    align-items: center;
    padding: 0.5rem 1rem;
    border-radius: 9999px;
    background-color: #f3f4f6;
    border: 1px solid #d1d5db;
    font-family: sans-serif;
  }
  
  .audio-icon {
    font-size: 1em;
    margin-right: 0.5rem;
  }
  
  .audio-text {
    font-weight: 400;
    color: #6b7280;
    font-size: 0.85rem;
  }

  @keyframes pulse {
    0%, 100% {
      opacity: 1;
      transform: scale(1);
    }
    50% {
      opacity: 0.7;
      transform: scale(1.05);
    }
  }
</style>

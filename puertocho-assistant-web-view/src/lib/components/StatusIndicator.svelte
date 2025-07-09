<script lang="ts">
  export let status: 'listening' | 'processing' | 'idle' | 'error' = 'idle';

  const statusInfo = {
    idle: { text: 'Esperando', color: 'gray' },
    listening: { text: 'Escuchando...', color: 'blue' },
    processing: { text: 'Procesando...', color: 'orange' },
    error: { text: 'Error', color: 'red' },
  };

  $: currentStatus = statusInfo[status] || statusInfo.idle;
</script>

<div class="status-indicator">
  <span class="status-dot" style="background-color: {currentStatus.color};"></span>
  <span class="status-text">{currentStatus.text}</span>
</div>

<style>
  .status-indicator {
    display: flex;
    align-items: center;
    padding: 0.5rem 1rem;
    border-radius: 9999px;
    background-color: #f0f0f0;
    border: 1px solid #e0e0e0;
    font-family: sans-serif;
  }

  .status-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 0.5rem;
    animation: pulse 2s infinite;
  }

  .status-text {
    font-weight: 500;
    color: #333;
  }

  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }
</style>

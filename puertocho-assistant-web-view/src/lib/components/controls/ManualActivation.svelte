<script lang="ts">
  import { sendMessage } from '$lib/services/websocketService';
  import { isConnected } from '$lib/stores/assistantStore';

  function activateAssistant() {
    if ($isConnected) {
      console.log('Sending manual activation command...');
      sendMessage({ type: 'manual_activation' });
    } else {
      alert('No se puede activar el asistente. No hay conexión con el backend.');
    }
  }
</script>

<div class="manual-activation">
  <button on:click={activateAssistant} disabled={!$isConnected} title={$isConnected ? 'Activar asistente' : 'Desconectado'} aria-label="Activar asistente manualmente">
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
      <line x1="12" y1="19" x2="12" y2="22"></line>
    </svg>
  </button>
</div>

<style>
  .manual-activation {
    margin-top: 1.5rem;
  }

  button {
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 50%;
    width: 60px;
    height: 60px;
    display: flex;
    justify-content: center;
    align-items: center;
    cursor: pointer;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    transition: background-color 0.3s, transform 0.2s;
  }

  button:hover {
    background-color: #0056b3;
    transform: scale(1.05);
  }

  button:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
    transform: none;
  }

  svg {
    width: 28px;
    height: 28px;
  }
</style>

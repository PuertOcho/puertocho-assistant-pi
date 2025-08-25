<script lang="ts">
  import { onMount } from 'svelte';
  import { assistantStatus, isConnected } from '$lib/stores/assistantStore';
  import { audioProcessingState } from '$lib/stores/audioStore';
  import { navigationStore } from '$lib/stores/navigationStore';
  
  // Audio wave visualization (mock data for now)
  let audioWaveData = [0.2, 0.5, 0.8, 0.3, 0.6, 0.9, 0.4, 0.7, 0.2, 0.5];
  
  // Update audio wave data periodically (mock animation)
  onMount(() => {
    const interval = setInterval(() => {
      audioWaveData = audioWaveData.map(() => Math.random());
    }, 100);
    
    return () => clearInterval(interval);
  });
  
  
  function getStatusColor(status: string): string {
    switch (status) {
      case 'listening': return '#28a745';
      case 'processing': return '#ffc107';
      case 'idle': return '#6c757d';
      case 'error': return '#dc3545';
      default: return '#6c757d';
    }
  }
  
  function getAudioStatusColor(status: string): string {
    switch (status) {
      case 'receiving': return '#17a2b8';
      case 'processing': return '#ffc107';
      case 'completed': return '#28a745';
      case 'error': return '#dc3545';
      default: return '#6c757d';
    }
  }
</script>

<div class="top-status-bar">
  
  <!-- Section 1: Audio Wave Visualization -->
  <div class="status-section audio-wave-section">
    <div class="section-label">Audio</div>
    <div class="audio-wave">
      {#each audioWaveData as amplitude, i}
        <div 
          class="wave-bar" 
          style="height: {amplitude * 100}%"
          style:animation-delay="{i * 0.1}s"
        ></div>
      {/each}
    </div>
  </div>
  
  <!-- Section 2: Audio Controls -->
  <div class="status-section audio-controls-section">
    <div class="section-label">Procesamiento</div>
    <div class="audio-status">
      <div 
        class="status-dot" 
        style="background-color: {getAudioStatusColor($audioProcessingState.status)}"
      ></div>
      <span class="status-text">
        {$audioProcessingState.status === 'idle' ? 'Esperando' : 
         $audioProcessingState.status === 'receiving' ? 'Recibiendo' :
         $audioProcessingState.status === 'processing' ? 'Procesando' :
         $audioProcessingState.status === 'completed' ? 'Completado' : 'Error'}
      </span>
      {#if $audioProcessingState.queue_length > 0}
        <span class="queue-info">({$audioProcessingState.queue_length} en cola)</span>
      {/if}
    </div>
  </div>
  
  <!-- Section 3: Assistant Status -->
  <div class="status-section assistant-status-section">
    <div class="section-label">Asistente</div>
    <div class="assistant-status">
      <div 
        class="status-dot pulse" 
        class:pulse-active={$assistantStatus === 'listening'}
        style="background-color: {getStatusColor($assistantStatus)}"
      ></div>
      <span class="status-text">
        {$assistantStatus === 'listening' ? 'Escuchando' : 
         $assistantStatus === 'processing' ? 'Procesando' :
         $assistantStatus === 'idle' ? 'Inactivo' : 'Error'}
      </span>
    </div>
  </div>
  
  <!-- Section 4: Server Connection Status -->
  <div class="status-section connection-status-section">
    <div class="section-label">Servidor</div>
    <div class="connection-status">
      <div 
        class="status-dot" 
        class:connected={$isConnected}
        class:disconnected={!$isConnected}
      ></div>
      <span class="status-text">
        {$isConnected ? 'Conectado' : 'Desconectado'}
      </span>
    </div>
  </div>
</div>

<style>
  .top-status-bar {
    height: 100%;
    display: flex;
    align-items: center;
    padding: 0 1rem;
    background: linear-gradient(90deg, #ffffff 0%, #f8f9fa 100%);
    border-bottom: 1px solid #dee2e6;
    position: relative;
  }
  
  
  /* Status Sections */
  .status-section {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 0.5rem;
    border-right: 1px solid #e9ecef;
    min-width: 120px;
  }
  
  .status-section:last-child {
    border-right: none;
  }
  
  .section-label {
    font-size: 0.7rem;
    color: #6c757d;
    font-weight: 600;
    margin-bottom: 0.25rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  /* Audio Wave */
  .audio-wave {
    display: flex;
    align-items: flex-end;
    gap: 2px;
    height: 24px;
    width: 60px;
  }
  
  .wave-bar {
    width: 3px;
    background: linear-gradient(to top, #3498db, #2980b9);
    border-radius: 1.5px;
    transition: height 0.1s ease;
    animation: wave-pulse 1s ease-in-out infinite;
  }
  
  @keyframes wave-pulse {
    0%, 100% { opacity: 0.6; }
    50% { opacity: 1; }
  }
  
  /* Status Elements */
  .audio-status,
  .assistant-status,
  .connection-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }
  
  .status-dot.pulse-active {
    animation: pulse 1.5s ease-in-out infinite;
  }
  
  .status-dot.connected {
    background-color: #28a745;
    box-shadow: 0 0 10px rgba(40, 167, 69, 0.3);
  }
  
  .status-dot.disconnected {
    background-color: #dc3545;
  }
  
  @keyframes pulse {
    0%, 100% { 
      transform: scale(1); 
      opacity: 1; 
    }
    50% { 
      transform: scale(1.2); 
      opacity: 0.8; 
    }
  }
  
  .status-text {
    font-size: 0.8rem;
    color: #495057;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .queue-info {
    font-size: 0.7rem;
    color: #6c757d;
    font-weight: 400;
  }
</style>

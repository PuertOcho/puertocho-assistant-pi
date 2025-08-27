<script lang="ts">
  import { onMount } from 'svelte';
  import { assistantStatus, isConnected } from '$lib/stores/assistantStore';
  import { audioProcessingState } from '$lib/stores/audioStore';
  import { navigationStore } from '$lib/stores/navigationStore';
  
  // Audio wave visualization (mock data for now)
  let audioWaveData = [0.2, 0.5, 0.8, 0.3, 0.6, 0.9, 0.4, 0.7, 0.2, 0.5];
  
  // Recording state
  let isRecording = false;
  let recordingStartTime: number | null = null;
  
  // Update audio wave data periodically (mock animation)
  onMount(() => {
    const interval = setInterval(() => {
      if (isRecording || $assistantStatus === 'listening') {
        // More dynamic animation when recording/listening
        audioWaveData = audioWaveData.map(() => Math.random() * 0.8 + 0.2);
      } else {
        // Subtle animation when idle
        audioWaveData = audioWaveData.map(() => Math.random() * 0.3 + 0.1);
      }
    }, 100);
    
    return () => clearInterval(interval);
  });

  // Sync recording state with assistant status
  $: {
    if ($assistantStatus === 'listening' && !isRecording) {
      isRecording = true;
      recordingStartTime = Date.now();
    } else if ($assistantStatus !== 'listening' && isRecording) {
      isRecording = false;
      recordingStartTime = null;
    }
  }
  
  
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

  async function handleRecordingToggle() {
    try {
      if (!isRecording) {
        // Iniciar grabación
        await startRecording();
      } else {
        // Detener grabación
        await stopRecording();
      }
    } catch (error) {
      console.error('Error toggle recording:', error);
    }
  }

  async function startRecording() {
    try {
      // Simular pulsación de botón en el hardware para iniciar grabación
      const response = await fetch('http://localhost:8080/button/simulate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event_type: 'short',
          duration: 0.5
        })
      });

      if (response.ok) {
        isRecording = true;
        recordingStartTime = Date.now();
        console.log('Recording started via hardware simulation');
      } else {
        throw new Error('Failed to start recording');
      }
    } catch (error) {
      console.error('Error starting recording:', error);
      // Fallback: enviar comando directo por WebSocket si la API HTTP falla
      try {
        // Importar sendMessage del websocket service
        const { sendMessage } = await import('$lib/services/websocketService');
        sendMessage({
          type: 'hardware_command',
          command: 'start_recording'
        });
        isRecording = true;
        recordingStartTime = Date.now();
      } catch (wsError) {
        console.error('WebSocket fallback failed:', wsError);
      }
    }
  }

  async function stopRecording() {
    try {
      // Simular pulsación larga de botón para detener grabación
      const response = await fetch('http://localhost:8080/button/simulate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event_type: 'long',
          duration: 2.0
        })
      });

      if (response.ok) {
        isRecording = false;
        recordingStartTime = null;
        console.log('Recording stopped via hardware simulation');
      } else {
        throw new Error('Failed to stop recording');
      }
    } catch (error) {
      console.error('Error stopping recording:', error);
      // Fallback: enviar comando directo por WebSocket
      try {
        const { sendMessage } = await import('$lib/services/websocketService');
        sendMessage({
          type: 'hardware_command',
          command: 'stop_recording'
        });
        isRecording = false;
        recordingStartTime = null;
      } catch (wsError) {
        console.error('WebSocket fallback failed:', wsError);
      }
    }
  }

  function getRecordingDuration(): string {
    if (!isRecording || !recordingStartTime) return '';
    const elapsed = Math.floor((Date.now() - recordingStartTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  }
</script>

<div class="top-status-bar">
  
  <!-- Section 1: Audio Wave Visualization (25%) -->
  <div class="status-section audio-wave-section">
    <div class="section-label">Audio</div>
    <div class="audio-wave" class:recording={isRecording}>
      {#each audioWaveData as amplitude, i}
        <div 
          class="wave-bar" 
          class:recording={isRecording}
          style="height: {amplitude * 100}%"
          style:animation-delay="{i * 0.1}s"
        ></div>
      {/each}
    </div>
  </div>
  
  <!-- Section 2: Recording Button (25%) -->
  <div class="status-section recording-button-section">
    <div class="section-label">Grabación</div>
    <div class="recording-controls">
      <button 
        class="record-button" 
        class:recording={isRecording}
        on:click={handleRecordingToggle}
        disabled={!$isConnected}
        title={isRecording ? 'Detener grabación' : 'Iniciar grabación'}
      >
        <div class="record-icon">
          {#if isRecording}
            <div class="stop-icon"></div>
          {:else}
            <div class="record-dot"></div>
          {/if}
        </div>
      </button>
      {#if isRecording}
        <div class="recording-duration">{getRecordingDuration()}</div>
      {:else}
        <div class="recording-duration">&nbsp;</div>
      {/if}
      <div class="recording-status">
        {isRecording ? 'Grabando' : $isConnected ? 'Listo' : 'Desconectado'}
      </div>
    </div>
  </div>
  
  <!-- Section 3: Combined Audio Processing + Assistant Status (25%) -->
  <div class="status-section combined-status-section">
    <div class="section-label">Estado</div>
    <div class="combined-status">
      <!-- Audio Processing Status -->
      <div class="audio-status">
        <div 
          class="status-dot small" 
          style="background-color: {getAudioStatusColor($audioProcessingState.status)}"
        ></div>
        <span class="status-text small">
          {$audioProcessingState.status === 'idle' ? 'Esperando' : 
           $audioProcessingState.status === 'receiving' ? 'Recibiendo' :
           $audioProcessingState.status === 'processing' ? 'Procesando' :
           $audioProcessingState.status === 'completed' ? 'Completado' : 'Error'}
        </span>
        {#if $audioProcessingState.queue_length > 0}
          <span class="queue-info">({$audioProcessingState.queue_length})</span>
        {/if}
      </div>
      
      <!-- Assistant Status -->
      <div class="assistant-status">
        <div 
          class="status-dot small pulse" 
          class:pulse-active={$assistantStatus === 'listening'}
          style="background-color: {getStatusColor($assistantStatus)}"
        ></div>
        <span class="status-text small">
          {$assistantStatus === 'listening' ? 'Escuchando' : 
           $assistantStatus === 'processing' ? 'Procesando' :
           $assistantStatus === 'idle' ? 'Inactivo' : 'Error'}
        </span>
      </div>
    </div>
  </div>
  
  <!-- Section 4: Server Connection Status (25%) -->
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
  
  .wave-bar.recording {
    background: linear-gradient(to top, #e74c3c, #c0392b);
    animation: recording-wave-pulse 0.5s ease-in-out infinite;
  }
  
  @keyframes wave-pulse {
    0%, 100% { opacity: 0.6; }
    50% { opacity: 1; }
  }
  
  @keyframes recording-wave-pulse {
    0%, 100% { opacity: 0.8; }
    50% { opacity: 1; }
  }
  
  /* Recording Button Section */
  .recording-controls {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 0.25rem;
  }

  .record-button {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: 2px solid #dc3545;
    background: #fff;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
  }
  
  .record-button:hover:not(:disabled) {
    transform: scale(1.1);
    box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);
  }
  
  .record-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    border-color: #6c757d;
  }
  
  .record-button.recording {
    background: #dc3545;
    animation: recording-pulse 1.5s ease-in-out infinite;
  }
  
  @keyframes recording-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }
  
  .record-icon {
    width: 16px;
    height: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .record-dot {
    width: 12px;
    height: 12px;
    background: #dc3545;
    border-radius: 50%;
  }
  
  .stop-icon {
    width: 8px;
    height: 8px;
    background: #fff;
    border-radius: 2px;
  }
  
  .recording-duration {
    font-size: 0.7rem;
    color: #dc3545;
    font-weight: 600;
    min-height: 1rem;
  }
  
  .recording-status {
    font-size: 0.65rem;
    color: #6c757d;
    font-weight: 500;
  }
  
  /* Combined Status Section */
  .combined-status {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    width: 100%;
  }
  
  .audio-status,
  .assistant-status {
    display: flex;
    align-items: center;
    gap: 0.3rem;
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
  
  .status-dot.small {
    width: 6px;
    height: 6px;
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
  
  .status-text.small {
    font-size: 0.7rem;
  }
  
  .queue-info {
    font-size: 0.65rem;
    color: #6c757d;
    font-weight: 400;
  }
</style>

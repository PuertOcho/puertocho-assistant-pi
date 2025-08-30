<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { assistantStatus, commandHistory } from '$lib/stores/assistantStore';
  import { chatStore, addUserMessage, addAssistantMessage } from '$lib/stores/chatStore';
  import { 
    buttonActions, 
    matrixConfig, 
    isLoading, 
    startConfigPolling, 
    stopConfigPolling
  } from '$lib/stores/buttonConfigStore';
  import { AudioControls } from '../audio';
  import ChatInterface from '../chat/ChatInterface.svelte';
  import ButtonIcon from '../ui/ButtonIcon.svelte';
  
  // Start configuration polling when component mounts
  onMount(() => {
    startConfigPolling();
  });
  
  // Clean up when component is destroyed
  onDestroy(() => {
    stopConfigPolling();
  });
  
  function handleButtonClick(action: string, label: string) {
    console.log(`Button clicked: ${label} (${action})`);
    // Here you would trigger the appropriate action
    // For now, just add to command history for demonstration
    commandHistory.update(history => [
      ...history,
      {
        timestamp: new Date().toLocaleTimeString(),
        command: `Manual: ${label}`
      }
    ]);
  }
  
  // Test function to simulate adding messages to chat
  function testAddMessage() {
    // Simulate user message with audio
    addUserMessage(
      "http://localhost:8000/api/v1/audio/verification/files/verification_20250828_094102_338_captured_voice_20250827_193516_595.wav",
      "test.wav",
      "Hola asistente, ¿puedes ayudarme?"
    );
    
    // Simulate assistant response after a delay
    setTimeout(() => {
      addAssistantMessage(
        "¡Hola! Por supuesto que puedo ayudarte. ¿En qué necesitas asistencia?"
      );
    }, 1000);
  }
  
  // Calculate how many buttons to show based on matrix configuration
  $: visibleButtons = $buttonActions.slice(0, $matrixConfig.rows * $matrixConfig.cols);
</script>

<div class="home-view">
  <div class="home-content">
    <!-- Left Side: Button Matrix (50% width) -->
    <div class="left-section">
      <!-- Configuration controls (only visible in development) -->
      {#if $isLoading}
        <div class="loading-indicator">
          <p>Cargando configuración...</p>
        </div>
      {/if}
      
      <div 
        class="button-matrix"
        style="grid-template-columns: repeat({$matrixConfig.cols}, 1fr); grid-template-rows: repeat({$matrixConfig.rows}, 1fr);"
      >
        {#each visibleButtons as button}
          <button 
            class="action-button"
            on:click={() => handleButtonClick(button.action, button.label)}
            title={button.label}
          >
            <div class="button-icon">
              <ButtonIcon 
                icon={button.icon} 
                iconType={button.iconType} 
                alt={button.label}
              />
            </div>
            <div class="button-label">{button.label}</div>
          </button>
        {/each}
        
        <!-- Fill remaining slots with placeholder buttons -->
        {#each Array($matrixConfig.rows * $matrixConfig.cols - visibleButtons.length) as _, i}
          <button class="action-button placeholder" disabled>
            <div class="button-icon">
              <ButtonIcon icon="mas_icon.png" iconType="image" alt="Libre" />
            </div>
            <div class="button-label">Libre</div>
          </button>
        {/each}
      </div>
    </div>
    
    <!-- Right Side: Chat/Audio Interface (50% width) -->
    <div class="right-section">
      <!-- Debug info (solo en desarrollo) -->
      {#if import.meta.env.DEV}
        <div class="debug-info">
          <small>
            Mensajes: {$chatStore.messages?.length || 0} | 
            Estado: {$assistantStatus} | 
            Cargando: {$chatStore.isLoading ? 'Sí' : 'No'}
          </small>
        </div>
      {/if}
      
      <!-- Chat Interface -->
      <div class="chat-section">
        <!-- Verificar si hay mensajes y mostrar estado alternativo -->
        {#if $chatStore.messages && $chatStore.messages.length > 0}
          <ChatInterface maxHeight="100%" />
        {:else}
          <div class="no-messages-state">
            <p>Puedes empezar una conversación enviando un comando de voz.</p>
            <div class="status-indicators">
              <div class="status-item">
                <span class="status-label">Estado:</span>
                <span class="status-value {$assistantStatus}">{$assistantStatus}</span>
              </div>
              {#if $chatStore.isLoading}
                <div class="status-item">
                  <span class="status-label">Procesando audio...</span>
                  <div class="loading-spinner"></div>
                </div>
              {/if}
            </div>
            <div class="quick-actions">
              <button class="quick-action-btn" on:click={() => handleButtonClick('help', 'Ayuda')}>
                ❓ Obtener ayuda
              </button>
              <button class="quick-action-btn" on:click={() => handleButtonClick('status', 'Estado del sistema')}>
                📊 Ver estado del sistema
              </button>
              <!-- Test button (solo en desarrollo) -->
              {#if import.meta.env.DEV}
                <button class="quick-action-btn test-btn" on:click={testAddMessage}>
                  🧪 Probar mensaje de chat
                </button>
              {/if}
            </div>
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>

<style>
  .home-view {
    height: 100%;
    padding: 0rem;
    background-color: #f8f9fa;
    box-sizing: border-box;
  }
  
  .home-content {
    height: 100%;
    display: grid;
    grid-template-columns: 50% 50%;
    max-width: 1400px;
    margin: 0 auto;
    box-sizing: border-box;
  }
  
  .left-section,
  .right-section {
    display: flex;
    flex-direction: column;
    background-color: #ffffff;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    width: 100%;
    box-sizing: border-box;
  }
  
  /* Button Matrix */
  .button-matrix {
    flex: 1;
    display: grid;
    gap: 0.75rem;
    padding: 1.5rem;
    overflow-y: auto;
  }
  
  .action-button {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
    padding: 0.8rem 0.4rem;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border: 2px solid #dee2e6;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s ease;
    min-height: 80px;
    font-size: 0.85rem;
    color: #495057;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .action-button:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    border-color: #007bff;
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  }
  
  .action-button:active:not(:disabled) {
    transform: translateY(0);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  
  .action-button.placeholder {
    opacity: 0.5;
    cursor: not-allowed;
    background: #f8f9fa;
  }
  
  .button-icon {
    font-size: 1.6rem;
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  
  .button-label {
    font-weight: 500;
    text-align: center;
    line-height: 1.1;
    word-break: keep-all;
    overflow-wrap: anywhere;
    hyphens: none;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-size: 0.75rem;
    max-width: 100%;
    padding: 0 0.3rem;
    overflow: visible;
  }
  
  /* Loading indicator */
  .loading-indicator {
    position: absolute;
    top: 10px;
    right: 10px;
    background: rgba(0, 123, 255, 0.9);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.8rem;
    z-index: 100;
  }
  
  .left-section {
    position: relative;
  }
  
  /* Right Section */
  .chat-section {
    flex: 1;
    overflow-y: auto;
  }
  
  /* Debug info */
  .debug-info {
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    padding: 0.5rem;
    font-size: 0.75rem;
    color: #856404;
    text-align: center;
  }
  
  /* No messages state */
  .no-messages-state {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    text-align: center;
    color: #6c757d;
  }
  
  .empty-chat-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.5;
  }
  
  .no-messages-state h3 {
    margin: 0 0 1rem 0;
    color: #495057;
    font-weight: 600;
  }
  
  .no-messages-state p {
    margin: 0 0 2rem 0;
    line-height: 1.5;
    max-width: 300px;
  }
  
  .status-indicators {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 2rem;
    padding: 1rem;
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #dee2e6;
  }
  
  .status-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.85rem;
  }
  
  .status-label {
    font-weight: 600;
    color: #495057;
  }
  
  .status-value {
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 500;
  }
  
  .status-value.idle {
    background: #d1ecf1;
    color: #0c5460;
  }
  
  .status-value.listening {
    background: #d4edda;
    color: #155724;
  }
  
  .status-value.processing {
    background: #fff3cd;
    color: #856404;
  }
  
  .status-value.error {
    background: #f8d7da;
    color: #721c24;
  }
  
  .loading-spinner {
    width: 16px;
    height: 16px;
    border: 2px solid #dee2e6;
    border-top: 2px solid #6c757d;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .quick-actions {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    width: 100%;
    max-width: 250px;
  }
  
  .quick-action-btn {
    padding: 0.75rem 1rem;
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.9rem;
    color: #495057;
  }
  
  .quick-action-btn:hover {
    background: #e9ecef;
    border-color: #adb5bd;
    transform: translateY(-1px);
  }
  
  .test-btn {
    background: #e3f2fd !important;
    border-color: #2196f3 !important;
    color: #1976d2 !important;
  }
  
  .test-btn:hover {
    background: #bbdefb !important;
    border-color: #1976d2 !important;
  }
  
  /* Touch-friendly for kiosk mode */
  @media (pointer: coarse) {
    .action-button {
      min-height: 90px;
      padding: 1rem 0.5rem;
      font-size: 0.9rem;
    }
    
    .button-icon {
      font-size: 1.8rem;
      margin-bottom: 0.7rem;
    }
    
    .button-label {
      font-size: 0.8rem;
    }
  }
  
  /* Landscape kiosk optimization */
  @media (orientation: landscape) and (max-height: 600px) {
    .action-button {
      min-height: 70px;
      padding: 0.6rem 0.3rem;
    }
    
    .button-icon {
      font-size: 1.4rem;
      margin-bottom: 0.4rem;
    }
    
    .button-label {
      font-size: 0.7rem;
      line-height: 1;
    }
  }
</style>

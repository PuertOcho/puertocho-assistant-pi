<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { assistantStatus, commandHistory } from '$lib/stores/assistantStore';
  import { 
    buttonActions, 
    matrixConfig, 
    isLoading, 
    startConfigPolling, 
    stopConfigPolling
  } from '$lib/stores/buttonConfigStore';
  import { AudioControls } from '../audio';
  import { CommandHistory } from '../assistant';
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
      <div class="section-header">
        <h2>Interfaz de Voz</h2>
        <p>Audio y comunicación</p>
      </div>
      
      <!-- Audio Controls -->
      <div class="audio-section">
        <AudioControls />
      </div>
      
      <!-- Command History -->
      <div class="chat-section">
        <CommandHistory commands={$commandHistory} />
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
  
  .section-header {
    padding: 1.5rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    text-align: center;
  }
  
  .section-header h2 {
    margin: 0 0 0.5rem 0;
    font-size: 1.5rem;
    font-weight: 600;
  }
  
  .section-header p {
    margin: 0;
    font-size: 0.9rem;
    opacity: 0.9;
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
  .audio-section {
    padding: 1.5rem;
    border-bottom: 1px solid #dee2e6;
  }
  
  .chat-section {
    flex: 1;
    padding: 1.5rem;
    overflow-y: auto;
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
    
    .section-header {
      padding: 1rem 1.5rem;
    }
    
    .section-header h2 {
      font-size: 1.2rem;
    }
  }
</style>

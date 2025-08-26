<script lang="ts">
  import { writable } from 'svelte/store';
  import { assistantStatus, commandHistory } from '$lib/stores/assistantStore';
  import { AudioControls } from '../audio';
  import { CommandHistory } from '../assistant';
  
  // Configuration for button matrix
  const matrixConfig = writable({ rows: 5, cols: 4 });
  
  // Sample button actions - these can be configured later
  const buttonActions = [
    { id: 1, label: 'Luces Salón', icon: '💡', action: 'lights_living_room' },
    { id: 2, label: 'Música', icon: '🎵', action: 'play_music' },
    { id: 3, label: 'Temperatura', icon: '🌡️', action: 'check_temperature' },
    { id: 4, label: 'Seguridad', icon: '🔒', action: 'security_status' },
    { id: 5, label: 'Persianas', icon: '🪟', action: 'blinds_control' },
    { id: 6, label: 'Cocina', icon: '🍳', action: 'kitchen_appliances' },
    { id: 7, label: 'Dormitorio', icon: '🛏️', action: 'bedroom_control' },
    { id: 8, label: 'Aspiradora', icon: '🧹', action: 'vacuum_start' },
    { id: 9, label: 'Información', icon: 'ℹ️', action: 'get_info' },
    { id: 10, label: 'Emergencia', icon: '🚨', action: 'emergency' },
    { id: 11, label: 'Riego', icon: '🌱', action: 'irrigation_system' },
    { id: 12, label: 'Garaje', icon: '🚗', action: 'garage_door' },
    { id: 13, label: 'Intercomunicador', icon: '📞', action: 'intercom' },
    { id: 14, label: 'Cámaras', icon: '📹', action: 'security_cameras' },
    { id: 15, label: 'Clima', icon: '❄️', action: 'climate_control' },
    { id: 16, label: 'Favoritos', icon: '⭐', action: 'favorites' },
  ];
  
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
  $: visibleButtons = buttonActions.slice(0, $matrixConfig.rows * $matrixConfig.cols);
</script>

<div class="home-view">
  <div class="home-content">
    <!-- Left Side: Button Matrix (50% width) -->
    <div class="left-section">
      <div class="section-header">
        <h2>Control Manual</h2>
        <p>Acciones rápidas del hogar</p>
      </div>
      
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
            <div class="button-icon">{button.icon}</div>
            <div class="button-label">{button.label}</div>
          </button>
        {/each}
        
        <!-- Fill remaining slots with placeholder buttons -->
        {#each Array($matrixConfig.rows * $matrixConfig.cols - visibleButtons.length) as _, i}
          <button class="action-button placeholder" disabled>
            <div class="button-icon">➕</div>
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
    padding: 1rem;
    background-color: #f8f9fa;
    box-sizing: border-box;
  }
  
  .home-content {
    height: 100%;
    display: grid;
    grid-template-columns: 50% 50%;
    gap: 2rem;
    max-width: 1400px;
    margin: 0 auto;
    box-sizing: border-box;
  }
  
  .left-section,
  .right-section {
    display: flex;
    flex-direction: column;
    background-color: #ffffff;
    border-radius: 12px;
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
    justify-content: center;
    padding: 1rem;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border: 2px solid #dee2e6;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s ease;
    min-height: 80px;
    font-size: 0.85rem;
    color: #495057;
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
    font-size: 1.8rem;
    margin-bottom: 0.5rem;
  }
  
  .button-label {
    font-weight: 500;
    text-align: center;
    line-height: 1.2;
    word-break: break-word;
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
  
  /* Responsive Design */
  @media (max-width: 1024px) {
    .home-content {
      grid-template-columns: 50% 50%;
      gap: 1rem;
    }
    
    .section-header h2 {
      font-size: 1.3rem;
    }
    
    .button-matrix {
      padding: 1rem;
      gap: 0.5rem;
    }
    
    .action-button {
      min-height: 70px;
      padding: 0.75rem;
      font-size: 0.8rem;
    }
    
    .button-icon {
      font-size: 1.5rem;
    }
  }
  
  /* Mobile */
  @media (max-width: 768px) {
    .home-view {
      padding: 0.5rem;
    }
    
    .home-content {
      grid-template-columns: 1fr;
      gap: 0.5rem;
    }
    
    .button-matrix {
      padding: 0.75rem;
      gap: 0.5rem;
    }
    
    .action-button {
      min-height: 60px;
      padding: 0.5rem;
      font-size: 0.75rem;
    }
    
    .button-icon {
      font-size: 1.3rem;
      margin-bottom: 0.25rem;
    }
    
    .audio-section,
    .chat-section {
      padding: 1rem;
    }
  }
  
  /* Touch-friendly for kiosk mode */
  @media (pointer: coarse) {
    .action-button {
      min-height: 90px;
      padding: 1.25rem;
      font-size: 0.9rem;
    }
    
    .button-icon {
      font-size: 2rem;
    }
  }
  
  /* Landscape kiosk optimization */
  @media (orientation: landscape) and (max-height: 600px) {
    .action-button {
      min-height: 70px;
      padding: 0.75rem;
    }
    
    .button-icon {
      font-size: 1.6rem;
      margin-bottom: 0.25rem;
    }
    
    .section-header {
      padding: 1rem 1.5rem;
    }
    
    .section-header h2 {
      font-size: 1.2rem;
    }
  }
</style>

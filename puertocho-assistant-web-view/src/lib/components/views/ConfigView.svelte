<script lang="ts">
  import { writable } from 'svelte/store';
  
  // Configuration stores
  const voiceConfig = writable({
    language: 'es-ES',
    voice: 'female',
    speed: 1.0,
    pitch: 1.0,
    volume: 0.8
  });
  
  const systemConfig = writable({
    wakeWord: 'PuertoCho',
    sensitivity: 0.7,
    noiseSuppress: true,
    echoCancel: true,
    autoMode: true
  });
  
  const uiConfig = writable({
    theme: 'light',
    buttonSize: 'medium',
    showAnimations: true,
    kioskMode: false,
    screenTimeout: 300
  });
  
  let activeTab = 'voice';
  
  // Available options
  const languages = [
    { value: 'es-ES', label: 'Español (España)' },
    { value: 'es-MX', label: 'Español (México)' },
    { value: 'en-US', label: 'English (US)' },
    { value: 'en-GB', label: 'English (UK)' }
  ];
  
  const voices = [
    { value: 'female', label: 'Voz Femenina' },
    { value: 'male', label: 'Voz Masculina' }
  ];
  
  const themes = [
    { value: 'light', label: 'Claro' },
    { value: 'dark', label: 'Oscuro' },
    { value: 'auto', label: 'Automático' }
  ];
  
  const buttonSizes = [
    { value: 'small', label: 'Pequeño' },
    { value: 'medium', label: 'Mediano' },
    { value: 'large', label: 'Grande' }
  ];
  
  function handleSaveConfig() {
    console.log('Saving configuration...', {
      voice: $voiceConfig,
      system: $systemConfig,
      ui: $uiConfig
    });
    // Here you would save to backend/localStorage
    alert('Configuración guardada correctamente');
  }
  
  function handleResetConfig() {
    if (confirm('¿Estás seguro de que quieres restablecer toda la configuración?')) {
      // Reset to defaults
      voiceConfig.set({
        language: 'es-ES',
        voice: 'female',
        speed: 1.0,
        pitch: 1.0,
        volume: 0.8
      });
      
      systemConfig.set({
        wakeWord: 'PuertoCho',
        sensitivity: 0.7,
        noiseSuppress: true,
        echoCancel: true,
        autoMode: true
      });
      
      uiConfig.set({
        theme: 'light',
        buttonSize: 'medium',
        showAnimations: true,
        kioskMode: false,
        screenTimeout: 300
      });
      
      alert('Configuración restablecida a valores por defecto');
    }
  }
</script>

<div class="config-view">
  <div class="config-header">
    <h1>Configuración del Asistente</h1>
    <p>Personaliza PuertoCho según tus preferencias</p>
  </div>
  
  <div class="config-content">
    <!-- Tab Navigation -->
    <div class="tab-navigation">
      <button 
        class="tab-button"
        class:active={activeTab === 'voice'}
        on:click={() => activeTab = 'voice'}
      >
        🎤 Voz
      </button>
      <button 
        class="tab-button"
        class:active={activeTab === 'system'}
        on:click={() => activeTab = 'system'}
      >
        ⚙️ Sistema
      </button>
      <button 
        class="tab-button"
        class:active={activeTab === 'ui'}
        on:click={() => activeTab = 'ui'}
      >
        🎨 Interfaz
      </button>
    </div>
    
    <!-- Tab Content -->
    <div class="tab-content">
      {#if activeTab === 'voice'}
        <!-- Voice Configuration -->
        <div class="config-section">
          <h3>Configuración de Voz</h3>
          
          <div class="config-group">
            <label for="language">Idioma:</label>
            <select id="language" bind:value={$voiceConfig.language}>
              {#each languages as lang}
                <option value={lang.value}>{lang.label}</option>
              {/each}
            </select>
          </div>
          
          <div class="config-group">
            <label for="voice">Tipo de voz:</label>
            <select id="voice" bind:value={$voiceConfig.voice}>
              {#each voices as voice}
                <option value={voice.value}>{voice.label}</option>
              {/each}
            </select>
          </div>
          
          <div class="config-group">
            <label for="speed">Velocidad: {$voiceConfig.speed}x</label>
            <input 
              id="speed" 
              type="range" 
              min="0.5" 
              max="2.0" 
              step="0.1" 
              bind:value={$voiceConfig.speed}
            >
          </div>
          
          <div class="config-group">
            <label for="pitch">Tono: {$voiceConfig.pitch}</label>
            <input 
              id="pitch" 
              type="range" 
              min="0.5" 
              max="2.0" 
              step="0.1" 
              bind:value={$voiceConfig.pitch}
            >
          </div>
          
          <div class="config-group">
            <label for="volume">Volumen: {Math.round($voiceConfig.volume * 100)}%</label>
            <input 
              id="volume" 
              type="range" 
              min="0" 
              max="1" 
              step="0.1" 
              bind:value={$voiceConfig.volume}
            >
          </div>
        </div>
        
      {:else if activeTab === 'system'}
        <!-- System Configuration -->
        <div class="config-section">
          <h3>Configuración del Sistema</h3>
          
          <div class="config-group">
            <label for="wakeWord">Palabra de activación:</label>
            <input id="wakeWord" type="text" bind:value={$systemConfig.wakeWord}>
          </div>
          
          <div class="config-group">
            <label for="sensitivity">Sensibilidad: {Math.round($systemConfig.sensitivity * 100)}%</label>
            <input 
              id="sensitivity" 
              type="range" 
              min="0" 
              max="1" 
              step="0.1" 
              bind:value={$systemConfig.sensitivity}
            >
          </div>
          
          <div class="config-group">
            <label class="checkbox-label">
              <input type="checkbox" bind:checked={$systemConfig.noiseSuppress}>
              Supresión de ruido
            </label>
          </div>
          
          <div class="config-group">
            <label class="checkbox-label">
              <input type="checkbox" bind:checked={$systemConfig.echoCancel}>
              Cancelación de eco
            </label>
          </div>
          
          <div class="config-group">
            <label class="checkbox-label">
              <input type="checkbox" bind:checked={$systemConfig.autoMode}>
              Modo automático
            </label>
          </div>
        </div>
        
      {:else if activeTab === 'ui'}
        <!-- UI Configuration -->
        <div class="config-section">
          <h3>Configuración de Interfaz</h3>
          
          <div class="config-group">
            <label for="theme">Tema:</label>
            <select id="theme" bind:value={$uiConfig.theme}>
              {#each themes as theme}
                <option value={theme.value}>{theme.label}</option>
              {/each}
            </select>
          </div>
          
          <div class="config-group">
            <label for="buttonSize">Tamaño de botones:</label>
            <select id="buttonSize" bind:value={$uiConfig.buttonSize}>
              {#each buttonSizes as size}
                <option value={size.value}>{size.label}</option>
              {/each}
            </select>
          </div>
          
          <div class="config-group">
            <label class="checkbox-label">
              <input type="checkbox" bind:checked={$uiConfig.showAnimations}>
              Mostrar animaciones
            </label>
          </div>
          
          <div class="config-group">
            <label class="checkbox-label">
              <input type="checkbox" bind:checked={$uiConfig.kioskMode}>
              Modo kiosko
            </label>
          </div>
          
          <div class="config-group">
            <label for="screenTimeout">Tiempo de espera de pantalla (segundos):</label>
            <input 
              id="screenTimeout" 
              type="number" 
              min="60" 
              max="3600" 
              bind:value={$uiConfig.screenTimeout}
            >
          </div>
        </div>
      {/if}
    </div>
    
    <!-- Action Buttons -->
    <div class="config-actions">
      <button class="btn btn-primary" on:click={handleSaveConfig}>
        💾 Guardar Cambios
      </button>
      <button class="btn btn-secondary" on:click={handleResetConfig}>
        🔄 Restablecer
      </button>
    </div>
  </div>
</div>

<style>
  .config-view {
    height: 100%;
    display: flex;
    flex-direction: column;
    background-color: #f8f9fa;
  }
  
  .config-header {
    padding: 2rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    text-align: center;
  }
  
  .config-header h1 {
    margin: 0 0 0.5rem 0;
    font-size: 2rem;
    font-weight: 600;
  }
  
  .config-header p {
    margin: 0;
    opacity: 0.9;
  }
  
  .config-content {
    flex: 1;
    padding: 2rem;
    max-width: 800px;
    margin: 0 auto;
    width: 100%;
  }
  
  /* Tab Navigation */
  .tab-navigation {
    display: flex;
    background-color: #ffffff;
    border-radius: 12px 12px 0 0;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    margin-bottom: 0;
  }
  
  .tab-button {
    flex: 1;
    padding: 1rem 2rem;
    background: none;
    border: none;
    color: #6c757d;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.2s ease;
    border-bottom: 3px solid transparent;
  }
  
  .tab-button:hover {
    background-color: #f8f9fa;
    color: #495057;
  }
  
  .tab-button.active {
    color: #007bff;
    background-color: #ffffff;
    border-bottom-color: #007bff;
  }
  
  /* Tab Content */
  .tab-content {
    background-color: #ffffff;
    border-radius: 0 0 12px 12px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    padding: 2rem;
    margin-bottom: 2rem;
  }
  
  .config-section h3 {
    color: #343a40;
    font-size: 1.5rem;
    margin: 0 0 2rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #e9ecef;
  }
  
  /* Form Groups */
  .config-group {
    margin-bottom: 2rem;
  }
  
  .config-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 600;
    color: #495057;
  }
  
  .config-group select,
  .config-group input[type="text"],
  .config-group input[type="number"] {
    width: 100%;
    padding: 0.75rem;
    border: 2px solid #dee2e6;
    border-radius: 8px;
    font-size: 1rem;
    transition: border-color 0.2s ease;
  }
  
  .config-group select:focus,
  .config-group input[type="text"]:focus,
  .config-group input[type="number"]:focus {
    outline: none;
    border-color: #007bff;
  }
  
  .config-group input[type="range"] {
    width: 100%;
    height: 8px;
    border-radius: 5px;
    background: #dee2e6;
    outline: none;
    -webkit-appearance: none;
  }
  
  .config-group input[type="range"]::-webkit-slider-thumb {
    appearance: none;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #007bff;
    cursor: pointer;
  }
  
  .config-group input[type="range"]::-moz-range-thumb {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #007bff;
    cursor: pointer;
    border: none;
  }
  
  /* Checkbox Labels */
  .checkbox-label {
    display: flex !important;
    align-items: center;
    gap: 0.75rem;
    cursor: pointer;
    margin-bottom: 0 !important;
  }
  
  .checkbox-label input[type="checkbox"] {
    width: auto !important;
    padding: 0 !important;
    margin: 0 !important;
    transform: scale(1.3);
  }
  
  /* Action Buttons */
  .config-actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
  }
  
  .btn {
    padding: 0.875rem 2rem;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .btn-primary {
    background: linear-gradient(135deg, #007bff, #0056b3);
    color: white;
  }
  
  .btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
  }
  
  .btn-secondary {
    background: linear-gradient(135deg, #6c757d, #545b62);
    color: white;
  }
  
  .btn-secondary:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(108, 117, 125, 0.3);
  }
  
  /* Responsive Design */
  @media (max-width: 768px) {
    .config-content {
      padding: 1rem;
    }
    
    .config-header {
      padding: 1.5rem 1rem;
    }
    
    .config-header h1 {
      font-size: 1.5rem;
    }
    
    .tab-content {
      padding: 1.5rem;
    }
    
    .tab-button {
      padding: 0.75rem 1rem;
      font-size: 0.9rem;
    }
    
    .config-actions {
      flex-direction: column;
    }
    
    .btn {
      width: 100%;
      justify-content: center;
    }
  }
  
  /* Touch-friendly for kiosk mode */
  @media (pointer: coarse) {
    .tab-button,
    .btn {
      padding: 1rem 2rem;
      min-height: 48px;
    }
    
    .config-group input[type="range"]::-webkit-slider-thumb {
      width: 24px;
      height: 24px;
    }
    
    .config-group input[type="range"]::-moz-range-thumb {
      width: 24px;
      height: 24px;
    }
    
    .checkbox-label input[type="checkbox"] {
      transform: scale(1.5);
    }
  }
</style>

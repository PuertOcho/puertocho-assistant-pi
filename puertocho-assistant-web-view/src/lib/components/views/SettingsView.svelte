<script lang="ts">
  import { writable } from 'svelte/store';
  import { onMount } from 'svelte';
  
  // System information stores
  const systemInfo = writable({
    hostname: 'puertocho-pi',
    os: 'Raspberry Pi OS',
    kernel: '6.1.0-rpi4-rpi-v8',
    uptime: '2d 14h 32m',
    load: '0.45, 0.52, 0.48',
    temperature: 45.2
  });
  
  const resources = writable({
    cpu: 23,
    memory: 67,
    storage: 45,
    network: {
      rx: '2.3 MB/s',
      tx: '1.8 MB/s'
    }
  });
  
  const services = writable([
    { name: 'puertocho-backend', status: 'running', port: 8000, uptime: '1d 12h', memory: '128 MB' },
    { name: 'puertocho-hardware', status: 'running', port: 8080, uptime: '1d 12h', memory: '64 MB' },
    { name: 'puertocho-webview', status: 'running', port: 3000, uptime: '1d 12h', memory: '45 MB' },
    { name: 'nginx', status: 'running', port: 80, uptime: '2d 14h', memory: '12 MB' },
    { name: 'docker', status: 'running', port: null, uptime: '2d 14h', memory: '89 MB' }
  ]);
  
  let selectedTab = 'overview';
  
  // Mock data update
  function updateSystemData() {
    resources.update(r => ({
      ...r,
      cpu: Math.max(10, Math.min(90, r.cpu + (Math.random() - 0.5) * 10)),
      memory: Math.max(30, Math.min(95, r.memory + (Math.random() - 0.5) * 5)),
      storage: Math.max(20, Math.min(80, r.storage + (Math.random() - 0.5) * 2))
    }));
    
    systemInfo.update(s => ({
      ...s,
      temperature: Math.max(35, Math.min(65, s.temperature + (Math.random() - 0.5) * 2))
    }));
  }
  
  function restartService(serviceName: string) {
    if (confirm(`¿Estás seguro de que quieres reiniciar ${serviceName}?`)) {
      console.log(`Restarting service: ${serviceName}`);
      // Update service status temporarily
      services.update(serviceList => 
        serviceList.map(service => 
          service.name === serviceName 
            ? { ...service, status: 'restarting' }
            : service
        )
      );
      
      // Simulate restart completion
      setTimeout(() => {
        services.update(serviceList => 
          serviceList.map(service => 
            service.name === serviceName 
              ? { ...service, status: 'running', uptime: '0m' }
              : service
          )
        );
      }, 3000);
    }
  }
  
  function rebootSystem() {
    if (confirm('¿Estás seguro de que quieres reiniciar el sistema? Esto desconectará temporalmente el asistente.')) {
      alert('Sistema reiniciándose... La interfaz se reconectará automáticamente.');
      // In a real system, this would trigger a system reboot
    }
  }
  
  function shutdownSystem() {
    if (confirm('¿Estás seguro de que quieres apagar el sistema? Necesitarás acceso físico para encenderlo nuevamente.')) {
      alert('Sistema apagándose...');
      // In a real system, this would trigger a system shutdown
    }
  }
  
  onMount(() => {
    const interval = setInterval(updateSystemData, 2000);
    return () => clearInterval(interval);
  });
</script>

<div class="settings-view">
  <div class="settings-content">
    <!-- Tab Navigation -->
    <div class="tab-navigation">
      <button 
        class="tab-btn"
        class:active={selectedTab === 'overview'}
        on:click={() => selectedTab = 'overview'}
      >
        📊 Resumen
      </button>
      <button 
        class="tab-btn"
        class:active={selectedTab === 'services'}
        on:click={() => selectedTab = 'services'}
      >
        🔧 Servicios
      </button>
      <button 
        class="tab-btn"
        class:active={selectedTab === 'network'}
        on:click={() => selectedTab = 'network'}
      >
        🌐 Red
      </button>
      <button 
        class="tab-btn"
        class:active={selectedTab === 'power'}
        on:click={() => selectedTab = 'power'}
      >
        ⚡ Energía
      </button>
    </div>
    
    <!-- Tab Content -->
    <div class="tab-content">
      {#if selectedTab === 'overview'}
        <!-- System Overview -->
        <div class="overview-grid">
          <!-- System Info Card -->
          <div class="info-card">
            <h3>Información del Sistema</h3>
            <div class="info-list">
              <div class="info-item">
                <span class="info-label">Hostname:</span>
                <span class="info-value">{$systemInfo.hostname}</span>
              </div>
              <div class="info-item">
                <span class="info-label">SO:</span>
                <span class="info-value">{$systemInfo.os}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Kernel:</span>
                <span class="info-value">{$systemInfo.kernel}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Tiempo activo:</span>
                <span class="info-value">{$systemInfo.uptime}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Carga:</span>
                <span class="info-value">{$systemInfo.load}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Temperatura:</span>
                <span class="info-value" class:temp-warning={$systemInfo.temperature > 60}>
                  {$systemInfo.temperature.toFixed(1)}°C
                </span>
              </div>
            </div>
          </div>
          
          <!-- Resource Usage Card -->
          <div class="info-card">
            <h3>Uso de Recursos</h3>
            <div class="resource-meters">
              <div class="resource-meter">
                <div class="meter-header">
                  <span>CPU</span>
                  <span>{$resources.cpu}%</span>
                </div>
                <div class="meter-bar">
                  <div 
                    class="meter-fill"
                    class:meter-warning={$resources.cpu > 70}
                    class:meter-critical={$resources.cpu > 90}
                    style="width: {$resources.cpu}%"
                  ></div>
                </div>
              </div>
              
              <div class="resource-meter">
                <div class="meter-header">
                  <span>Memoria</span>
                  <span>{$resources.memory}%</span>
                </div>
                <div class="meter-bar">
                  <div 
                    class="meter-fill"
                    class:meter-warning={$resources.memory > 80}
                    class:meter-critical={$resources.memory > 95}
                    style="width: {$resources.memory}%"
                  ></div>
                </div>
              </div>
              
              <div class="resource-meter">
                <div class="meter-header">
                  <span>Almacenamiento</span>
                  <span>{$resources.storage}%</span>
                </div>
                <div class="meter-bar">
                  <div 
                    class="meter-fill"
                    class:meter-warning={$resources.storage > 70}
                    class:meter-critical={$resources.storage > 90}
                    style="width: {$resources.storage}%"
                  ></div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Network Card -->
          <div class="info-card">
            <h3>Estado de Red</h3>
            <div class="network-stats">
              <div class="network-item">
                <span class="network-icon">📥</span>
                <div>
                  <div class="network-label">Descarga</div>
                  <div class="network-value">{$resources.network.rx}</div>
                </div>
              </div>
              <div class="network-item">
                <span class="network-icon">📤</span>
                <div>
                  <div class="network-label">Subida</div>
                  <div class="network-value">{$resources.network.tx}</div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Quick Actions Card -->
          <div class="info-card">
            <h3>Acciones Rápidas</h3>
            <div class="quick-actions">
              <button class="action-btn restart" on:click={rebootSystem}>
                🔄 Reiniciar
              </button>
              <button class="action-btn shutdown" on:click={shutdownSystem}>
                ⏻ Apagar
              </button>
            </div>
          </div>
        </div>
        
      {:else if selectedTab === 'services'}
        <!-- Services Management -->
        <div class="services-section">
          <h3>Gestión de Servicios</h3>
          <div class="services-table">
            <div class="table-header">
              <span>Servicio</span>
              <span>Estado</span>
              <span>Puerto</span>
              <span>Tiempo Activo</span>
              <span>Memoria</span>
              <span>Acciones</span>
            </div>
            {#each $services as service}
              <div class="table-row">
                <span class="service-name">{service.name}</span>
                <span class="service-status status-{service.status}">
                  {service.status === 'running' ? '🟢 Ejecutándose' : 
                   service.status === 'restarting' ? '🟡 Reiniciando' :
                   '🔴 Detenido'}
                </span>
                <span class="service-port">{service.port || 'N/A'}</span>
                <span class="service-uptime">{service.uptime}</span>
                <span class="service-memory">{service.memory}</span>
                <div class="service-actions">
                  <button 
                    class="action-btn-small"
                    on:click={() => restartService(service.name)}
                    disabled={service.status === 'restarting'}
                  >
                    🔄
                  </button>
                </div>
              </div>
            {/each}
          </div>
        </div>
        
      {:else if selectedTab === 'network'}
        <!-- Network Configuration -->
        <div class="network-section">
          <h3>Configuración de Red</h3>
          <div class="network-config">
            <div class="config-group">
              <label>Dirección IP:</label>
              <input type="text" value="192.168.1.100" readonly>
            </div>
            <div class="config-group">
              <label>Puerta de enlace:</label>
              <input type="text" value="192.168.1.1" readonly>
            </div>
            <div class="config-group">
              <label>DNS:</label>
              <input type="text" value="8.8.8.8, 8.8.4.4" readonly>
            </div>
            <div class="config-group">
              <label>SSID WiFi:</label>
              <input type="text" value="PuertoCho_Network" readonly>
            </div>
          </div>
          <p class="network-note">
            ℹ️ La configuración de red se realiza desde el sistema operativo
          </p>
        </div>
        
      {:else if selectedTab === 'power'}
        <!-- Power Management -->
        <div class="power-section">
          <h3>Gestión de Energía</h3>
          <div class="power-options">
            <div class="power-option">
              <h4>Reiniciar Sistema</h4>
              <p>Reinicia completamente el sistema. Todos los servicios se reiniciarán.</p>
              <button class="power-btn restart" on:click={rebootSystem}>
                🔄 Reiniciar Sistema
              </button>
            </div>
            
            <div class="power-option">
              <h4>Apagar Sistema</h4>
              <p>Apaga el sistema de forma segura. Será necesario el acceso físico para encenderlo.</p>
              <button class="power-btn shutdown" on:click={shutdownSystem}>
                ⏻ Apagar Sistema
              </button>
            </div>
            
            <div class="power-option">
              <h4>Modo de Bajo Consumo</h4>
              <p>Reduce el consumo energético limitando algunas funcionalidades.</p>
              <button class="power-btn eco" disabled>
                🌱 Activar (Próximamente)
              </button>
            </div>
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .settings-view {
    height: 100%;
    display: flex;
    flex-direction: column;
    background-color: #f8f9fa;
  }
  
  .settings-header {
    padding: 2rem;
    background: linear-gradient(135deg, #fd7e14 0%, #dc3545 100%);
    color: white;
    text-align: center;
  }
  
  .settings-header h1 {
    margin: 0 0 0.5rem 0;
    font-size: 2rem;
    font-weight: 600;
  }
  
  .settings-header p {
    margin: 0;
    opacity: 0.9;
  }
  
  .settings-content {
    flex: 1;
    padding: 2rem;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  
  /* Tab Navigation */
  .tab-navigation {
    display: flex;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    overflow: hidden;
  }
  
  .tab-btn {
    flex: 1;
    padding: 1rem;
    background: none;
    border: none;
    color: #6c757d;
    cursor: pointer;
    transition: all 0.2s ease;
    border-bottom: 3px solid transparent;
  }
  
  .tab-btn:hover {
    background: #f8f9fa;
    color: #495057;
  }
  
  .tab-btn.active {
    color: #007bff;
    border-bottom-color: #007bff;
    background: white;
  }
  
  /* Tab Content */
  .tab-content {
    flex: 1;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    padding: 2rem;
    overflow-y: auto;
  }
  
  /* Overview Grid */
  .overview-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
  }
  
  .info-card {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 1.5rem;
    border: 1px solid #dee2e6;
  }
  
  .info-card h3 {
    margin: 0 0 1rem 0;
    color: #343a40;
    font-size: 1.25rem;
  }
  
  /* System Info */
  .info-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .info-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
    border-bottom: 1px solid #e9ecef;
  }
  
  .info-item:last-child {
    border-bottom: none;
  }
  
  .info-label {
    font-weight: 600;
    color: #495057;
  }
  
  .info-value {
    color: #343a40;
    font-family: 'Courier New', monospace;
  }
  
  .temp-warning {
    color: #dc3545 !important;
    font-weight: 600;
  }
  
  /* Resource Meters */
  .resource-meters {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .resource-meter {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .meter-header {
    display: flex;
    justify-content: space-between;
    font-weight: 600;
    color: #495057;
  }
  
  .meter-bar {
    height: 8px;
    background: #e9ecef;
    border-radius: 4px;
    overflow: hidden;
  }
  
  .meter-fill {
    height: 100%;
    background: #28a745;
    transition: width 0.3s ease;
  }
  
  .meter-fill.meter-warning {
    background: #ffc107;
  }
  
  .meter-fill.meter-critical {
    background: #dc3545;
  }
  
  /* Network Stats */
  .network-stats {
    display: flex;
    justify-content: space-around;
    gap: 1rem;
  }
  
  .network-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  
  .network-icon {
    font-size: 1.5rem;
  }
  
  .network-label {
    color: #6c757d;
    font-size: 0.9rem;
  }
  
  .network-value {
    color: #343a40;
    font-weight: 600;
    font-family: 'Courier New', monospace;
  }
  
  /* Quick Actions */
  .quick-actions {
    display: flex;
    gap: 1rem;
  }
  
  .action-btn {
    flex: 1;
    padding: 0.75rem;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.2s ease;
  }
  
  .action-btn.restart {
    background: #ffc107;
    color: #212529;
  }
  
  .action-btn.shutdown {
    background: #dc3545;
    color: white;
  }
  
  .action-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  }
  
  /* Services Table */
  .services-section h3 {
    margin: 0 0 1.5rem 0;
    color: #343a40;
  }
  
  .services-table {
    display: grid;
    grid-template-columns: 2fr 1.5fr 1fr 1.5fr 1fr 1fr;
    gap: 0.5rem;
  }
  
  .table-header {
    display: contents;
    font-weight: 600;
    color: #495057;
  }
  
  .table-header > span {
    padding: 0.75rem;
    background: #f8f9fa;
    border-bottom: 2px solid #dee2e6;
  }
  
  .table-row {
    display: contents;
  }
  
  .table-row > span,
  .service-actions {
    padding: 0.75rem;
    border-bottom: 1px solid #e9ecef;
    display: flex;
    align-items: center;
  }
  
  .service-name {
    font-family: 'Courier New', monospace;
    font-weight: 600;
  }
  
  .service-status.status-running {
    color: #28a745;
  }
  
  .service-status.status-restarting {
    color: #ffc107;
  }
  
  .action-btn-small {
    padding: 0.25rem 0.5rem;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8rem;
  }
  
  .action-btn-small:disabled {
    background: #6c757d;
    cursor: not-allowed;
  }
  
  /* Power Section */
  .power-section h3 {
    margin: 0 0 1.5rem 0;
    color: #343a40;
  }
  
  .power-options {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .power-option {
    padding: 1.5rem;
    border: 2px solid #dee2e6;
    border-radius: 12px;
    background: #f8f9fa;
  }
  
  .power-option h4 {
    margin: 0 0 0.5rem 0;
    color: #343a40;
  }
  
  .power-option p {
    margin: 0 0 1rem 0;
    color: #6c757d;
  }
  
  .power-btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.2s ease;
  }
  
  .power-btn.restart {
    background: #ffc107;
    color: #212529;
  }
  
  .power-btn.shutdown {
    background: #dc3545;
    color: white;
  }
  
  .power-btn.eco {
    background: #28a745;
    color: white;
  }
  
  .power-btn:disabled {
    background: #6c757d;
    cursor: not-allowed;
  }
  
  .power-btn:not(:disabled):hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  }
  
  /* Network Configuration */
  .network-section h3 {
    margin: 0 0 1.5rem 0;
    color: #343a40;
  }
  
  .network-config {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 1rem;
  }
  
  .config-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .config-group label {
    font-weight: 600;
    color: #495057;
  }
  
  .config-group input {
    padding: 0.75rem;
    border: 2px solid #dee2e6;
    border-radius: 8px;
    background: #f8f9fa;
  }
  
  .network-note {
    color: #6c757d;
    font-style: italic;
    background: #e7f1ff;
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #007bff;
  }
  
  /* Responsive Design */
  @media (max-width: 768px) {
    .settings-content {
      padding: 1rem;
    }
    
    .overview-grid {
      grid-template-columns: 1fr;
    }
    
    .services-table {
      grid-template-columns: 1fr;
      gap: 0;
    }
    
    .table-header {
      display: none;
    }
    
    .table-row {
      display: flex;
      flex-direction: column;
      background: #f8f9fa;
      margin-bottom: 1rem;
      border-radius: 8px;
      overflow: hidden;
    }
    
    .network-stats {
      flex-direction: column;
      align-items: center;
    }
    
    .quick-actions {
      flex-direction: column;
    }
    
    .tab-navigation {
      flex-wrap: wrap;
    }
    
    .tab-btn {
      flex: 1 1 50%;
    }
  }
</style>

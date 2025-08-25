<script lang="ts">
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';
  
  // Mock log data - in reality this would come from backend
  const logs = writable([]);
  
  let logLevel = 'all'; // all, info, warn, error, debug
  let autoRefresh = true;
  let refreshInterval: number;
  
  const logLevels = [
    { value: 'all', label: 'Todos', color: '#6c757d', icon: '📋' },
    { value: 'info', label: 'Info', color: '#17a2b8', icon: 'ℹ️' },
    { value: 'warn', label: 'Advertencias', color: '#ffc107', icon: '⚠️' },
    { value: 'error', label: 'Errores', color: '#dc3545', icon: '❌' },
    { value: 'debug', label: 'Debug', color: '#28a745', icon: '🐛' }
  ];
  
  // Generate mock log entries
  function generateMockLogs() {
    const mockEntries = [
      { level: 'info', message: 'WebSocket connection established', component: 'WebSocketService', timestamp: new Date().toISOString() },
      { level: 'info', message: 'Audio processing started', component: 'AudioProcessor', timestamp: new Date(Date.now() - 5000).toISOString() },
      { level: 'warn', message: 'High audio queue length detected', component: 'AudioProcessor', timestamp: new Date(Date.now() - 10000).toISOString() },
      { level: 'error', message: 'Failed to connect to remote backend', component: 'RemoteBackendClient', timestamp: new Date(Date.now() - 15000).toISOString() },
      { level: 'debug', message: 'Voice activation threshold adjusted', component: 'VoiceDetector', timestamp: new Date(Date.now() - 20000).toISOString() },
      { level: 'info', message: 'Configuration saved successfully', component: 'ConfigManager', timestamp: new Date(Date.now() - 25000).toISOString() },
      { level: 'warn', message: 'Memory usage above 80%', component: 'SystemMonitor', timestamp: new Date(Date.now() - 30000).toISOString() },
      { level: 'error', message: 'Audio device not found', component: 'AudioCapture', timestamp: new Date(Date.now() - 35000).toISOString() },
      { level: 'info', message: 'Kiosk mode activated', component: 'DisplayManager', timestamp: new Date(Date.now() - 40000).toISOString() },
      { level: 'debug', message: 'Navigation state changed to config', component: 'NavigationStore', timestamp: new Date(Date.now() - 45000).toISOString() }
    ];
    
    logs.set(mockEntries);
  }
  
  // Filter logs based on selected level
  $: filteredLogs = logLevel === 'all' 
    ? $logs 
    : $logs.filter(log => log.level === logLevel);
  
  function formatTimestamp(timestamp: string): string {
    return new Date(timestamp).toLocaleString();
  }
  
  function getLogLevelInfo(level: string) {
    return logLevels.find(l => l.value === level) || logLevels[0];
  }
  
  function clearLogs() {
    if (confirm('¿Estás seguro de que quieres limpiar todos los logs?')) {
      logs.set([]);
    }
  }
  
  function downloadLogs() {
    const logData = $logs.map(log => 
      `[${formatTimestamp(log.timestamp)}] [${log.level.toUpperCase()}] [${log.component}] ${log.message}`
    ).join('\n');
    
    const blob = new Blob([logData], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `puertocho-logs-${new Date().toISOString().split('T')[0]}.log`;
    a.click();
    URL.revokeObjectURL(url);
  }
  
  function toggleAutoRefresh() {
    autoRefresh = !autoRefresh;
    if (autoRefresh) {
      startAutoRefresh();
    } else {
      stopAutoRefresh();
    }
  }
  
  function startAutoRefresh() {
    refreshInterval = setInterval(() => {
      // In a real app, this would fetch new logs from backend
      if (Math.random() > 0.7) { // 30% chance of new log
        const levels = ['info', 'warn', 'error', 'debug'];
        const components = ['AudioProcessor', 'WebSocketService', 'SystemMonitor', 'VoiceDetector'];
        const messages = [
          'New audio file processed',
          'WebSocket message received',
          'System health check completed',
          'Voice detection threshold met',
          'Configuration updated',
          'Cache cleared successfully'
        ];
        
        const newLog = {
          level: levels[Math.floor(Math.random() * levels.length)],
          message: messages[Math.floor(Math.random() * messages.length)],
          component: components[Math.floor(Math.random() * components.length)],
          timestamp: new Date().toISOString()
        };
        
        logs.update(currentLogs => [newLog, ...currentLogs].slice(0, 100)); // Keep only last 100 logs
      }
    }, 3000);
  }
  
  function stopAutoRefresh() {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
  }
  
  onMount(() => {
    generateMockLogs();
    if (autoRefresh) {
      startAutoRefresh();
    }
    
    return () => {
      stopAutoRefresh();
    };
  });
</script>

<div class="logs-view">
  <div class="logs-header">
    <h1>Registros del Sistema</h1>
    <p>Monitoreo en tiempo real de eventos y errores</p>
  </div>
  
  <div class="logs-content">
    <!-- Controls -->
    <div class="logs-controls">
      <div class="level-filters">
        {#each logLevels as level}
          <button 
            class="level-filter-btn"
            class:active={logLevel === level.value}
            style="--level-color: {level.color}"
            on:click={() => logLevel = level.value}
          >
            {level.icon} {level.label}
            <span class="count">
              ({logLevel === 'all' ? $logs.length : $logs.filter(log => log.level === level.value).length})
            </span>
          </button>
        {/each}
      </div>
      
      <div class="action-controls">
        <button 
          class="control-btn"
          class:active={autoRefresh}
          on:click={toggleAutoRefresh}
          title="Activar/desactivar actualización automática"
        >
          {autoRefresh ? '⏸️' : '▶️'} Auto-actualizar
        </button>
        <button class="control-btn" on:click={() => generateMockLogs()}>
          🔄 Actualizar
        </button>
        <button class="control-btn" on:click={downloadLogs}>
          📥 Descargar
        </button>
        <button class="control-btn danger" on:click={clearLogs}>
          🗑️ Limpiar
        </button>
      </div>
    </div>
    
    <!-- Logs Display -->
    <div class="logs-container">
      {#if filteredLogs.length === 0}
        <div class="no-logs">
          <div class="no-logs-icon">📊</div>
          <h3>No hay logs disponibles</h3>
          <p>
            {#if logLevel === 'all'}
              No se han registrado eventos aún
            {:else}
              No hay logs de nivel "{getLogLevelInfo(logLevel).label}"
            {/if}
          </p>
        </div>
      {:else}
        <div class="logs-list">
          {#each filteredLogs as log}
            {@const levelInfo = getLogLevelInfo(log.level)}
            <div 
              class="log-entry"
              class:log-error={log.level === 'error'}
              class:log-warn={log.level === 'warn'}
              class:log-info={log.level === 'info'}
              class:log-debug={log.level === 'debug'}
            >
              <div class="log-indicator" style="background-color: {levelInfo.color}"></div>
              <div class="log-content">
                <div class="log-header">
                  <span class="log-level" style="color: {levelInfo.color}">
                    {levelInfo.icon} {levelInfo.label.toUpperCase()}
                  </span>
                  <span class="log-component">[{log.component}]</span>
                  <span class="log-timestamp">{formatTimestamp(log.timestamp)}</span>
                </div>
                <div class="log-message">{log.message}</div>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .logs-view {
    height: 100%;
    display: flex;
    flex-direction: column;
    background-color: #f8f9fa;
  }
  
  .logs-header {
    padding: 2rem;
    background: linear-gradient(135deg, #6f42c1 0%, #e83e8c 100%);
    color: white;
    text-align: center;
  }
  
  .logs-header h1 {
    margin: 0 0 0.5rem 0;
    font-size: 2rem;
    font-weight: 600;
  }
  
  .logs-header p {
    margin: 0;
    opacity: 0.9;
  }
  
  .logs-content {
    flex: 1;
    padding: 2rem;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    min-height: 0;
  }
  
  /* Controls */
  .logs-controls {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
  }
  
  .level-filters {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }
  
  .level-filter-btn {
    padding: 0.5rem 1rem;
    background: white;
    border: 2px solid var(--level-color, #dee2e6);
    border-radius: 20px;
    color: var(--level-color, #6c757d);
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .level-filter-btn:hover {
    background: var(--level-color, #f8f9fa);
    color: white;
  }
  
  .level-filter-btn.active {
    background: var(--level-color, #007bff);
    color: white;
  }
  
  .count {
    background: rgba(255, 255, 255, 0.2);
    padding: 0.125rem 0.375rem;
    border-radius: 10px;
    font-size: 0.75rem;
  }
  
  .action-controls {
    display: flex;
    gap: 0.5rem;
  }
  
  .control-btn {
    padding: 0.5rem 1rem;
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.85rem;
    transition: all 0.2s ease;
  }
  
  .control-btn:hover {
    background: #e9ecef;
  }
  
  .control-btn.active {
    background: #007bff;
    color: white;
    border-color: #007bff;
  }
  
  .control-btn.danger {
    background: #dc3545;
    color: white;
    border-color: #dc3545;
  }
  
  .control-btn.danger:hover {
    background: #c82333;
  }
  
  /* Logs Container */
  .logs-container {
    flex: 1;
    background: #1a1a1a;
    border-radius: 12px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }
  
  .logs-list {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
  }
  
  .log-entry {
    display: flex;
    gap: 0.75rem;
    padding: 0.75rem;
    border-radius: 8px;
    margin-bottom: 0.5rem;
    background: #2a2a2a;
    transition: background-color 0.2s ease;
    border-left: 4px solid transparent;
  }
  
  .log-entry:hover {
    background: #333333;
  }
  
  .log-entry.log-error {
    border-left-color: #dc3545;
    background: rgba(220, 53, 69, 0.1);
  }
  
  .log-entry.log-warn {
    border-left-color: #ffc107;
    background: rgba(255, 193, 7, 0.1);
  }
  
  .log-entry.log-info {
    border-left-color: #17a2b8;
    background: rgba(23, 162, 184, 0.1);
  }
  
  .log-entry.log-debug {
    border-left-color: #28a745;
    background: rgba(40, 167, 69, 0.1);
  }
  
  .log-indicator {
    width: 4px;
    border-radius: 2px;
    flex-shrink: 0;
  }
  
  .log-content {
    flex: 1;
    min-width: 0;
  }
  
  .log-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.25rem;
    font-size: 0.85rem;
  }
  
  .log-level {
    font-weight: 600;
    font-size: 0.75rem;
    white-space: nowrap;
  }
  
  .log-component {
    color: #6c757d;
    font-family: 'Courier New', monospace;
    font-size: 0.8rem;
    white-space: nowrap;
  }
  
  .log-timestamp {
    color: #adb5bd;
    font-size: 0.75rem;
    margin-left: auto;
    white-space: nowrap;
  }
  
  .log-message {
    color: #e9ecef;
    font-family: 'Courier New', monospace;
    font-size: 0.9rem;
    line-height: 1.4;
    word-break: break-word;
  }
  
  /* No Logs */
  .no-logs {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    color: #6c757d;
    padding: 4rem 2rem;
  }
  
  .no-logs-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
  }
  
  .no-logs h3 {
    margin: 0 0 0.5rem 0;
    color: #adb5bd;
  }
  
  .no-logs p {
    text-align: center;
    color: #6c757d;
  }
  
  /* Scrollbar */
  .logs-list::-webkit-scrollbar {
    width: 8px;
  }
  
  .logs-list::-webkit-scrollbar-track {
    background: #333333;
  }
  
  .logs-list::-webkit-scrollbar-thumb {
    background: #555555;
    border-radius: 4px;
  }
  
  .logs-list::-webkit-scrollbar-thumb:hover {
    background: #777777;
  }
  
  /* Responsive Design */
  @media (max-width: 768px) {
    .logs-content {
      padding: 1rem;
    }
    
    .logs-controls {
      flex-direction: column;
      align-items: stretch;
      gap: 1rem;
    }
    
    .level-filters {
      justify-content: center;
    }
    
    .action-controls {
      justify-content: center;
      flex-wrap: wrap;
    }
    
    .log-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.25rem;
    }
    
    .log-timestamp {
      margin-left: 0;
    }
  }
</style>

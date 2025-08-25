<script lang="ts">
  import { commandHistory } from '$lib/stores/assistantStore';
  import { audioHistory } from '$lib/stores/audioStore';
  
  let filterType = 'all'; // all, voice, manual, errors
  let searchQuery = '';
  
  // Combine and sort all history items
  $: allHistory = [
    ...$commandHistory.map(cmd => ({
      ...cmd,
      type: 'command',
      icon: '🗣️'
    })),
    ...$audioHistory.map(audio => ({
      timestamp: audio.timestamp,
      command: `Audio: ${audio.filename}`,
      type: 'audio',
      icon: '🎵',
      status: audio.status,
      size: audio.size,
      duration: audio.duration
    }))
  ].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  
  // Filter history based on search and filter type
  $: filteredHistory = allHistory.filter(item => {
    const matchesSearch = searchQuery === '' || 
      item.command.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesFilter = filterType === 'all' || 
      (filterType === 'voice' && item.type === 'command') ||
      (filterType === 'manual' && item.command.startsWith('Manual:')) ||
      (filterType === 'audio' && item.type === 'audio') ||
      (filterType === 'errors' && item.status === 'error');
    
    return matchesSearch && matchesFilter;
  });
  
  function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
  
  function formatDuration(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }
  
  function clearHistory() {
    if (confirm('¿Estás seguro de que quieres eliminar todo el historial?')) {
      commandHistory.set([]);
      // Note: audioHistory clearing would need backend coordination
      alert('Historial de comandos eliminado');
    }
  }
  
  function exportHistory() {
    const data = JSON.stringify(filteredHistory, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `puertocho-history-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
</script>

<div class="history-view">
  <div class="history-header">
    <h1>Historial de Actividad</h1>
    <p>Registro completo de comandos y actividades del asistente</p>
  </div>
  
  <div class="history-content">
    <!-- Controls -->
    <div class="history-controls">
      <div class="search-filter-section">
        <div class="search-box">
          <input 
            type="text" 
            placeholder="Buscar en historial..." 
            bind:value={searchQuery}
            class="search-input"
          >
          <span class="search-icon">🔍</span>
        </div>
        
        <div class="filter-buttons">
          <button 
            class="filter-btn"
            class:active={filterType === 'all'}
            on:click={() => filterType = 'all'}
          >
            📋 Todos
          </button>
          <button 
            class="filter-btn"
            class:active={filterType === 'voice'}
            on:click={() => filterType = 'voice'}
          >
            🗣️ Voz
          </button>
          <button 
            class="filter-btn"
            class:active={filterType === 'manual'}
            on:click={() => filterType = 'manual'}
          >
            👆 Manual
          </button>
          <button 
            class="filter-btn"
            class:active={filterType === 'audio'}
            on:click={() => filterType = 'audio'}
          >
            🎵 Audio
          </button>
          <button 
            class="filter-btn"
            class:active={filterType === 'errors'}
            on:click={() => filterType = 'errors'}
          >
            ❌ Errores
          </button>
        </div>
      </div>
      
      <div class="action-buttons">
        <button class="btn btn-secondary" on:click={exportHistory}>
          📤 Exportar
        </button>
        <button class="btn btn-danger" on:click={clearHistory}>
          🗑️ Limpiar
        </button>
      </div>
    </div>
    
    <!-- History List -->
    <div class="history-list">
      {#if filteredHistory.length === 0}
        <div class="no-results">
          <div class="no-results-icon">📭</div>
          <h3>No se encontraron resultados</h3>
          <p>
            {#if searchQuery}
              No hay elementos que coincidan con "{searchQuery}"
            {:else}
              No hay actividad registrada para este filtro
            {/if}
          </p>
        </div>
      {:else}
        {#each filteredHistory as item}
          <div class="history-item" class:error={item.status === 'error'}>
            <div class="item-icon">{item.icon}</div>
            <div class="item-content">
              <div class="item-header">
                <span class="item-command">{item.command}</span>
                <span class="item-timestamp">{item.timestamp}</span>
              </div>
              {#if item.type === 'audio'}
                <div class="item-details">
                  {#if item.duration}
                    <span class="detail-badge">⏱️ {formatDuration(item.duration)}</span>
                  {/if}
                  {#if item.size}
                    <span class="detail-badge">📦 {formatFileSize(item.size)}</span>
                  {/if}
                  {#if item.status}
                    <span class="detail-badge status-{item.status}">
                      {item.status === 'processing' ? '⏳ Procesando' :
                       item.status === 'completed' ? '✅ Completado' :
                       item.status === 'error' ? '❌ Error' : item.status}
                    </span>
                  {/if}
                </div>
              {/if}
            </div>
          </div>
        {/each}
      {/if}
    </div>
  </div>
</div>

<style>
  .history-view {
    height: 100%;
    display: flex;
    flex-direction: column;
    background-color: #f8f9fa;
  }
  
  .history-header {
    padding: 2rem;
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
    color: white;
    text-align: center;
  }
  
  .history-header h1 {
    margin: 0 0 0.5rem 0;
    font-size: 2rem;
    font-weight: 600;
  }
  
  .history-header p {
    margin: 0;
    opacity: 0.9;
  }
  
  .history-content {
    flex: 1;
    padding: 2rem;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  
  /* Controls */
  .history-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  
  .search-filter-section {
    flex: 1;
    display: flex;
    gap: 1rem;
    align-items: center;
  }
  
  .search-box {
    position: relative;
    min-width: 300px;
  }
  
  .search-input {
    width: 100%;
    padding: 0.75rem 2.5rem 0.75rem 1rem;
    border: 2px solid #dee2e6;
    border-radius: 8px;
    font-size: 1rem;
  }
  
  .search-input:focus {
    outline: none;
    border-color: #007bff;
  }
  
  .search-icon {
    position: absolute;
    right: 1rem;
    top: 50%;
    transform: translateY(-50%);
    color: #6c757d;
  }
  
  .filter-buttons {
    display: flex;
    gap: 0.5rem;
  }
  
  .filter-btn {
    padding: 0.5rem 1rem;
    background: #f8f9fa;
    border: 2px solid #dee2e6;
    border-radius: 20px;
    color: #6c757d;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.85rem;
    white-space: nowrap;
  }
  
  .filter-btn:hover {
    background: #e9ecef;
    border-color: #adb5bd;
  }
  
  .filter-btn.active {
    background: #007bff;
    border-color: #007bff;
    color: white;
  }
  
  .action-buttons {
    display: flex;
    gap: 0.75rem;
  }
  
  .btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    transition: all 0.2s ease;
  }
  
  .btn-secondary {
    background: #6c757d;
    color: white;
  }
  
  .btn-danger {
    background: #dc3545;
    color: white;
  }
  
  .btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }
  
  /* History List */
  .history-list {
    flex: 1;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    overflow-y: auto;
    padding: 1rem;
  }
  
  .history-item {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 1rem;
    border-bottom: 1px solid #e9ecef;
    transition: background-color 0.2s ease;
  }
  
  .history-item:hover {
    background-color: #f8f9fa;
  }
  
  .history-item:last-child {
    border-bottom: none;
  }
  
  .history-item.error {
    border-left: 4px solid #dc3545;
    background-color: #fdf2f2;
  }
  
  .item-icon {
    font-size: 1.2rem;
    width: 2rem;
    text-align: center;
    flex-shrink: 0;
  }
  
  .item-content {
    flex: 1;
    min-width: 0;
  }
  
  .item-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;
  }
  
  .item-command {
    font-weight: 600;
    color: #343a40;
    flex: 1;
    margin-right: 1rem;
    word-break: break-word;
  }
  
  .item-timestamp {
    color: #6c757d;
    font-size: 0.85rem;
    white-space: nowrap;
  }
  
  .item-details {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }
  
  .detail-badge {
    padding: 0.25rem 0.5rem;
    background: #e9ecef;
    border-radius: 12px;
    font-size: 0.75rem;
    color: #495057;
  }
  
  .detail-badge.status-completed {
    background: #d4edda;
    color: #155724;
  }
  
  .detail-badge.status-processing {
    background: #fff3cd;
    color: #856404;
  }
  
  .detail-badge.status-error {
    background: #f8d7da;
    color: #721c24;
  }
  
  /* No Results */
  .no-results {
    text-align: center;
    padding: 4rem 2rem;
    color: #6c757d;
  }
  
  .no-results-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
  }
  
  .no-results h3 {
    margin: 0 0 0.5rem 0;
    color: #495057;
  }
  
  /* Responsive Design */
  @media (max-width: 768px) {
    .history-content {
      padding: 1rem;
    }
    
    .history-controls {
      flex-direction: column;
      align-items: stretch;
      gap: 1rem;
    }
    
    .search-filter-section {
      flex-direction: column;
    }
    
    .search-box {
      min-width: unset;
    }
    
    .filter-buttons {
      flex-wrap: wrap;
    }
    
    .action-buttons {
      justify-content: center;
    }
    
    .item-header {
      flex-direction: column;
      gap: 0.5rem;
    }
    
    .item-command {
      margin-right: 0;
    }
  }
</style>

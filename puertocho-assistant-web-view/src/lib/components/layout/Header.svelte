<script lang="ts">
  import { isConnected } from '$lib/stores/assistantStore';
</script>

<header class="app-header">
  <div class="header-content">
    <h1>Dashboard de PuertoCho Assistant</h1>
    <div class="connection-status">
      {#if $isConnected}
        <span class="dot connected"></span> Conectado
      {:else}
        <span class="dot disconnected"></span> Desconectado
      {/if}
    </div>
  </div>
</header>

<style>
  .app-header {
    background-color: #fff;
    border-bottom: 1px solid #dee2e6;
    padding: 1rem 2rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1200px;
    margin: 0 auto;
  }

  h1 {
    color: #343a40;
    font-size: 1.8rem;
    margin: 0;
  }

  .connection-status {
    display: flex;
    align-items: center;
    font-size: 0.9rem;
    color: #6c757d;
    padding: 0.25rem 0.75rem;
    border: 1px solid #dee2e6;
    border-radius: 1rem;
    background-color: #f8f9fa;
  }

  .dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 0.5rem;
  }

  .connected {
    background-color: #28a745;
  }

  .disconnected {
    background-color: #dc3545;
  }

  @media (max-width: 768px) {
    .app-header {
      padding: 1rem;
    }
    
    .header-content {
      flex-direction: column;
      gap: 1rem;
    }
    
    h1 {
      font-size: 1.5rem;
    }
  }
</style>

<script lang="ts">
  import StatusIndicator from '$lib/components/StatusIndicator.svelte';
  import CommandHistory from '$lib/components/CommandHistory.svelte';
  import ManualActivation from '$lib/components/ManualActivation.svelte';
  import AudioProcessor from '$lib/components/AudioProcessor.svelte';
  import AudioHistory from '$lib/components/AudioHistory.svelte';
  import { assistantStatus, commandHistory, isConnected, audioProcessingState } from '$lib/stores/assistantStore';
</script>

<main>
  <header>
    <h1>Dashboard de PuertoCho Assistant</h1>
    <div class="connection-status">
      {#if $isConnected}
        <span class="dot connected"></span> Conectado
      {:else}
        <span class="dot disconnected"></span> Desconectado
      {/if}
    </div>
    <StatusIndicator status={$assistantStatus} />
    <ManualActivation />
  </header>

  <section>
    <div class="dashboard-grid">
      <!-- Left column: Commands and Status -->
      <div class="left-column">
        <CommandHistory commands={$commandHistory} />
      </div>
      
      <!-- Right column: Audio Processing -->
      <div class="right-column">
        <AudioProcessor />
        <AudioHistory />
      </div>
    </div>
  </section>
</main>

<style>
  :global(body) {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
      Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    background-color: #f8f9fa;
    color: #212529;
  }

  main {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 2rem;
  }

  header {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    margin-bottom: 2rem;
    position: relative;
  }

  h1 {
    color: #343a40;
    font-size: 2.5rem;
    text-align: center;
  }

  .connection-status {
    display: flex;
    align-items: center;
    font-size: 0.9rem;
    color: #6c757d;
    padding: 0.25rem 0.75rem;
    border: 1px solid #dee2e6;
    border-radius: 1rem;
    background-color: #fff;
  }

  .dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 0.5rem;
  }

  .connected {
    background-color: #28a745; /* Verde */
  }

  .disconnected {
    background-color: #dc3545; /* Rojo */
  }

  section {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
  }
  
  .dashboard-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
    width: 100%;
  }
  
  .left-column,
  .right-column {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  
  /* Mobile responsiveness */
  @media (max-width: 768px) {
    .dashboard-grid {
      grid-template-columns: 1fr;
      gap: 1rem;
    }
    
    main {
      padding: 1rem;
    }
    
    h1 {
      font-size: 2rem;
    }
  }
</style>

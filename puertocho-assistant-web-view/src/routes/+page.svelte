<script lang="ts">
  import StatusIndicator from '$lib/components/StatusIndicator.svelte';
  import CommandHistory from '$lib/components/CommandHistory.svelte';
  import ManualActivation from '$lib/components/ManualActivation.svelte';
  import { assistantStatus, commandHistory, isConnected } from '$lib/stores/assistantStore';
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
    <CommandHistory commands={$commandHistory} />
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
    display: flex;
    justify-content: center;
  }
</style>

<script lang="ts">
  export let commands: { timestamp: string; command: string }[] = [];
</script>

<div class="command-history">
  <h2>Historial de Comandos</h2>
  {#if commands.length === 0}
    <p class="empty-history">Aún no se han detectado comandos.</p>
  {:else}
    <ul>
      {#each commands as item}
        <li>
          <span class="timestamp">{item.timestamp}</span>
          <span class="command">{item.command}</span>
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .command-history {
    width: 100%;
    max-width: 600px;
    margin: 1rem auto;
    padding: 1rem;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    background-color: #fafafa;
    font-family: sans-serif;
  }

  h2 {
    margin-top: 0;
    color: #333;
    text-align: center;
  }

  .empty-history {
    text-align: center;
    color: #888;
  }

  ul {
    list-style: none;
    padding: 0;
    margin: 0;
    max-height: 300px;
    overflow-y: auto;
  }

  li {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid #eee;
  }

  li:last-child {
    border-bottom: none;
  }

  .timestamp {
    color: #666;
    font-size: 0.85rem;
    margin-right: 1rem;
  }

  .command {
    color: #111;
    font-weight: 500;
  }
</style>

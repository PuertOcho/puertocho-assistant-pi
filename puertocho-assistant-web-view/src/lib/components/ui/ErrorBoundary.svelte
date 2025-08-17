<script lang="ts">
  import { onMount } from 'svelte';
  
  export let error: Error | null = null;
  export let retry: (() => void) | null = null;
  
  let errorMessage = '';
  
  $: if (error) {
    errorMessage = error.message || 'Ha ocurrido un error inesperado';
  }
  
  onMount(() => {
    if (error) {
      console.error('ErrorBoundary caught error:', error);
    }
  });
</script>

{#if error}
  <div class="error-boundary">
    <div class="error-content">
      <h3>¡Ups! Algo salió mal</h3>
      <p class="error-message">{errorMessage}</p>
      {#if retry}
        <button class="retry-button" on:click={retry}>
          Intentar de nuevo
        </button>
      {/if}
    </div>
  </div>
{:else}
  <slot />
{/if}

<style>
  .error-boundary {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    background-color: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 0.5rem;
    margin: 1rem 0;
  }
  
  .error-content {
    text-align: center;
    max-width: 400px;
  }
  
  h3 {
    color: #dc2626;
    margin: 0 0 1rem 0;
    font-size: 1.25rem;
  }
  
  .error-message {
    color: #7f1d1d;
    margin: 0 0 1.5rem 0;
    line-height: 1.5;
  }
  
  .retry-button {
    background-color: #dc2626;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 0.375rem;
    cursor: pointer;
    font-size: 0.875rem;
    transition: background-color 0.2s;
  }
  
  .retry-button:hover {
    background-color: #b91c1c;
  }
</style>

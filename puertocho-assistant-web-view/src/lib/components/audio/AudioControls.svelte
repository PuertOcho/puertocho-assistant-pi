<script lang="ts">
  import { AudioProcessor, AudioHistory, AudioPlayer } from './';
  import { audioProcessingState } from '$lib/stores/assistantStore';
  
  export let showHistory = true;
  export let showPlayer = true;
  export let showProcessor = true;
</script>

<div class="audio-controls-container">
  {#if showProcessor}
    <div class="audio-section">
      <h3>Procesamiento de Audio</h3>
      <AudioProcessor />
    </div>
  {/if}
  
  {#if showPlayer}
    <div class="audio-section">
      <h3>Reproductor</h3>
      <AudioPlayer />
    </div>
  {/if}
  
  {#if showHistory}
    <div class="audio-section">
      <h3>Historial de Audio</h3>
      <AudioHistory />
    </div>
  {/if}
</div>

<style>
  .audio-controls-container {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .audio-section {
    background-color: #fff;
    border-radius: 0.5rem;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  h3 {
    margin: 0 0 1rem 0;
    color: #374151;
    font-size: 1.125rem;
    font-weight: 600;
  }
</style>

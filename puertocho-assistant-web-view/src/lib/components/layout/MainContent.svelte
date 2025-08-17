<script lang="ts">
  import { StatusIndicator } from '../ui';
  import { ManualActivation } from '../controls';
  import { CommandHistory } from '../assistant';
  import { AudioControls } from '../audio';
  import { assistantStatus, commandHistory } from '$lib/stores/assistantStore';
</script>

<main class="main-content">
  <div class="controls-section">
    <StatusIndicator status={$assistantStatus} />
    <ManualActivation />
  </div>

  <section class="dashboard-section">
    <div class="dashboard-grid">
      <!-- Left column: Commands and Status -->
      <div class="left-column">
        <CommandHistory commands={$commandHistory} />
      </div>
      
      <!-- Right column: Audio Processing -->
      <div class="right-column">
        <AudioControls />
      </div>
    </div>
  </section>
</main>

<style>
  .main-content {
    flex: 1;
    padding: 2rem;
    overflow-y: auto;
  }

  .controls-section {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    margin-bottom: 2rem;
  }

  .dashboard-section {
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
    .main-content {
      padding: 1rem;
    }
    
    .dashboard-grid {
      grid-template-columns: 1fr;
      gap: 1rem;
    }
  }
</style>

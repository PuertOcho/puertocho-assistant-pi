<script lang="ts">
  import { activeView } from '$lib/stores/navigationStore';
  
  // Import view components
  import HomeView from '../views/HomeView.svelte';
  import ConfigView from '../views/ConfigView.svelte';
  import HistoryView from '../views/HistoryView.svelte';
  import LogsView from '../views/LogsView.svelte';
  import SettingsView from '../views/SettingsView.svelte';
</script>

<div class="main-view-container">
  {#if $activeView === 'home'}
    <HomeView />
  {:else if $activeView === 'config'}
    <ConfigView />
  {:else if $activeView === 'history'}
    <HistoryView />
  {:else if $activeView === 'logs'}
    <LogsView />
  {:else if $activeView === 'settings'}
    <SettingsView />
  {:else}
    <!-- Fallback to home -->
    <HomeView />
  {/if}
</div>

<style>
  .main-view-container {
    height: 100%;
    width: 100%;
    overflow-y: auto;
    background-color: #ffffff;
  }
  
  /* Custom scrollbar */
  .main-view-container::-webkit-scrollbar {
    width: 8px;
  }
  
  .main-view-container::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 4px;
  }
  
  .main-view-container::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 4px;
  }
  
  .main-view-container::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
  }
</style>

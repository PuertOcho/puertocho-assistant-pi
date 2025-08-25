<script lang="ts">
  import { onMount } from 'svelte';
  import { activeView, sideNavVisible } from '$lib/stores/navigationStore';
  import { assistantStatus, isConnected } from '$lib/stores/assistantStore';
  import { audioProcessingState } from '$lib/stores/audioStore';
  
  import SideNavigation from './SideNavigation.svelte';
  import TopStatusBar from './TopStatusBar.svelte';
  import MainView from './MainView.svelte';
  
  // Side navigation is always visible - no responsive behavior
</script>


<div class="three-column-layout">
  <!-- Side Navigation (Left Column - fixed 200px width) -->
  <aside class="side-navigation">
    <SideNavigation />
  </aside>
  
  <!-- Main Content Area -->
  <div class="main-area">
    <!-- Top Status Bar (7% height) -->
    <header class="top-status-bar">
      <TopStatusBar />
    </header>
    
    <!-- Main View (93% height) -->
    <main class="main-view">
      <MainView />
    </main>
  </div>
</div>

<style>
  .three-column-layout {
    display: flex;
    width: 100%;
    height: 100vh;
    overflow: hidden;
    background-color: #f8f9fa;
  }
  
  /* Side Navigation */
  .side-navigation {
    width: 13%;
    height: 100vh;
    background-color: #2c3e50;
    border-right: 1px solid #34495e;
    z-index: 100;
  }
  
  /* Main Content Area */
  .main-area {
    width: 87%;
    height: 100vh;
    display: flex;
    flex-direction: column;
  }
  
  /* Top Status Bar */
  .top-status-bar {
    width: 100%;
    height: 15vh;
    background-color: #ffffff;
    border-bottom: 1px solid #dee2e6;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    z-index: 90;
  }
  
  /* Main View */
  .main-view {
    width: 100%;
    height: 85vh;
    overflow-y: auto;
    padding: 1rem;
  }
</style>

<script lang="ts">
  import { onMount } from 'svelte';
  import { activeView, sideNavVisible } from '$lib/stores/navigationStore';
  import { assistantStatus, isConnected } from '$lib/stores/assistantStore';
  import { audioProcessingState } from '$lib/stores/audioStore';
  
  import SideNavigation from './SideNavigation.svelte';
  import TopStatusBar from './TopStatusBar.svelte';
  import MainView from './MainView.svelte';
  
  let isPortrait = false;
  
  function checkOrientation() {
    isPortrait = window.innerHeight > window.innerWidth;
  }
  
  onMount(() => {
    checkOrientation();
    window.addEventListener('resize', checkOrientation);
    window.addEventListener('orientationchange', () => {
      setTimeout(checkOrientation, 100);
    });
    
    return () => {
      window.removeEventListener('resize', checkOrientation);
      window.removeEventListener('orientationchange', checkOrientation);
    };
  });
</script>


<div class="three-column-layout" class:portrait-mode={isPortrait}>
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
    flex-shrink: 0;
  }
  
  /* Main Content Area */
  .main-area {
    width: 87%;
    height: 100vh;
    display: flex;
    flex-direction: column;
    flex: 1;
  }
  
  /* Top Status Bar */
  .top-status-bar {
    width: 100%;
    height: 15vh;
    background-color: #ffffff;
    border-bottom: 1px solid #dee2e6;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    z-index: 90;
    flex-shrink: 0;
  }
  
  /* Main View */
  .main-view {
    width: 100%;
    height: 85vh;
    overflow-y: auto;
    padding: 1rem;
    flex: 1;
  }
  
  /* Ajustes para modo portrait */
  .three-column-layout.portrait-mode {
    /* Usar dimensiones fijas basadas en el viewport original */
    min-width: 100%;
    min-height: 100%;
  }
  
  .portrait-mode .side-navigation {
    /* Mantener proporciones fijas en portrait */
    padding-left: 27px;
    width: 13vh;
  }
  
  .portrait-mode .main-area {
    width: 87%;
    flex: 1;
  }
  
  .portrait-mode .top-status-bar {
    height: 8vh;
  }
  
  .portrait-mode .main-view {
    height: 85vh;
    flex: 1;
  }
</style>

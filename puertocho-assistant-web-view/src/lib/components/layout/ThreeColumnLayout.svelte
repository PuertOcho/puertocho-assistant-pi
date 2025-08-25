<script lang="ts">
  import { onMount } from 'svelte';
  import { activeView, sideNavVisible } from '$lib/stores/navigationStore';
  import { assistantStatus, isConnected } from '$lib/stores/assistantStore';
  import { audioProcessingState } from '$lib/stores/audioStore';
  
  import SideNavigation from './SideNavigation.svelte';
  import TopStatusBar from './TopStatusBar.svelte';
  import MainView from './MainView.svelte';
  
  let innerWidth = 0;
  let innerHeight = 0;
  
  // Auto-hide side navigation on small screens
  $: if (innerWidth < 768) {
    sideNavVisible.set(false);
  } else if (innerWidth >= 768) {
    sideNavVisible.set(true);
  }
</script>

<svelte:window bind:innerWidth bind:innerHeight />

<div class="three-column-layout">
  <!-- Side Navigation (Left Column - 10% width on desktop) -->
  {#if $sideNavVisible}
    <aside class="side-navigation" class:hidden={!$sideNavVisible}>
      <SideNavigation />
    </aside>
  {/if}
  
  <!-- Main Content Area -->
  <div class="main-area" class:full-width={!$sideNavVisible}>
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
    height: 100vh;
    overflow: hidden;
    background-color: #f8f9fa;
  }
  
  /* Side Navigation */
  .side-navigation {
    width: 10%;
    min-width: 200px;
    background-color: #2c3e50;
    border-right: 1px solid #34495e;
    transition: transform 0.3s ease;
    z-index: 100;
  }
  
  .side-navigation.hidden {
    transform: translateX(-100%);
    position: absolute;
    height: 100%;
  }
  
  /* Main Content Area */
  .main-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    width: 90%;
    transition: width 0.3s ease;
  }
  
  .main-area.full-width {
    width: 100%;
  }
  
  /* Top Status Bar */
  .top-status-bar {
    height: 7vh;
    min-height: 60px;
    background-color: #ffffff;
    border-bottom: 1px solid #dee2e6;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    z-index: 90;
  }
  
  /* Main View */
  .main-view {
    flex: 1;
    height: 93vh;
    overflow-y: auto;
    padding: 1rem;
  }
  
  /* Mobile Responsiveness */
  @media (max-width: 768px) {
    .side-navigation {
      position: fixed;
      top: 0;
      left: 0;
      height: 100vh;
      width: 280px;
      min-width: 280px;
      z-index: 1000;
      transform: translateX(-100%);
    }
    
    .side-navigation:not(.hidden) {
      transform: translateX(0);
    }
    
    .main-area {
      width: 100%;
    }
    
    .main-view {
      padding: 0.5rem;
    }
    
    .top-status-bar {
      min-height: 50px;
    }
  }
  
  /* Small screens */
  @media (max-width: 480px) {
    .main-view {
      padding: 0.25rem;
    }
    
    .top-status-bar {
      height: 8vh;
    }
    
    .main-view {
      height: 92vh;
    }
  }
  
  /* Kiosk mode optimizations */
  @media (orientation: landscape) and (max-height: 600px) {
    .top-status-bar {
      height: 10vh;
      min-height: 50px;
    }
    
    .main-view {
      height: 90vh;
    }
  }
</style>

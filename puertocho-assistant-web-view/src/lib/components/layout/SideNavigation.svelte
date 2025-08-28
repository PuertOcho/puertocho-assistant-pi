<script lang="ts">
  import { activeView, navigationItems, navigationStore } from '$lib/stores/navigationStore';
  
  function handleNavigation(viewId: string) {
    navigationStore.setActiveView(viewId as any);
  }
</script>

<nav class="side-navigation-content">
  <!-- Navigation Items -->
  <div class="nav-items">
    {#each navigationItems as item}
      <button 
        class="nav-item" 
        class:active={$activeView === item.id}
        on:click={() => handleNavigation(item.id)}
        title={item.description}
      >
        <span class="nav-icon">
          {#if item.icon !== '' && item.icon !== null}
            <img src="/sideIcons/{item.icon}.png" alt={item.label} class="icon-image" />
          {:else}
            <span class="nav-label">{item.label}</span>
          {/if}
        </span>
      </button>
    {/each}
  </div>
  
  <!-- Footer -->
  <div class="nav-footer">
    <div class="version-info">
      <small>v1.0.0</small>
    </div>
  </div>
</nav>

<style>
  .side-navigation-content {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
    color: #ecf0f1;
    position: relative;
    overflow-x: hidden;
    overflow-y: auto;
  }
  
  /* Navigation Items */
  .nav-items {
    flex: 1;
    padding: 1rem 0;
    overflow-x: hidden;
    overflow-y: auto;
    align-items: center;
  }
  
  .nav-item {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0.875rem 1rem;
    background: none;
    border: none;
    color: #bdc3c7;
    font-size: 0.9rem;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: center;
    position: relative;
  }
  
  .nav-item:hover {
    background-color: rgba(52, 73, 94, 0.5);
    color: #ecf0f1;
    transform: translateX(2px);
  }
  
  .nav-item.active {
    background: linear-gradient(90deg, rgba(52, 152, 219, 0.2) 0%, transparent 100%);
    color: #3498db;
    border-right: 3px solid #3498db;
  }
  
  .nav-item.active::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: linear-gradient(180deg, #3498db, #2980b9);
  }
  
  .nav-icon {
    font-size: 1.2rem;
    width: 50px;
    height: 50px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    flex-shrink: 0;
  }
  
  .icon-image {
    width: 58px;
    height: 58px;
    object-fit: contain;
    filter: brightness(0.8);
    transition: filter 0.2s ease;
    z-index: 500;
  }
  
  /* Ajustes para modo portrait - elementos más pequeños proporcionalmente */
  :global(.portrait-rotated) .nav-icon {
    width: 3.5rem;
    height: 3.5rem;
    font-size: 1rem;
  }
  
  :global(.portrait-rotated) .icon-image {
    width: 4rem;
    height: 4rem;
  }
  
  :global(.portrait-rotated) .nav-item {
    padding: 0.6rem 0.8rem;
    font-size: 0.8rem;
  }
  
  .nav-item:hover .icon-image {
    filter: brightness(1);
  }
  
  .nav-item.active .icon-image {
    filter: brightness(1.2) sepia(1) hue-rotate(180deg) saturate(1.5);
  }
  
  .nav-label {
    flex: 1;
    font-weight: 500;
  }
  
  /* Footer */
  .nav-footer {
    padding: 1rem;
    border-top: 1px solid #445068;
    text-align: center;
  }
  
  .version-info {
    color: #7f8c8d;
    font-size: 0.8rem;
  }
  
  /* Scrollbar Styles */
  .nav-items::-webkit-scrollbar {
    width: 4px;
  }
  
  .nav-items::-webkit-scrollbar-track {
    background: rgba(52, 73, 94, 0.3);
  }
  
  .nav-items::-webkit-scrollbar-thumb {
    background: rgba(189, 195, 199, 0.3);
    border-radius: 2px;
  }
  
  .nav-items::-webkit-scrollbar-thumb:hover {
    background: rgba(189, 195, 199, 0.5);
  }
</style>

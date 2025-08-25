<script lang="ts">
  import { activeView, navigationItems, navigationStore, sideNavVisible } from '$lib/stores/navigationStore';
  
  function handleNavigation(viewId: string) {
    navigationStore.setActiveView(viewId as any);
    // Auto-hide on mobile after selection
    if (window.innerWidth < 768) {
      sideNavVisible.set(false);
    }
  }
</script>

<nav class="side-navigation-content">
  <!-- Header -->
  <div class="nav-header">
    <div class="logo">
      <span class="logo-icon">🤖</span>
      <span class="logo-text">PuertoCho</span>
    </div>
  </div>
  
  <!-- Navigation Items -->
  <div class="nav-items">
    {#each navigationItems as item}
      <button 
        class="nav-item" 
        class:active={$activeView === item.id}
        on:click={() => handleNavigation(item.id)}
        title={item.description}
      >
        <span class="nav-icon">{item.icon}</span>
        <span class="nav-label">{item.label}</span>
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
  }
  
  /* Header */
  .nav-header {
    padding: 1.5rem 1rem;
    border-bottom: 1px solid #445068;
  }
  
  .logo {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  
  .logo-icon {
    font-size: 1.5rem;
    background: linear-gradient(45deg, #3498db, #e74c3c);
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  
  .logo-text {
    font-size: 1.1rem;
    font-weight: 600;
    color: #ecf0f1;
  }
  
  /* Navigation Items */
  .nav-items {
    flex: 1;
    padding: 1rem 0;
    overflow-y: auto;
  }
  
  .nav-item {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.875rem 1rem;
    background: none;
    border: none;
    color: #bdc3c7;
    font-size: 0.9rem;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: left;
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
    width: 1.5rem;
    text-align: center;
    flex-shrink: 0;
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
  
  /* Mobile Adjustments */
  @media (max-width: 768px) {
    .nav-header {
      padding: 1rem;
    }
    
    .nav-item {
      padding: 1rem;
      font-size: 1rem;
    }
    
    .nav-icon {
      font-size: 1.3rem;
    }
  }
  
  /* Touch-friendly sizing for kiosk mode */
  @media (pointer: coarse) {
    .nav-item {
      padding: 1.125rem 1rem;
      min-height: 48px;
    }
  }
</style>

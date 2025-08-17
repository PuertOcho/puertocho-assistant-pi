<script lang="ts">
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let color: string = '#3b82f6';
  
  const sizeMap = {
    sm: '16px',
    md: '24px',
    lg: '32px'
  };
</script>

<div class="loading-spinner" style="width: {sizeMap[size]}; height: {sizeMap[size]};">
  <div class="spinner" style="border-color: {color} transparent {color} transparent;"></div>
</div>

<style>
  .loading-spinner {
    display: inline-block;
  }
  
  .spinner {
    width: 100%;
    height: 100%;
    border: 2px solid;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
</style>

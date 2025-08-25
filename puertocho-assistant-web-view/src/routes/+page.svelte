<script lang="ts">
  import { onMount } from 'svelte';
  import { ThreeColumnLayout } from '$lib/components/layout';
  
  let isPortrait = false;
  
  function checkOrientation() {
    isPortrait = window.innerHeight > window.innerWidth;
  }
  
  onMount(() => {
    checkOrientation();
    window.addEventListener('resize', checkOrientation);
    window.addEventListener('orientationchange', () => {
      // Pequeño delay para asegurar que las dimensiones se hayan actualizado
      setTimeout(checkOrientation, 100);
    });
    
    return () => {
      window.removeEventListener('resize', checkOrientation);
      window.removeEventListener('orientationchange', checkOrientation);
    };
  });
</script>

<div class="app-container" class:portrait-rotated={isPortrait}>
  <ThreeColumnLayout />
</div>

<style>
  :global(body) {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
      Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    background-color: #f8f9fa;
    color: #212529;
  }

  .app-container {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100vh;
    overflow: hidden;
  }
  
  /* Rotación cuando está en portrait */
  .app-container.portrait-rotated {
    transform: rotate(90deg);
    transform-origin: center center;
    width: 100vh;
    height: 100vw;
    position: fixed;
    top: 50%;
    left: 50%;
    margin-top: calc(-100vw / 2);
    margin-left: calc(-100vh / 2);
    /* Forzar que el contenido se escale apropiadamente */
    box-sizing: border-box;
  }
  
  /* Asegurar que los elementos internos mantengan su proporción */
  .portrait-rotated :global(*) {
    box-sizing: border-box;
  }
  
  /* Asegurar que el body no tenga scroll cuando esté rotado */
  :global(body:has(.portrait-rotated)) {
    overflow: hidden !important;
    position: fixed;
    width: 100vw;
    height: 100vh;
  }
  
  /* Corrección adicional para webkit browsers */
  :global(html:has(.portrait-rotated)) {
    overflow: hidden !important;
    width: 100%;
    height: 100%;
  }
</style>

<script lang="ts">
  import { ThreeColumnLayout } from '$lib/components/layout';
</script>

<div class="app-container">
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
</style>

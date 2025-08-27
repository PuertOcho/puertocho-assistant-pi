<script lang="ts">
  export let icon: string;
  export let iconType: 'emoji' | 'image';
  export let alt: string = '';
  export let size: string = '2.3rem';
  
  // Get the appropriate icon source
  $: iconSrc = iconType === 'image' ? `/mcpIcons/${icon}` : null;
</script>

{#if iconType === 'emoji'}
  <span class="emoji-icon" style="font-size: {size};">
    {icon}
  </span>
{:else if iconType === 'image'}
  <img 
    src={iconSrc} 
    alt={alt} 
    class="image-icon"
    style="width: {size}; height: {size};"
    on:error={(e) => {
      console.error(`Failed to load icon: ${iconSrc}`);
      e.currentTarget.style.display = 'none';
    }}
  />
{/if}

<style>
  .emoji-icon {
    display: inline-block;
    line-height: 1;
  }
  
  .image-icon {
    display: inline-block;
    object-fit: contain;
    filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.1));
    transition: filter 0.2s ease;
    margin-top: -8px;
  }
  
  .image-icon:hover {
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
  }
</style>

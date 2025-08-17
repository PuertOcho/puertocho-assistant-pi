<script lang="ts">
  export let audioUrl: string = '';
  export let filename: string = '';
  export let duration: number = 0;
  export let autoplay: boolean = false;
  export let showControls: boolean = true;
  
  let audioElement: HTMLAudioElement;
  let isPlaying = false;
  let currentTime = 0;
  let isLoaded = false;
  let volume = 1;
  let isMuted = false;
  
  // Reactive statements
  $: if (audioElement && audioUrl) {
    audioElement.src = audioUrl;
  }
  
  $: if (audioElement && autoplay && audioUrl && isLoaded) {
    play();
  }
  
  function formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }
  
  function play() {
    if (audioElement && audioUrl) {
      audioElement.play().catch(console.error);
    }
  }
  
  function pause() {
    if (audioElement) {
      audioElement.pause();
    }
  }
  
  function togglePlay() {
    if (isPlaying) {
      pause();
    } else {
      play();
    }
  }
  
  function seek(event: Event) {
    const target = event.target as HTMLInputElement;
    const seekTime = (parseFloat(target.value) / 100) * duration;
    if (audioElement) {
      audioElement.currentTime = seekTime;
    }
  }
  
  function setVolume(event: Event) {
    const target = event.target as HTMLInputElement;
    volume = parseFloat(target.value) / 100;
    if (audioElement) {
      audioElement.volume = volume;
    }
  }
  
  function toggleMute() {
    if (audioElement) {
      isMuted = !isMuted;
      audioElement.muted = isMuted;
    }
  }
  
  function onLoadedData() {
    isLoaded = true;
  }
  
  function onPlay() {
    isPlaying = true;
  }
  
  function onPause() {
    isPlaying = false;
  }
  
  function onTimeUpdate() {
    if (audioElement) {
      currentTime = audioElement.currentTime;
    }
  }
  
  function onEnded() {
    isPlaying = false;
    currentTime = 0;
  }
  
  function downloadAudio() {
    if (audioUrl) {
      const a = document.createElement('a');
      a.href = audioUrl;
      a.download = filename || 'audio.wav';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  }
</script>

<!-- Hidden audio element -->
<audio
  bind:this={audioElement}
  on:loadeddata={onLoadedData}
  on:play={onPlay}
  on:pause={onPause}
  on:timeupdate={onTimeUpdate}
  on:ended={onEnded}
  preload="metadata"
>
  Your browser does not support the audio element.
</audio>

{#if audioUrl}
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 p-4">
    <!-- File info -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <div class="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
          <span class="text-xl">🎵</span>
        </div>
        <div>
          <div class="font-medium text-gray-900 dark:text-white truncate max-w-48">
            {filename || 'Audio File'}
          </div>
          <div class="text-sm text-gray-500 dark:text-gray-400">
            {formatTime(duration)}
          </div>
        </div>
      </div>
      
      <button
        on:click={downloadAudio}
        class="p-2 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 
               hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
        title="Download audio"
      >
        💾
      </button>
    </div>
    
    {#if showControls}
      <!-- Progress bar -->
      <div class="mb-4">
        <div class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1">
          <span>{formatTime(currentTime)}</span>
          <span>/</span>
          <span>{formatTime(duration)}</span>
        </div>
        <input
          type="range"
          min="0"
          max="100"
          value={duration > 0 ? (currentTime / duration) * 100 : 0}
          on:input={seek}
          class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer 
                 slider-thumb:appearance-none slider-thumb:w-4 slider-thumb:h-4 slider-thumb:bg-blue-500 
                 slider-thumb:rounded-full slider-thumb:cursor-pointer"
        />
      </div>
      
      <!-- Controls -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <!-- Play/Pause button -->
          <button
            on:click={togglePlay}
            disabled={!isLoaded}
            class="w-12 h-12 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 dark:disabled:bg-gray-600 
                   text-white rounded-full flex items-center justify-center transition-colors"
            title={isPlaying ? 'Pause' : 'Play'}
          >
            {#if isPlaying}
              <span class="text-lg">⏸️</span>
            {:else}
              <span class="text-lg">▶️</span>
            {/if}
          </button>
          
          <!-- Loading indicator -->
          {#if !isLoaded && audioUrl}
            <div class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
              <div class="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              Loading...
            </div>
          {/if}
        </div>
        
        <!-- Volume controls -->
        <div class="flex items-center gap-2">
          <button
            on:click={toggleMute}
            class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 
                   transition-colors"
            title={isMuted ? 'Unmute' : 'Mute'}
          >
            {#if isMuted}
              <span>🔇</span>
            {:else if volume > 0.5}
              <span>🔊</span>
            {:else if volume > 0}
              <span>🔉</span>
            {:else}
              <span>🔈</span>
            {/if}
          </button>
          
          <input
            type="range"
            min="0"
            max="100"
            value={volume * 100}
            on:input={setVolume}
            class="w-20 h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
            title="Volume"
          />
        </div>
      </div>
    {:else}
      <!-- Simple play button -->
      <div class="flex items-center justify-center">
        <button
          on:click={togglePlay}
          disabled={!isLoaded}
          class="w-16 h-16 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 dark:disabled:bg-gray-600 
                 text-white rounded-full flex items-center justify-center transition-colors"
          title={isPlaying ? 'Pause' : 'Play'}
        >
          {#if isPlaying}
            <span class="text-2xl">⏸️</span>
          {:else}
            <span class="text-2xl">▶️</span>
          {/if}
        </button>
      </div>
    {/if}
  </div>
{:else}
  <div class="bg-gray-50 dark:bg-gray-800 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 p-8 text-center">
    <div class="text-gray-400 dark:text-gray-500 text-4xl mb-2">🎵</div>
    <div class="text-gray-500 dark:text-gray-400 text-sm">No audio file selected</div>
  </div>
{/if}

<style>
  /* Custom slider styles */
  input[type="range"] {
    -webkit-appearance: none;
    appearance: none;
  }
  
  input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: #3b82f6;
    cursor: pointer;
  }
  
  input[type="range"]::-moz-range-thumb {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: #3b82f6;
    cursor: pointer;
    border: none;
  }
</style>

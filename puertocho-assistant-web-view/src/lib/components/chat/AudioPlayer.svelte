<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  
  export let audioUrl: string;
  export let filename: string = '';
  export let isPlaying: boolean = false;
  
  const dispatch = createEventDispatcher();
  
  let audioElement: HTMLAudioElement;
  let duration: number = 0;
  let currentTime: number = 0;
  let loading: boolean = false;
  let error: boolean = false;
  
  function formatTime(seconds: number): string {
    if (isNaN(seconds) || !isFinite(seconds)) return '00:00';
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  }
  
  function formatFileSize(url: string): string {
    // This would ideally come from the backend, but for now we'll show the filename
    if (filename) {
      return filename.replace(/\.wav$|\.mp3$|\.ogg$/i, '');
    }
    return 'Audio';
  }
  
  async function togglePlayPause() {
    if (!audioElement) return;
    
    try {
      loading = true;
      error = false;
      
      if (isPlaying) {
        audioElement.pause();
        dispatch('pause');
      } else {
        // Pause any other audio that might be playing
        document.querySelectorAll('audio').forEach(audio => {
          if (audio !== audioElement) audio.pause();
        });
        
        await audioElement.play();
        dispatch('play');
      }
    } catch (err) {
      console.error('Error playing audio:', err);
      error = true;
      dispatch('error', err);
    } finally {
      loading = false;
    }
  }
  
  function handleTimeUpdate() {
    if (audioElement) {
      currentTime = audioElement.currentTime;
    }
  }
  
  function handleLoadedMetadata() {
    if (audioElement) {
      duration = audioElement.duration;
    }
  }
  
  function handleEnded() {
    dispatch('pause');
  }
  
  function handleError(event: Event) {
    console.error('Audio loading error:', event);
    error = true;
    loading = false;
  }
  
  function handleLoadStart() {
    loading = true;
    error = false;
  }
  
  function handleCanPlay() {
    loading = false;
  }
  
  function seekTo(event: MouseEvent) {
    if (!audioElement || !duration) return;
    
    const progressBar = event.currentTarget as HTMLElement;
    const rect = progressBar.getBoundingClientRect();
    const percent = (event.clientX - rect.left) / rect.width;
    const seekTime = duration * percent;
    
    audioElement.currentTime = seekTime;
  }
  
  $: progressPercent = duration ? (currentTime / duration) * 100 : 0;
</script>

<div class="audio-player">
  <audio
    bind:this={audioElement}
    src={audioUrl}
    preload="metadata"
    on:timeupdate={handleTimeUpdate}
    on:loadedmetadata={handleLoadedMetadata}
    on:ended={handleEnded}
    on:error={handleError}
    on:loadstart={handleLoadStart}
    on:canplay={handleCanPlay}
  ></audio>
  
  <div class="player-controls">
    <button 
      class="play-button {isPlaying ? 'playing' : ''}" 
      on:click={togglePlayPause}
      disabled={loading || error}
      title={isPlaying ? 'Pausar' : 'Reproducir'}
    >
      {#if loading}
        <div class="loading-spinner-small"></div>
      {:else if error}
        <span class="error-icon">⚠️</span>
      {:else if isPlaying}
        <span class="pause-icon">⏸️</span>
      {:else}
        <span class="play-icon">▶️</span>
      {/if}
    </button>
    
    <div class="player-info">
      <div class="audio-title">
        {formatFileSize(audioUrl)}
      </div>
      
      <div class="progress-container">
        <!-- svelte-ignore a11y-click-events-have-key-events -->
        <!-- svelte-ignore a11y-no-static-element-interactions -->
        <div class="progress-bar" on:click={seekTo}>
          <div class="progress-fill" style="width: {progressPercent}%"></div>
        </div>
        
        <div class="time-display">
          <span class="current-time">{formatTime(currentTime)}</span>
          <span class="duration">{formatTime(duration)}</span>
        </div>
      </div>
    </div>
  </div>
  
  {#if error}
    <div class="error-message">
      Error al cargar el audio
    </div>
  {/if}
</div>

<style>
  .audio-player {
    background: white;
    border: 1px solid #e1e5e9;
    border-radius: 8px;
    padding: 0.75rem;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }
  
  .player-controls {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  
  .play-button {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: none;
    background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
    color: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    transition: all 0.2s ease;
    flex-shrink: 0;
  }
  
  .play-button:hover:not(:disabled) {
    transform: scale(1.05);
    box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
  }
  
  .play-button:active:not(:disabled) {
    transform: scale(0.98);
  }
  
  .play-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
  
  .play-button.playing {
    background: linear-gradient(135deg, #28a745 0%, #1e7e34 100%);
  }
  
  .loading-spinner-small {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top: 2px solid white;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  .error-icon {
    font-size: 1rem;
    filter: grayscale(1);
  }
  
  .player-info {
    flex: 1;
    min-width: 0;
  }
  
  .audio-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: #333;
    margin-bottom: 0.5rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .progress-container {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .progress-bar {
    height: 4px;
    background: #e1e5e9;
    border-radius: 2px;
    cursor: pointer;
    position: relative;
    overflow: hidden;
  }
  
  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #007bff 0%, #0056b3 100%);
    border-radius: 2px;
    transition: width 0.1s ease;
  }
  
  .time-display {
    display: flex;
    justify-content: space-between;
    font-size: 0.75rem;
    color: #6c757d;
    font-variant-numeric: tabular-nums;
  }
  
  .error-message {
    margin-top: 0.5rem;
    color: #dc3545;
    font-size: 0.8rem;
    text-align: center;
    padding: 0.25rem;
    background: rgba(220, 53, 69, 0.1);
    border-radius: 4px;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  /* Responsive adjustments */
  @media (max-width: 480px) {
    .audio-player {
      padding: 0.5rem;
    }
    
    .play-button {
      width: 36px;
      height: 36px;
      font-size: 1rem;
    }
    
    .audio-title {
      font-size: 0.8rem;
    }
    
    .time-display {
      font-size: 0.7rem;
    }
  }
</style>
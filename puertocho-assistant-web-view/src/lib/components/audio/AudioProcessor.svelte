<script lang="ts">
  import { audioProcessingState } from '$lib/stores/assistantStore';
  
  $: status = $audioProcessingState.status;
  $: currentAudio = $audioProcessingState.current_audio;
  $: queueLength = $audioProcessingState.queue_length;
  $: totalProcessed = $audioProcessingState.total_processed;

  function getStatusIcon(status: string): string {
    switch (status) {
      case 'idle': return '⏸️';
      case 'receiving': return '📥';
      case 'processing': return '⚡';
      case 'completed': return '✅';
      case 'error': return '❌';
      default: return '❓';
    }
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'idle': return 'text-gray-500';
      case 'receiving': return 'text-blue-500';
      case 'processing': return 'text-yellow-500';
      case 'completed': return 'text-green-500';
      case 'error': return 'text-red-500';
      default: return 'text-gray-500';
    }
  }

  function formatDuration(seconds: number): string {
    if (seconds < 1) return `${Math.round(seconds * 1000)}ms`;
    return `${seconds.toFixed(2)}s`;
  }

  function formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
</script>

<div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 border border-gray-200 dark:border-gray-700">
  <div class="flex items-center justify-between mb-4">
    <h3 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
      🎙️ Audio Processor
      <span class="text-sm {getStatusColor(status)}">
        {getStatusIcon(status)} {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    </h3>
    
    {#if queueLength > 0}
      <div class="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded-full text-xs font-medium">
        Queue: {queueLength}
      </div>
    {/if}
  </div>

  <!-- Current audio being processed -->
  {#if currentAudio}
    <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 mb-4">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Current Audio:</span>
        <span class="text-xs text-gray-500 dark:text-gray-400">
          {new Date(currentAudio.timestamp).toLocaleTimeString()}
        </span>
      </div>
      
      <div class="space-y-2">
        <div class="flex justify-between items-center">
          <span class="text-sm text-gray-600 dark:text-gray-400">File:</span>
          <span class="text-sm font-mono text-gray-900 dark:text-white truncate max-w-48">
            {currentAudio.filename}
          </span>
        </div>
        
        <div class="flex justify-between items-center">
          <span class="text-sm text-gray-600 dark:text-gray-400">Duration:</span>
          <span class="text-sm text-gray-900 dark:text-white">
            {formatDuration(currentAudio.duration)}
          </span>
        </div>
        
        <div class="flex justify-between items-center">
          <span class="text-sm text-gray-600 dark:text-gray-400">Size:</span>
          <span class="text-sm text-gray-900 dark:text-white">
            {formatFileSize(currentAudio.size)}
          </span>
        </div>
        
        {#if currentAudio.quality_score !== undefined}
          <div class="flex justify-between items-center">
            <span class="text-sm text-gray-600 dark:text-gray-400">Quality:</span>
            <div class="flex items-center gap-2">
              <div class="w-20 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                <div 
                  class="h-2 rounded-full transition-all duration-300"
                  class:bg-red-500={currentAudio.quality_score < 50}
                  class:bg-yellow-500={currentAudio.quality_score >= 50 && currentAudio.quality_score < 80}
                  class:bg-green-500={currentAudio.quality_score >= 80}
                  style="width: {currentAudio.quality_score}%"
                ></div>
              </div>
              <span class="text-sm text-gray-900 dark:text-white">
                {currentAudio.quality_score}%
              </span>
            </div>
          </div>
        {/if}
        
        <!-- Processing status indicator -->
        {#if status === 'processing'}
          <div class="mt-2">
            <div class="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
              <div class="h-2 bg-blue-500 rounded-full animate-pulse w-3/4"></div>
            </div>
            <span class="text-xs text-gray-500 dark:text-gray-400 mt-1 block">Processing audio...</span>
          </div>
        {/if}
      </div>
    </div>
  {/if}

  <!-- Statistics -->
  <div class="grid grid-cols-2 gap-4">
    <div class="text-center">
      <div class="text-2xl font-bold text-gray-900 dark:text-white">{totalProcessed}</div>
      <div class="text-sm text-gray-500 dark:text-gray-400">Total Processed</div>
    </div>
    
    <div class="text-center">
      <div class="text-2xl font-bold text-gray-900 dark:text-white">{queueLength}</div>
      <div class="text-sm text-gray-500 dark:text-gray-400">In Queue</div>
    </div>
  </div>

  <!-- Status indicator -->
  {#if status === 'idle'}
    <div class="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
      Waiting for audio input...
    </div>
  {:else if status === 'error'}
    <div class="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
      <div class="text-sm text-red-700 dark:text-red-300 text-center">
        ❌ Audio processing error occurred
      </div>
    </div>
  {/if}
</div>

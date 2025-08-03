<script lang="ts">
  import { audioHistory } from '$lib/stores/assistantStore';
  
  $: files = $audioHistory;

  function formatDuration(seconds: number): string {
    if (seconds < 1) return `${Math.round(seconds * 1000)}ms`;
    return `${seconds.toFixed(2)}s`;
  }

  function formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function getQualityColor(score: number | undefined): string {
    if (score === undefined) return 'text-gray-500';
    if (score < 50) return 'text-red-500';
    if (score < 80) return 'text-yellow-500';
    return 'text-green-500';
  }

  function getStatusIcon(status: string): string {
    switch (status) {
      case 'processing': return '⚡';
      case 'completed': return '✅';
      case 'error': return '❌';
      default: return '❓';
    }
  }

  function formatTimestamp(timestamp: string): string {
    return new Date(timestamp).toLocaleString();
  }

  function playAudio(url?: string) {
    if (url) {
      const audio = new Audio(url);
      audio.play().catch(console.error);
    }
  }

  function downloadFile(filename: string, url?: string) {
    if (url) {
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  }
</script>

<div class="bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700">
  <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
    <h3 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
      📝 Audio History
      {#if files.length > 0}
        <span class="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded-full text-xs font-medium">
          {files.length} files
        </span>
      {/if}
    </h3>
  </div>

  <div class="max-h-96 overflow-y-auto">
    {#if files.length === 0}
      <div class="p-6 text-center text-gray-500 dark:text-gray-400">
        <div class="text-4xl mb-2">🎙️</div>
        <div class="text-sm">No audio files processed yet</div>
        <div class="text-xs mt-1">Audio files will appear here after processing</div>
      </div>
    {:else}
      <div class="divide-y divide-gray-200 dark:divide-gray-700">
        {#each files as file (file.id)}
          <div class="p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            <div class="flex items-start justify-between">
              <!-- File info -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <span class="text-lg">
                    {getStatusIcon(file.status)}
                  </span>
                  <span class="font-mono text-sm text-gray-900 dark:text-white truncate">
                    {file.filename}
                  </span>
                </div>
                
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-2">
                  {formatTimestamp(file.timestamp)}
                </div>
                
                <div class="grid grid-cols-2 gap-4 text-sm">
                  <div class="flex justify-between">
                    <span class="text-gray-600 dark:text-gray-400">Duration:</span>
                    <span class="text-gray-900 dark:text-white">
                      {formatDuration(file.duration)}
                    </span>
                  </div>
                  
                  <div class="flex justify-between">
                    <span class="text-gray-600 dark:text-gray-400">Size:</span>
                    <span class="text-gray-900 dark:text-white">
                      {formatFileSize(file.size)}
                    </span>
                  </div>
                </div>
                
                {#if file.quality_score !== undefined}
                  <div class="mt-2 flex items-center gap-2">
                    <span class="text-xs text-gray-600 dark:text-gray-400">Quality:</span>
                    <div class="flex-1 bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
                      <div 
                        class="h-1.5 rounded-full transition-all duration-300"
                        class:bg-red-500={file.quality_score < 50}
                        class:bg-yellow-500={file.quality_score >= 50 && file.quality_score < 80}
                        class:bg-green-500={file.quality_score >= 80}
                        style="width: {file.quality_score}%"
                      ></div>
                    </div>
                    <span class="text-xs {getQualityColor(file.quality_score)}">
                      {file.quality_score}%
                    </span>
                  </div>
                {/if}
              </div>
              
              <!-- Actions -->
              <div class="flex items-center gap-2 ml-4">
                {#if file.url && file.status === 'completed'}
                  <button
                    on:click={() => playAudio(file.url)}
                    class="p-2 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 
                           hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                    title="Play audio"
                  >
                    ▶️
                  </button>
                  
                  <button
                    on:click={() => downloadFile(file.filename, file.url)}
                    class="p-2 text-gray-500 hover:text-green-600 dark:text-gray-400 dark:hover:text-green-400 
                           hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition-colors"
                    title="Download file"
                  >
                    💾
                  </button>
                {/if}
                
                {#if file.status === 'processing'}
                  <div class="flex items-center gap-2">
                    <div class="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    <span class="text-xs text-blue-600 dark:text-blue-400">Processing...</span>
                  </div>
                {:else if file.status === 'error'}
                  <div class="text-xs text-red-600 dark:text-red-400 flex items-center gap-1">
                    ⚠️ Error
                  </div>
                {/if}
              </div>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
  
  {#if files.length > 0}
    <div class="px-4 py-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
      <div class="text-xs text-gray-500 dark:text-gray-400 text-center">
        Showing last {files.length} audio files
      </div>
    </div>
  {/if}
</div>

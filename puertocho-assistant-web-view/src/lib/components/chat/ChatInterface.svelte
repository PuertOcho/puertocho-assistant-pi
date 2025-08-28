<script lang="ts">
  import { onMount } from 'svelte';
  import { chatStore, type ChatMessage, setAudioPlaying } from '$lib/stores/chatStore';
  import AudioPlayer from './AudioPlayer.svelte';
  
  export let maxHeight: string = '400px';
  
  let chatContainer: HTMLElement;
  
  $: messages = $chatStore.messages;
  
  // Auto-scroll to bottom when new messages arrive
  function scrollToBottom() {
    if (chatContainer) {
      setTimeout(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }, 100);
    }
  }
  
  $: if (messages.length > 0) {
    scrollToBottom();
  }
  
  function formatTime(date: Date): string {
    return date.toLocaleTimeString('es-ES', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  }
  
  function handlePlayAudio(message: ChatMessage) {
    if (message.audioUrl) {
      setAudioPlaying(message.isPlaying ? null : message.id);
    }
  }
</script>

<div class="chat-interface">
  <div class="chat-header">
    <h3>Conversación</h3>
    <div class="message-count">
      {messages.length} mensaje{messages.length !== 1 ? 's' : ''}
    </div>
  </div>
  
  <div 
    class="chat-messages" 
    bind:this={chatContainer}
    style="max-height: {maxHeight};"
  >
    {#if messages.length === 0}
      <div class="empty-state">
        <div class="empty-icon">🎤</div>
        <p>No hay conversaciones aún</p>
        <small>Las interacciones de voz aparecerán aquí</small>
      </div>
    {/if}
    
    {#each messages as message (message.id)}
      <div class="message {message.type}">
        <div class="message-header">
          <div class="message-sender">
            {#if message.type === 'user'}
              <span class="user-icon">👤</span>
              <strong>Tú</strong>
            {:else}
              <span class="assistant-icon">🤖</span>
              <strong>Asistente</strong>
            {/if}
          </div>
          <div class="message-time">
            {formatTime(message.timestamp)}
          </div>
        </div>
        
        <div class="message-content">
          <!-- Audio section -->
          {#if message.audioUrl}
            <div class="audio-section">
              <AudioPlayer 
                audioUrl={message.audioUrl}
                filename={message.audioFilename}
                isPlaying={message.isPlaying || false}
                on:play={() => handlePlayAudio(message)}
                on:pause={() => setAudioPlaying(null)}
              />
            </div>
          {/if}
          
          <!-- Text content -->
          {#if message.type === 'user' && message.transcription}
            <div class="transcription">
              <div class="text-label">Transcripción:</div>
              <p>{message.transcription}</p>
            </div>
          {:else if message.type === 'user' && message.status === 'processing'}
            <div class="processing">
              <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span>Procesando audio...</span>
            </div>
          {/if}
          
          {#if message.type === 'assistant' && message.response}
            <div class="response">
              <div class="text-label">Respuesta:</div>
              <p>{message.response}</p>
            </div>
          {/if}
        </div>
        
        {#if message.status === 'error'}
          <div class="error-indicator">
            ⚠️ Error al procesar
          </div>
        {/if}
      </div>
    {/each}
  </div>
  
  {#if $chatStore.isLoading}
    <div class="chat-loading">
      <div class="loading-spinner"></div>
      <span>Procesando...</span>
    </div>
  {/if}
</div>

<style>
  .chat-interface {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: white;
    border-radius: 8px;
    overflow: hidden;
  }
  
  .chat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-bottom: 1px solid #dee2e6;
  }
  
  .chat-header h3 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
  }
  
  .message-count {
    font-size: 0.85rem;
    opacity: 0.9;
  }
  
  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #6c757d;
    text-align: center;
    padding: 2rem;
  }
  
  .empty-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.5;
  }
  
  .empty-state p {
    margin: 0 0 0.5rem 0;
    font-size: 1.1rem;
  }
  
  .empty-state small {
    opacity: 0.7;
  }
  
  .message {
    display: flex;
    flex-direction: column;
    padding: 1rem;
    border-radius: 12px;
    max-width: 85%;
    word-wrap: break-word;
  }
  
  .message.user {
    align-self: flex-end;
    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
    border: 1px solid #2196f3;
  }
  
  .message.assistant {
    align-self: flex-start;
    background: linear-gradient(135deg, #f1f8e9 0%, #dcedc8 100%);
    border: 1px solid #4caf50;
  }
  
  .message-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
    font-size: 0.85rem;
  }
  
  .message-sender {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
  }
  
  .user-icon, .assistant-icon {
    font-size: 1.2rem;
  }
  
  .message-time {
    opacity: 0.7;
    font-size: 0.75rem;
  }
  
  .message-content {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .audio-section {
    background: rgba(255, 255, 255, 0.8);
    padding: 0.75rem;
    border-radius: 8px;
    border: 1px solid rgba(0, 0, 0, 0.1);
  }
  
  .text-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: #495057;
    margin-bottom: 0.25rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  .transcription p, .response p {
    margin: 0;
    line-height: 1.4;
    font-size: 0.95rem;
  }
  
  .processing {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #6c757d;
    font-style: italic;
  }
  
  .loading-dots {
    display: flex;
    gap: 2px;
  }
  
  .loading-dots span {
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: #6c757d;
    animation: loading-bounce 1.4s infinite ease-in-out;
  }
  
  .loading-dots span:nth-child(1) { animation-delay: -0.32s; }
  .loading-dots span:nth-child(2) { animation-delay: -0.16s; }
  
  @keyframes loading-bounce {
    0%, 80%, 100% { transform: scale(0); opacity: 0.5; }
    40% { transform: scale(1); opacity: 1; }
  }
  
  .error-indicator {
    color: #dc3545;
    font-size: 0.8rem;
    padding: 0.25rem 0.5rem;
    background: rgba(220, 53, 69, 0.1);
    border-radius: 4px;
    margin-top: 0.5rem;
  }
  
  .chat-loading {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 1rem;
    background: #f8f9fa;
    border-top: 1px solid #dee2e6;
    color: #6c757d;
  }
  
  .loading-spinner {
    width: 16px;
    height: 16px;
    border: 2px solid #dee2e6;
    border-top: 2px solid #6c757d;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  /* Responsive adjustments */
  @media (max-width: 768px) {
    .message {
      max-width: 95%;
      padding: 0.75rem;
    }
    
    .chat-messages {
      padding: 0.75rem;
    }
  }
</style>
/**
 * Application Configuration
 * Centralized configuration management for scalability
 */

export interface AppConfig {
  api: {
    baseUrl: string;
    timeout: number;
    retryAttempts: number;
  };
  websocket: {
    url: string;
    reconnectInterval: number;
    maxReconnectAttempts: number;
    heartbeatInterval: number;
  };
  audio: {
    maxHistoryItems: number;
    syncInterval: number;
    supportedFormats: string[];
    maxFileSize: number; // bytes
  };
  ui: {
    theme: 'light' | 'dark' | 'auto';
    language: string;
    updateInterval: number;
    animationDuration: number;
  };
  features: {
    audioVisualization: boolean;
    realTimeUpdates: boolean;
    offlineMode: boolean;
    debugMode: boolean;
  };
}

// Default configuration
const defaultConfig: AppConfig = {
  api: {
    baseUrl: 'http://localhost:8000',
    timeout: 10000, // 10 seconds
    retryAttempts: 3
  },
  websocket: {
    url: 'ws://localhost:8000/ws',
    reconnectInterval: 3000, // 3 seconds
    maxReconnectAttempts: 10,
    heartbeatInterval: 30000 // 30 seconds
  },
  audio: {
    maxHistoryItems: 100,
    syncInterval: 30000, // 30 seconds
    supportedFormats: ['audio/wav', 'audio/mp3', 'audio/ogg'],
    maxFileSize: 50 * 1024 * 1024 // 50 MB
  },
  ui: {
    theme: 'auto',
    language: 'es',
    updateInterval: 1000, // 1 second
    animationDuration: 300 // 300ms
  },
  features: {
    audioVisualization: true,
    realTimeUpdates: true,
    offlineMode: false,
    debugMode: false
  }
};

// Environment-based configuration overrides
function getEnvironmentConfig(): Partial<AppConfig> {
  if (typeof window === 'undefined') return {};

  const config: Partial<AppConfig> = {};

  // Check for environment variables (if available)
  const env = (globalThis as any).process?.env || {};

  if (env.VITE_API_BASE_URL) {
    config.api = { ...defaultConfig.api, baseUrl: env.VITE_API_BASE_URL };
  }

  if (env.VITE_WS_URL) {
    config.websocket = { ...defaultConfig.websocket, url: env.VITE_WS_URL };
  }

  if (env.VITE_DEBUG_MODE === 'true') {
    config.features = { ...defaultConfig.features, debugMode: true };
  }

  // Check URL parameters for development overrides
  const urlParams = new URLSearchParams(window.location.search);
  
  if (urlParams.get('debug') === 'true') {
    config.features = { ...defaultConfig.features, debugMode: true };
  }

  if (urlParams.get('theme')) {
    const theme = urlParams.get('theme') as 'light' | 'dark' | 'auto';
    if (['light', 'dark', 'auto'].includes(theme)) {
      config.ui = { ...defaultConfig.ui, theme };
    }
  }

  return config;
}

// Merge configurations
function createConfig(): AppConfig {
  const envConfig = getEnvironmentConfig();
  return {
    api: { ...defaultConfig.api, ...envConfig.api },
    websocket: { ...defaultConfig.websocket, ...envConfig.websocket },
    audio: { ...defaultConfig.audio, ...envConfig.audio },
    ui: { ...defaultConfig.ui, ...envConfig.ui },
    features: { ...defaultConfig.features, ...envConfig.features }
  };
}

// Export the final configuration
export const config = createConfig();

// Configuration utilities
export const configUtils = {
  /**
   * Get a configuration value by path
   */
  get<T>(path: string): T | undefined {
    return path.split('.').reduce((obj: any, key) => obj?.[key], config);
  },

  /**
   * Check if a feature is enabled
   */
  isFeatureEnabled(feature: keyof AppConfig['features']): boolean {
    return config.features[feature];
  },

  /**
   * Get API URL with path
   */
  getApiUrl(path: string): string {
    return `${config.api.baseUrl}${path.startsWith('/') ? path : `/${path}`}`;
  },

  /**
   * Get WebSocket URL
   */
  getWebSocketUrl(): string {
    return config.websocket.url;
  },

  /**
   * Validate file format
   */
  isValidAudioFormat(mimeType: string): boolean {
    return config.audio.supportedFormats.includes(mimeType);
  },

  /**
   * Check file size limit
   */
  isValidFileSize(size: number): boolean {
    return size <= config.audio.maxFileSize;
  },

  /**
   * Development/debug helpers
   */
  isDevelopment(): boolean {
    return config.features.debugMode || (typeof window !== 'undefined' && window.location.hostname === 'localhost');
  },

  /**
   * Log configuration (for debugging)
   */
  logConfig(): void {
    if (this.isDevelopment()) {
      console.group('🔧 App Configuration');
      console.table(config);
      console.groupEnd();
    }
  }
};

// Initialize configuration logging in development
if (configUtils.isDevelopment()) {
  configUtils.logConfig();
}

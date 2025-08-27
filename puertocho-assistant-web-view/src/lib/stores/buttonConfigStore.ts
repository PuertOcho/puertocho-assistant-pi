import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

// Types
export interface ButtonAction {
  id: number;
  label: string;
  icon: string;
  iconType: 'emoji' | 'image';
  action: string;
  category?: string;
}

export interface ButtonConfig {
  matrixConfig: {
    rows: number;
    cols: number;
  };
  buttonActions: ButtonAction[];
}

// Default fallback configuration
const defaultConfig: ButtonConfig = {
  matrixConfig: { rows: 5, cols: 4 },
  buttonActions: [
    { id: 1, label: 'Sin configurar', icon: '⚙️', iconType: 'emoji', action: 'no_config' }
  ]
};

// Create stores
export const buttonConfig = writable<ButtonConfig>(defaultConfig);
export const isLoading = writable<boolean>(true);
export const lastUpdated = writable<Date>(new Date());

// Derived stores
export const matrixConfig = derived(buttonConfig, ($config) => $config.matrixConfig);
export const buttonActions = derived(buttonConfig, ($config) => $config.buttonActions);

// Polling interval (in milliseconds) - check for updates every 30 seconds
const POLLING_INTERVAL = 30000;
let pollingInterval: number | null = null;

// Load configuration from JSON file
async function loadButtonConfig(): Promise<ButtonConfig> {
  try {
    const response = await fetch('/api/button-config', {
      cache: 'no-store', // Ensure we always get the latest version
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const config: ButtonConfig = await response.json();
    
    // Validate the loaded configuration
    if (!config.matrixConfig || !config.buttonActions || !Array.isArray(config.buttonActions)) {
      throw new Error('Invalid configuration format');
    }
    
    return config;
  } catch (error) {
    console.error('Error loading button configuration:', error);
    // Fallback to static file if API fails
    try {
      const fallbackResponse = await fetch('/buttonConfig.json', {
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      
      if (fallbackResponse.ok) {
        return await fallbackResponse.json();
      }
    } catch (fallbackError) {
      console.error('Fallback also failed:', fallbackError);
    }
    
    return defaultConfig;
  }
}

// Update configuration
export async function updateButtonConfig(): Promise<void> {
  if (!browser) return;
  
  try {
    isLoading.set(true);
    const config = await loadButtonConfig();
    buttonConfig.set(config);
    lastUpdated.set(new Date());
    console.log('Button configuration updated:', config);
  } catch (error) {
    console.error('Failed to update button configuration:', error);
  } finally {
    isLoading.set(false);
  }
}

// Start automatic polling for configuration updates
export function startConfigPolling(): void {
  if (!browser || pollingInterval) return;
  
  // Load initial configuration
  updateButtonConfig();
  
  // Set up polling
  pollingInterval = setInterval(() => {
    updateButtonConfig();
  }, POLLING_INTERVAL);
  
  console.log(`Started button configuration polling every ${POLLING_INTERVAL / 1000} seconds`);
}

// Stop polling
export function stopConfigPolling(): void {
  if (pollingInterval) {
    clearInterval(pollingInterval);
    pollingInterval = null;
    console.log('Stopped button configuration polling');
  }
}

// Manual refresh function for user-triggered updates
export async function refreshConfig(): Promise<void> {
  await updateButtonConfig();
}

// Function to update configuration via API
export async function saveButtonConfig(newConfig: ButtonConfig): Promise<boolean> {
  if (!browser) return false;
  
  try {
    const response = await fetch('/api/button-config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(newConfig)
    });
    
    if (response.ok) {
      // Update the store with the new configuration
      buttonConfig.set(newConfig);
      lastUpdated.set(new Date());
      return true;
    } else {
      console.error('Failed to save configuration:', response.statusText);
      return false;
    }
  } catch (error) {
    console.error('Error saving button configuration:', error);
    return false;
  }
}

// Utility function to get icon path for image icons
export function getIconPath(icon: string, iconType: 'emoji' | 'image'): string {
  if (iconType === 'emoji') {
    return icon;
  }
  return `/mcpIcons/${icon}`;
}

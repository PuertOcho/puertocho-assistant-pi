/**
 * Audio API Service
 * Handles communication with backend audio endpoints
 */

const API_BASE_URL = 'http://localhost:8000';

export interface AudioVerificationStatus {
  enabled: boolean;
  directory: string;
  total_files: number;
  total_size_mb: number;
  oldest_file?: string;
  newest_file?: string;
  retention_days: number;
  max_files: number;
}

export interface AudioFile {
  id: string;
  filename: string;
  file_path: string;
  file_size: number;
  created_at: string;
  duration?: number;
  quality_score?: number;
}

export interface AudioProcessingHistory {
  total_processed: number;
  processing_queue_length: number;
  average_processing_time: number;
  last_processed?: string;
  recent_files: AudioFile[];
}

/**
 * Get audio verification status from backend
 */
export async function getAudioVerificationStatus(): Promise<AudioVerificationStatus> {
  try {
    const response = await fetch(`${API_BASE_URL}/audio/verification/status`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching audio verification status:', error);
    throw error;
  }
}

/**
 * Get list of audio verification files
 */
export async function getAudioVerificationFiles(): Promise<AudioFile[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/audio/verification/files`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    const data = await response.json();
    return data.files || [];
  } catch (error) {
    console.error('Error fetching audio verification files:', error);
    throw error;
  }
}

/**
 * Get audio processing history
 */
export async function getAudioProcessingHistory(): Promise<AudioProcessingHistory> {
  try {
    const response = await fetch(`${API_BASE_URL}/audio/processing/history`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching audio processing history:', error);
    throw error;
  }
}

/**
 * Get audio file content (for playing or downloading)
 */
export async function getAudioFileUrl(filename: string): Promise<string> {
  // In a real implementation, this would return a proper URL to download/stream the audio file
  // For now, we'll construct a URL based on the filename
  return `${API_BASE_URL}/audio/verification/download/${encodeURIComponent(filename)}`;
}

/**
 * Download audio file
 */
export async function downloadAudioFile(filename: string): Promise<Blob> {
  try {
    const response = await fetch(`${API_BASE_URL}/audio/verification/download/${encodeURIComponent(filename)}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.blob();
  } catch (error) {
    console.error('Error downloading audio file:', error);
    throw error;
  }
}

/**
 * Get current backend status including audio processor info
 */
export async function getBackendStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/status`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching backend status:', error);
    throw error;
  }
}

/**
 * Refresh audio data from backend
 * This function can be called periodically to sync the latest audio information
 */
export async function refreshAudioData(): Promise<{
  status: AudioVerificationStatus;
  files: AudioFile[];
  history: AudioProcessingHistory;
}> {
  try {
    const [status, files, history] = await Promise.all([
      getAudioVerificationStatus(),
      getAudioVerificationFiles(),
      getAudioProcessingHistory()
    ]);

    return { status, files, history };
  } catch (error) {
    console.error('Error refreshing audio data:', error);
    throw error;
  }
}

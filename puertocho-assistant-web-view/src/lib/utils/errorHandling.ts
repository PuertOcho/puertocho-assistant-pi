/**
 * Error Handling and Logging System
 * Centralized error management for scalability and maintainability
 */

import { writable } from 'svelte/store';
import { configUtils } from '$lib/config/appConfig';

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3
}

export interface LogEntry {
  id: string;
  timestamp: Date;
  level: LogLevel;
  category: string;
  message: string;
  data?: any;
  error?: Error;
}

export interface AppError {
  id: string;
  timestamp: Date;
  type: 'network' | 'websocket' | 'audio' | 'ui' | 'validation' | 'unknown';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  details?: any;
  recovered: boolean;
}

// Error store for UI display
export const errorStore = writable<AppError[]>([]);
export const logStore = writable<LogEntry[]>([]);

class Logger {
  private logs: LogEntry[] = [];
  private maxLogs = 1000;
  private logLevel = configUtils.isDevelopment() ? LogLevel.DEBUG : LogLevel.INFO;

  private createLogEntry(level: LogLevel, category: string, message: string, data?: any, error?: Error): LogEntry {
    return {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      level,
      category,
      message,
      data,
      error
    };
  }

  private addLog(entry: LogEntry) {
    if (entry.level >= this.logLevel) {
      this.logs.unshift(entry);
      if (this.logs.length > this.maxLogs) {
        this.logs = this.logs.slice(0, this.maxLogs);
      }
      logStore.set([...this.logs]);

      // Console output in development
      if (configUtils.isDevelopment()) {
        const method = entry.level === LogLevel.ERROR ? 'error' : 
                     entry.level === LogLevel.WARN ? 'warn' : 
                     entry.level === LogLevel.INFO ? 'info' : 'debug';
        
        console[method](`[${entry.category}] ${entry.message}`, entry.data || '');
        if (entry.error) console.error(entry.error);
      }
    }
  }

  debug(category: string, message: string, data?: any) {
    this.addLog(this.createLogEntry(LogLevel.DEBUG, category, message, data));
  }

  info(category: string, message: string, data?: any) {
    this.addLog(this.createLogEntry(LogLevel.INFO, category, message, data));
  }

  warn(category: string, message: string, data?: any) {
    this.addLog(this.createLogEntry(LogLevel.WARN, category, message, data));
  }

  error(category: string, message: string, error?: Error, data?: any) {
    this.addLog(this.createLogEntry(LogLevel.ERROR, category, message, data, error));
  }

  getLogs(): LogEntry[] {
    return [...this.logs];
  }

  clearLogs() {
    this.logs = [];
    logStore.set([]);
  }
}

class ErrorManager {
  private errors: AppError[] = [];
  private maxErrors = 100;

  createError(
    type: AppError['type'], 
    severity: AppError['severity'], 
    message: string, 
    details?: any
  ): AppError {
    return {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      type,
      severity,
      message,
      details,
      recovered: false
    };
  }

  addError(error: AppError) {
    this.errors.unshift(error);
    if (this.errors.length > this.maxErrors) {
      this.errors = this.errors.slice(0, this.maxErrors);
    }
    errorStore.set([...this.errors]);

    // Log the error
    logger.error('ERROR_MANAGER', error.message, undefined, { type: error.type, severity: error.severity, details: error.details });

    // Auto-recovery for certain error types
    this.attemptAutoRecovery(error);
  }

  markAsRecovered(errorId: string) {
    const error = this.errors.find(e => e.id === errorId);
    if (error) {
      error.recovered = true;
      errorStore.set([...this.errors]);
      logger.info('ERROR_MANAGER', `Error recovered: ${error.message}`, { errorId });
    }
  }

  clearErrors() {
    this.errors = [];
    errorStore.set([]);
  }

  private attemptAutoRecovery(error: AppError) {
    setTimeout(() => {
      switch (error.type) {
        case 'network':
          if (error.severity === 'low' || error.severity === 'medium') {
            this.markAsRecovered(error.id);
          }
          break;
        case 'websocket':
          // WebSocket auto-reconnection is handled by websocketService
          break;
        default:
          // No auto-recovery for other types
          break;
      }
    }, 5000); // 5 second delay
  }

  getErrors(): AppError[] {
    return [...this.errors];
  }

  getCriticalErrors(): AppError[] {
    return this.errors.filter(e => e.severity === 'critical' && !e.recovered);
  }

  hasUnrecoveredErrors(): boolean {
    return this.errors.some(e => !e.recovered);
  }
}

// Global instances
export const logger = new Logger();
export const errorManager = new ErrorManager();

// Error handling utilities
export const errorUtils = {
  /**
   * Handle API errors consistently
   */
  handleApiError(error: any, context: string): AppError {
    let message = 'Unknown API error';
    let severity: AppError['severity'] = 'medium';
    
    if (error.response) {
      // HTTP error response
      message = `API Error ${error.response.status}: ${error.response.statusText}`;
      severity = error.response.status >= 500 ? 'high' : 'medium';
    } else if (error.request) {
      // Network error
      message = 'Network connection error';
      severity = 'high';
    } else if (error.message) {
      message = error.message;
    }

    const appError = errorManager.createError('network', severity, message, { context, originalError: error });
    errorManager.addError(appError);
    return appError;
  },

  /**
   * Handle WebSocket errors
   */
  handleWebSocketError(error: any, context: string): AppError {
    const message = error.message || 'WebSocket connection error';
    const appError = errorManager.createError('websocket', 'high', message, { context, originalError: error });
    errorManager.addError(appError);
    return appError;
  },

  /**
   * Handle audio processing errors
   */
  handleAudioError(error: any, context: string): AppError {
    const message = error.message || 'Audio processing error';
    const severity: AppError['severity'] = context.includes('critical') ? 'critical' : 'medium';
    const appError = errorManager.createError('audio', severity, message, { context, originalError: error });
    errorManager.addError(appError);
    return appError;
  },

  /**
   * Handle validation errors
   */
  handleValidationError(message: string, context: string, details?: any): AppError {
    const appError = errorManager.createError('validation', 'low', message, { context, details });
    errorManager.addError(appError);
    return appError;
  },

  /**
   * Create user-friendly error messages
   */
  getUserFriendlyMessage(error: AppError): string {
    switch (error.type) {
      case 'network':
        return error.severity === 'high' ? 
          'Sin conexión a internet. Verifique su conexión.' :
          'Error temporal de conexión. Reintentando...';
      case 'websocket':
        return 'Conexión en tiempo real perdida. Reconectando...';
      case 'audio':
        return error.severity === 'critical' ?
          'Error crítico en procesamiento de audio' :
          'Error temporal en procesamiento de audio';
      case 'validation':
        return `Error de validación: ${error.message}`;
      default:
        return 'Error inesperado. Por favor, recargue la página.';
    }
  }
};

// Performance monitoring
export const performanceMonitor = {
  timers: new Map<string, number>(),

  start(label: string) {
    this.timers.set(label, performance.now());
  },

  end(label: string): number {
    const startTime = this.timers.get(label);
    if (startTime) {
      const duration = performance.now() - startTime;
      this.timers.delete(label);
      
      if (configUtils.isDevelopment()) {
        logger.debug('PERFORMANCE', `${label}: ${duration.toFixed(2)}ms`);
      }
      
      return duration;
    }
    return 0;
  },

  measure<T>(label: string, fn: () => T): T {
    this.start(label);
    try {
      const result = fn();
      return result;
    } finally {
      this.end(label);
    }
  }
};

// Global error handler
if (typeof window !== 'undefined') {
  window.addEventListener('error', (event) => {
    const error = errorManager.createError(
      'unknown',
      'high',
      event.message || 'Unhandled JavaScript error',
      {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack
      }
    );
    errorManager.addError(error);
  });

  window.addEventListener('unhandledrejection', (event) => {
    const error = errorManager.createError(
      'unknown',
      'high',
      'Unhandled Promise rejection',
      {
        reason: event.reason,
        stack: event.reason?.stack
      }
    );
    errorManager.addError(error);
  });
}

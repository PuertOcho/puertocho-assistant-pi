#!/usr/bin/env python3
"""
Logging utility for PuertoCho Assistant Hardware Service
"""

import logging
import logging.handlers
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)

class HardwareLogger:
    """Hardware service logger with structured logging"""
    
    def __init__(self, name: str = "hardware", log_level: str = "INFO", 
                 log_file: str = None, 
                 log_format: str = "json"):
        self.name = name
        self.log_level = log_level
        
        # Usar variable de entorno o path por defecto
        if log_file is None:
            log_dir = os.environ.get('LOG_DIR', '/app/logs')
            self.log_file = os.path.join(log_dir, 'hardware.log')
        else:
            self.log_file = log_file
            
        self.log_format = log_format
        self.logger = None
        
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with handlers"""
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self._get_log_level())
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self._get_log_level())
        
        # File handler with rotation
        self._ensure_log_directory()
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(self._get_log_level())
        
        # Set formatters
        if self.log_format.lower() == "json":
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def _get_log_level(self) -> int:
        """Get numeric log level"""
        level_mapping = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return level_mapping.get(self.log_level.upper(), logging.INFO)
    
    def _ensure_log_directory(self):
        """Ensure log directory exists"""
        log_dir = Path(self.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    def debug(self, message: str, extra: Dict[str, Any] = None):
        """Log debug message"""
        self._log(logging.DEBUG, message, extra)
    
    def info(self, message: str, extra: Dict[str, Any] = None):
        """Log info message"""
        self._log(logging.INFO, message, extra)
    
    def warning(self, message: str, extra: Dict[str, Any] = None):
        """Log warning message"""
        self._log(logging.WARNING, message, extra)
    
    def error(self, message: str, extra: Dict[str, Any] = None):
        """Log error message"""
        self._log(logging.ERROR, message, extra)
    
    def critical(self, message: str, extra: Dict[str, Any] = None):
        """Log critical message"""
        self._log(logging.CRITICAL, message, extra)
    
    def _log(self, level: int, message: str, extra: Dict[str, Any] = None):
        """Internal log method"""
        if extra:
            # Create log record with extra fields
            record = self.logger.makeRecord(
                self.logger.name, level, __file__, 0, message, (), None
            )
            record.extra_fields = extra
            self.logger.handle(record)
        else:
            self.logger.log(level, message)

# Global logger instance
logger = HardwareLogger()

def get_logger(name: str = "hardware") -> HardwareLogger:
    """Get logger instance"""
    return HardwareLogger(name)

def log_hardware_event(event_type: str, details: Dict[str, Any] = None):
    """Log hardware-specific event"""
    extra = {
        "event_type": event_type,
        "component": "hardware",
        **(details or {})
    }
    logger.info(f"Hardware event: {event_type}", extra)

def log_audio_event(event_type: str, details: Dict[str, Any] = None):
    """Log audio-specific event"""
    extra = {
        "event_type": event_type,
        "component": "audio",
        **(details or {})
    }
    logger.info(f"Audio event: {event_type}", extra)

def log_wake_word_event(detected: bool, confidence: float = None):
    """Log wake word detection event"""
    extra = {
        "event_type": "wake_word_detection",
        "component": "wake_word",
        "detected": detected,
        "confidence": confidence
    }
    logger.info(f"Wake word {'detected' if detected else 'not detected'}", extra)

def log_button_event(event_type: str, duration: float = None):
    """Log button event"""
    extra = {
        "event_type": event_type,
        "component": "button",
        "duration": duration
    }
    logger.info(f"Button event: {event_type}", extra)

def log_led_event(pattern: str, color: str = None):
    """Log LED event"""
    extra = {
        "event_type": "led_pattern_change",
        "component": "led",
        "pattern": pattern,
        "color": color
    }
    logger.info(f"LED pattern changed: {pattern}", extra)

def log_nfc_event(event_type: str, tag_id: str = None):
    """Log NFC event"""
    extra = {
        "event_type": event_type,
        "component": "nfc",
        "tag_id": tag_id
    }
    logger.info(f"NFC event: {event_type}", extra)

def log_performance_metric(metric_name: str, value: float, unit: str = None):
    """Log performance metric"""
    extra = {
        "metric_type": "performance",
        "metric_name": metric_name,
        "value": value,
        "unit": unit
    }
    logger.info(f"Performance metric: {metric_name} = {value} {unit or ''}", extra)

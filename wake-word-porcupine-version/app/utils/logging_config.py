"""
Configuración de logging estructurado para el asistente PuertoCho.
"""

import logging
import sys
from typing import Optional

def setup_logging(level: str = "INFO", format_type: str = "structured") -> logging.Logger:
    """
    Configurar logging estructurado para el asistente.
    
    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
        format_type: Tipo de formato ("structured" o "simple")
    
    Returns:
        Logger configurado
    """
    # Configurar nivel
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Formato estructurado para mejor análisis
    if format_type == "structured":
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # Formato simple para desarrollo
        formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
    
    # Configurar handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    # Configurar logger principal
    logger = logging.getLogger('puertocho_assistant')
    logger.setLevel(log_level)
    logger.addHandler(handler)
    
    # Evitar duplicación de logs
    logger.propagate = False
    
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Obtener logger para un módulo específico.
    
    Args:
        name: Nombre del módulo (opcional)
    
    Returns:
        Logger configurado para el módulo
    """
    if name:
        return logging.getLogger(f'puertocho_assistant.{name}')
    return logging.getLogger('puertocho_assistant')

# Configurar print con flush automático para logs en tiempo real
_original_print = print

def print_flush(*args, **kwargs):
    """Print con flush automático para logs en tiempo real"""
    _original_print(*args, **kwargs)
    sys.stdout.flush()

def setup_print_flush():
    """Configurar print global con flush automático"""
    import builtins
    builtins.print = print_flush

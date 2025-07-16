#!/usr/bin/env python3
"""
Script de prueba para los LEDs RGB integrados del ReSpeaker 2-Mic Pi HAT V1.0
"""

import sys
import time
import argparse
from pathlib import Path

# Agregar el directorio app al path (desde scripts subir un nivel y luego a app)
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))

from utils.led_controller import get_led_controller
from utils.logging_config import get_logger

logger = get_logger('test_leds')

def test_basic_colors():
    """Prueba básica de colores individuales"""
    logger.info("🎨 Probando colores básicos...")
    
    led_controller = get_led_controller(brightness=10)
    
    if not led_controller.is_enabled():
        logger.error("❌ LEDs no habilitados, no se puede probar")
        return
    
    # Probar colores básicos
    colors = {
        'Rojo': [255, 0, 0] * 3,
        'Verde': [0, 255, 0] * 3,
        'Azul': [0, 0, 255] * 3,
        'Amarillo': [255, 255, 0] * 3,
        'Magenta': [255, 0, 255] * 3,
        'Cyan': [0, 255, 255] * 3,
        'Blanco': [255, 255, 255] * 3,
    }
    
    for color_name, color_values in colors.items():
        logger.info(f"  - {color_name}")
        led_controller.write(color_values)
        time.sleep(1)
    
    # Apagar
    led_controller.off()
    logger.info("✅ Prueba de colores básicos completada")

def test_states():
    """Prueba de estados del asistente"""
    logger.info("🤖 Probando estados del asistente...")
    
    led_controller = get_led_controller(brightness=10)
    led_controller.test_sequence()

def test_individual_leds():
    """Prueba de LEDs individuales"""
    logger.info("🔍 Probando LEDs individuales...")
    
    led_controller = get_led_controller(brightness=10)
    
    if not led_controller.is_enabled():
        logger.error("❌ LEDs no habilitados, no se puede probar")
        return
    
    # Probar cada LED individualmente
    for i in range(3):
        logger.info(f"  - LED {i}")
        colors = [0, 0, 0] * 3
        colors[i*3] = 100    # Rojo
        colors[i*3+1] = 0    # Verde
        colors[i*3+2] = 0    # Azul
        led_controller.write(colors)
        time.sleep(1)
        
        colors[i*3] = 0      # Rojo
        colors[i*3+1] = 100  # Verde
        colors[i*3+2] = 0    # Azul
        led_controller.write(colors)
        time.sleep(1)
        
        colors[i*3] = 0      # Rojo
        colors[i*3+1] = 0    # Verde
        colors[i*3+2] = 100  # Azul
        led_controller.write(colors)
        time.sleep(1)
    
    led_controller.off()
    logger.info("✅ Prueba de LEDs individuales completada")

def test_breathing():
    """Efecto de respiración suave"""
    logger.info("💨 Probando efecto de respiración...")
    
    led_controller = get_led_controller(brightness=10)
    
    if not led_controller.is_enabled():
        logger.error("❌ LEDs no habilitados, no se puede probar")
        return
    
    # Efecto de respiración azul
    for cycle in range(3):
        for intensity in range(0, 50, 2):
            colors = [0, 0, intensity] * 3
            led_controller.write(colors)
            time.sleep(0.05)
        
        for intensity in range(50, 0, -2):
            colors = [0, 0, intensity] * 3
            led_controller.write(colors)
            time.sleep(0.05)
    
    led_controller.off()
    logger.info("✅ Efecto de respiración completado")

def test_rotation():
    """Efecto de rotación"""
    logger.info("🔄 Probando efecto de rotación...")
    
    led_controller = get_led_controller(brightness=10)
    
    if not led_controller.is_enabled():
        logger.error("❌ LEDs no habilitados, no se puede probar")
        return
    
    # Efecto de rotación
    for cycle in range(6):
        for pos in range(3):
            colors = [0, 0, 0] * 3
            colors[pos*3] = 50    # Rojo en posición actual
            colors[pos*3+1] = 25  # Verde suave
            led_controller.write(colors)
            time.sleep(0.3)
    
    led_controller.off()
    logger.info("✅ Efecto de rotación completado")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Prueba de LEDs RGB del ReSpeaker")
    parser.add_argument('--test', '-t', 
                       choices=['colors', 'states', 'individual', 'breathing', 'rotation', 'all'],
                       default='states',
                       help='Tipo de prueba a realizar')
    parser.add_argument('--brightness', '-b', type=int, default=10,
                       help='Brillo de los LEDs (1-31)')
    
    args = parser.parse_args()
    
    logger.info("🎮 Iniciando prueba de LEDs RGB integrados del ReSpeaker")
    logger.info(f"   Brillo: {args.brightness}")
    
    try:
        if args.test == 'colors' or args.test == 'all':
            test_basic_colors()
            time.sleep(1)
        
        if args.test == 'states' or args.test == 'all':
            test_states()
            time.sleep(1)
        
        if args.test == 'individual' or args.test == 'all':
            test_individual_leds()
            time.sleep(1)
        
        if args.test == 'breathing' or args.test == 'all':
            test_breathing()
            time.sleep(1)
        
        if args.test == 'rotation' or args.test == 'all':
            test_rotation()
        
        logger.info("🎉 Todas las pruebas completadas")
        
    except KeyboardInterrupt:
        logger.info("⚠️ Prueba interrumpida por el usuario")
    except Exception as e:
        logger.error(f"❌ Error en la prueba: {e}")
    finally:
        # Asegurar que los LEDs se apaguen
        try:
            led_controller = get_led_controller()
            led_controller.off()
            led_controller.cleanup()
        except:
            pass

if __name__ == "__main__":
    main()

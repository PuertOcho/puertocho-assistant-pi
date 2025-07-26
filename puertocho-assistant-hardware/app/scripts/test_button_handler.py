#!/usr/bin/env python3
"""
Script de prueba para ButtonHandler

Prueba la funcionalidad del ButtonHandler tanto en modo real como simulado.
"""

import time
import sys
import os
import threading
from typing import Dict, Any
from pathlib import Path

# Añadir el directorio de la app al path para imports absolutos
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

# Cambiar al directorio de la app para que los imports funcionen
os.chdir(str(app_dir))

try:
    from core.button_handler import ButtonHandler, ButtonEvent, ButtonEventData
    from config import config
    from utils.logger import get_logger
except ImportError as e:
    print(f"❌ Error al importar módulos: {e}")
    print("Asegúrate de estar en el directorio correcto y que todos los archivos existan.")
    print(f"Directorio actual: {os.getcwd()}")
    print(f"App directory: {app_dir}")
    sys.exit(1)

# Configurar logger
logger = get_logger(__name__)

class ButtonTester:
    """Clase para probar ButtonHandler"""
    
    def __init__(self):
        self.events_received = []
        self.test_results = {}
        
    def button_callback(self, event_data: ButtonEventData):
        """Callback para eventos de botón"""
        timestamp = time.strftime("%H:%M:%S", time.localtime(event_data.timestamp))
        
        print(f"[{timestamp}] Evento: {event_data.event_type.value}")
        print(f"    Pin: {event_data.pin}")
        print(f"    Duración: {event_data.press_duration:.2f}s")
        print(f"    Timestamp: {event_data.timestamp}")
        print("-" * 40)
        
        self.events_received.append(event_data)
        
        # Log del evento
        logger.info(f"Evento de botón recibido: {event_data.event_type.value}, duración: {event_data.press_duration:.2f}s")
    
    def test_basic_functionality(self):
        """Prueba funcionalidad básica"""
        print("\n=== Prueba de Funcionalidad Básica ===")
        
        # Crear ButtonHandler en modo simulación
        button_handler = ButtonHandler(simulate=True)
        
        # Registrar callback
        button_handler.register_callback(ButtonEvent.SHORT_PRESS, self.button_callback)
        button_handler.register_callback(ButtonEvent.LONG_PRESS, self.button_callback)
        button_handler.register_callback(ButtonEvent.PRESS_START, self.button_callback)
        button_handler.register_callback(ButtonEvent.PRESS_END, self.button_callback)
        
        # Iniciar handler
        button_handler.start()
        
        # Mostrar estado
        status = button_handler.get_status()
        print(f"Estado inicial: {status}")
        
        # Simular pulsación corta
        print("\nSimulando pulsación corta (0.1s)...")
        button_handler.simulate_button_press(0.1)
        time.sleep(0.5)
        
        # Simular pulsación larga
        print("\nSimulando pulsación larga (3.0s)...")
        button_handler.simulate_button_press(3.0)
        time.sleep(0.5)
        
        # Mostrar estado final
        status = button_handler.get_status()
        print(f"Estado final: {status}")
        
        # Detener handler
        button_handler.stop()
        
        return len(self.events_received) >= 4  # Esperamos al menos 4 eventos
    
    def test_configuration(self):
        """Prueba diferentes configuraciones"""
        print("\n=== Prueba de Configuración ===")
        
        # Probar configuración personalizada
        button_handler = ButtonHandler(
            pin=18,
            debounce_time=0.1,
            long_press_time=1.5,
            simulate=True
        )
        
        status = button_handler.get_status()
        print(f"Configuración personalizada: {status}")
        
        # Verificar valores
        config_ok = (
            status['pin'] == 18 and
            status['debounce_time'] == 0.1 and
            status['long_press_time'] == 1.5 and
            status['simulate'] == True
        )
        
        button_handler.stop()
        return config_ok
    
    def test_callback_management(self):
        """Prueba gestión de callbacks"""
        print("\n=== Prueba de Gestión de Callbacks ===")
        
        button_handler = ButtonHandler(simulate=True)
        
        # Registrar callbacks
        button_handler.register_callback(ButtonEvent.SHORT_PRESS, self.button_callback)
        button_handler.register_callback(ButtonEvent.LONG_PRESS, self.button_callback)
        
        status = button_handler.get_status()
        print(f"Callbacks registrados: {status['callbacks_registered']}")
        
        # Desregistrar callback
        button_handler.unregister_callback(ButtonEvent.SHORT_PRESS)
        
        status = button_handler.get_status()
        print(f"Callbacks después de desregistrar: {status['callbacks_registered']}")
        
        button_handler.stop()
        return len(status['callbacks_registered']) == 1
    
    def test_real_hardware(self):
        """Prueba con hardware real (si está disponible)"""
        print("\n=== Prueba con Hardware Real ===")
        
        if config.simulate_hardware:
            print("Modo simulación activado en config, saltando prueba de hardware real")
            return True
        
        try:
            # Intentar crear ButtonHandler real
            button_handler = ButtonHandler(simulate=False)
            
            # Registrar callback
            button_handler.register_callback(ButtonEvent.SHORT_PRESS, self.button_callback)
            button_handler.register_callback(ButtonEvent.LONG_PRESS, self.button_callback)
            
            # Iniciar handler
            button_handler.start()
            
            print(f"ButtonHandler iniciado en pin {config.gpio.button_pin}")
            print("Presiona el botón para probar (tienes 10 segundos)...")
            print("- Pulsación corta: < 2 segundos")
            print("- Pulsación larga: >= 2 segundos")
            
            # Esperar eventos
            start_time = time.time()
            while time.time() - start_time < 10:
                time.sleep(0.1)
            
            print("Tiempo de prueba terminado")
            
            # Detener handler
            button_handler.stop()
            
            return True
            
        except Exception as e:
            print(f"Error en prueba de hardware real: {e}")
            return False
    
    def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        print("=== INICIANDO PRUEBAS DE BUTTONHANDLER ===")
        print(f"Configuración actual:")
        print(f"  Pin: {config.gpio.button_pin}")
        print(f"  Debounce: {config.gpio.debounce_time}s")
        print(f"  Long press: {config.gpio.long_press_time}s")
        print(f"  Simulate: {config.simulate_hardware}")
        
        tests = [
            ("Funcionalidad Básica", self.test_basic_functionality),
            ("Configuración", self.test_configuration),
            ("Gestión de Callbacks", self.test_callback_management),
            ("Hardware Real", self.test_real_hardware)
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                print(f"\n{'='*50}")
                result = test_func()
                results[test_name] = result
                status = "✓ PASÓ" if result else "✗ FALLÓ"
                print(f"{test_name}: {status}")
            except Exception as e:
                results[test_name] = False
                print(f"{test_name}: ✗ ERROR - {e}")
        
        # Resumen
        print(f"\n{'='*50}")
        print("RESUMEN DE PRUEBAS:")
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✓" if result else "✗"
            print(f"  {status} {test_name}")
        
        print(f"\nResultado: {passed}/{total} pruebas pasaron")
        print(f"Eventos recibidos: {len(self.events_received)}")
        
        return passed == total

def main():
    """Función principal"""
    try:
        tester = ButtonTester()
        success = tester.run_all_tests()
        
        if success:
            print("\n🎉 ¡Todas las pruebas pasaron!")
            sys.exit(0)
        else:
            print("\n❌ Algunas pruebas fallaron")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nPruebas interrumpidas por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\nError inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

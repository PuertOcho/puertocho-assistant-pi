#!/usr/bin/env python3
"""
Tests unitarios para el controlador de LEDs APA102
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.led_controller import (
    LEDController, 
    LEDState, 
    LEDColor, 
    LEDPattern,
    SolidPattern,
    PulsePattern,
    RotatingPattern,
    BlinkPattern
)

class TestLEDColor:
    """Tests para la clase LEDColor"""
    
    def test_valid_color_creation(self):
        """Test creación de color válido"""
        color = LEDColor(255, 128, 0, 200)
        assert color.red == 255
        assert color.green == 128
        assert color.blue == 0
        assert color.brightness == 200
    
    def test_default_brightness(self):
        """Test brillo por defecto"""
        color = LEDColor(255, 0, 0)
        assert color.brightness == 255
    
    def test_invalid_color_values(self):
        """Test valores inválidos"""
        with pytest.raises(ValueError):
            LEDColor(256, 0, 0)
        
        with pytest.raises(ValueError):
            LEDColor(0, -1, 0)
        
        with pytest.raises(ValueError):
            LEDColor(0, 0, 0, 300)

class TestLEDPatterns:
    """Tests para patrones de LED"""
    
    def test_solid_pattern(self):
        """Test patrón sólido"""
        color = LEDColor(255, 0, 0)
        pattern = SolidPattern([color])
        
        result = pattern.get_color(0, 0)
        assert result.red == 255
        assert result.green == 0
        assert result.blue == 0
    
    def test_pulse_pattern(self):
        """Test patrón pulsante"""
        color = LEDColor(255, 0, 0, 200)
        pattern = PulsePattern([color], duration=2.0, min_brightness=50)
        
        # En el mínimo del pulso
        result = pattern.get_color(0, 1.5)  # 3/4 del ciclo
        assert result.brightness >= 50
        assert result.brightness <= 200
    
    def test_rotating_pattern(self):
        """Test patrón giratorio"""
        color = LEDColor(0, 255, 0)
        pattern = RotatingPattern([color], duration=1.0)
        
        # Probar diferentes posiciones
        result1 = pattern.get_color(0, 0)
        result2 = pattern.get_color(1, 0)
        
        # Al menos uno debería estar encendido
        assert result1.green == 255 or result2.green == 255
    
    def test_blink_pattern(self):
        """Test patrón parpadeante"""
        color = LEDColor(255, 255, 0)
        pattern = BlinkPattern([color], duration=1.0, duty_cycle=0.5)
        
        # En la primera mitad del ciclo
        result1 = pattern.get_color(0, 0.25)
        assert result1.red == 255
        assert result1.green == 255
        
        # En la segunda mitad del ciclo
        result2 = pattern.get_color(0, 0.75)
        assert result2.red == 0
        assert result2.green == 0

class TestLEDController:
    """Tests para el controlador principal"""
    
    def test_controller_initialization(self):
        """Test inicialización del controlador"""
        controller = LEDController(num_leds=3, brightness=128, simulate=True)
        
        assert controller.num_leds == 3
        assert controller.brightness == 128
        assert controller.simulate == True
        assert controller.current_state == LEDState.OFF
        assert controller.driver is None
    
    def test_brightness_setting(self):
        """Test configuración de brillo"""
        controller = LEDController(simulate=True)
        
        controller.set_brightness(200)
        assert controller.brightness == 200
        
        with pytest.raises(ValueError):
            controller.set_brightness(300)
        
        with pytest.raises(ValueError):
            controller.set_brightness(-1)
    
    def test_state_changes(self):
        """Test cambios de estado"""
        controller = LEDController(simulate=True)
        
        # Cambiar a estado IDLE
        controller.set_state(LEDState.IDLE)
        assert controller.current_state == LEDState.IDLE
        assert controller.current_pattern is not None
        
        # Cambiar a estado LISTENING
        controller.set_state(LEDState.LISTENING)
        assert controller.current_state == LEDState.LISTENING
        
        # Cambiar a estado ERROR
        controller.set_state(LEDState.ERROR)
        assert controller.current_state == LEDState.ERROR
    
    def test_custom_color(self):
        """Test color personalizado"""
        controller = LEDController(simulate=True)
        
        custom_color = LEDColor(128, 64, 32)
        controller.set_custom_color(custom_color)
        
        assert controller.current_pattern is not None
        assert isinstance(controller.current_pattern, SolidPattern)
    
    def test_predefined_colors(self):
        """Test colores predefinidos"""
        controller = LEDController(simulate=True)
        
        # Verificar que los colores predefinidos existen
        assert 'red' in controller.COLORS
        assert 'green' in controller.COLORS
        assert 'blue' in controller.COLORS
        assert 'yellow' in controller.COLORS
        assert 'white' in controller.COLORS
        
        # Verificar valores
        red = controller.COLORS['red']
        assert red.red == 255
        assert red.green == 0
        assert red.blue == 0
    
    def test_brightness_application(self):
        """Test aplicación de brillo"""
        controller = LEDController(brightness=128, simulate=True)
        
        color = LEDColor(255, 255, 255)
        adjusted = controller._apply_brightness(color)
        
        # Con brillo 128 (50%), los valores deben ser aproximadamente la mitad
        assert adjusted.red == 127  # 255 * 128/255 ≈ 127
        assert adjusted.green == 127
        assert adjusted.blue == 127
    
    def test_animation_control(self):
        """Test control de animación"""
        controller = LEDController(simulate=True)
        
        # Iniciar animación
        controller.start_animation()
        assert controller.animation_running == True
        assert controller.animation_thread is not None
        
        # Detener animación
        controller.stop_animation()
        assert controller.animation_running == False
    
    def test_context_manager(self):
        """Test context manager"""
        with LEDController(simulate=True) as controller:
            assert controller.animation_running == True
            controller.set_state(LEDState.IDLE)
        
        # Después del context manager, debería estar limpio
        assert controller.animation_running == False
    
    def test_test_pattern(self):
        """Test patrón de prueba"""
        controller = LEDController(simulate=True)
        
        # Ejecutar patrón de prueba rápido
        start_time = time.time()
        controller.test_pattern(duration=0.5)
        end_time = time.time()
        
        # Debería tomar aproximadamente 0.5 segundos
        elapsed = end_time - start_time
        assert 0.4 <= elapsed <= 0.7  # Margen de error
        
        # Debería terminar en OFF
        assert controller.current_state == LEDState.OFF
    
    def test_rainbow_pattern(self):
        """Test patrón arcoíris"""
        controller = LEDController(simulate=True)
        
        controller.set_rainbow_pattern(duration=1.0)
        assert controller.current_pattern is not None
        assert controller.current_pattern.duration == 1.0
    
    def test_turn_off(self):
        """Test apagar LEDs"""
        controller = LEDController(simulate=True)
        
        # Encender primero
        controller.set_state(LEDState.LISTENING)
        assert controller.current_state == LEDState.LISTENING
        
        # Apagar
        controller.turn_off()
        assert controller.current_state == LEDState.OFF
    
    def test_cleanup(self):
        """Test limpieza de recursos"""
        controller = LEDController(simulate=True)
        controller.start_animation()
        
        controller.cleanup()
        
        assert controller.animation_running == False
        assert controller.current_state == LEDState.OFF
    
    @patch('core.led_controller.apa102')
    def test_real_hardware_initialization(self, mock_apa102):
        """Test inicialización con hardware real"""
        mock_driver = Mock()
        mock_apa102.APA102.return_value = mock_driver
        
        controller = LEDController(num_leds=3, simulate=False)
        
        # Verificar que se llamó al driver
        mock_apa102.APA102.assert_called_once_with(num_led=3, global_brightness=128)
        assert controller.driver is mock_driver
    
    @patch('core.led_controller.apa102')
    def test_hardware_led_update(self, mock_apa102):
        """Test actualización de LEDs con hardware"""
        mock_driver = Mock()
        mock_apa102.APA102.return_value = mock_driver
        
        controller = LEDController(num_leds=3, simulate=False)
        
        # Establecer color
        color = LEDColor(255, 0, 0)
        controller.set_custom_color(color)
        
        # Forzar actualización
        controller._update_all_leds([color, color, color])
        
        # Verificar llamadas al driver
        assert mock_driver.set_pixel.call_count == 3
        mock_driver.show.assert_called()

class TestThreadSafety:
    """Tests para seguridad en hilos"""
    
    def test_concurrent_state_changes(self):
        """Test cambios de estado concurrentes"""
        controller = LEDController(simulate=True)
        controller.start_animation()
        
        def change_states():
            for i in range(10):
                state = LEDState.IDLE if i % 2 == 0 else LEDState.PROCESSING
                controller.set_state(state)
                time.sleep(0.01)
        
        # Ejecutar cambios concurrentes
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=change_states)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        controller.cleanup()
        
        # No debería haber excepciones
        assert True

class TestErrorHandling:
    """Tests para manejo de errores"""
    
    def test_invalid_state(self):
        """Test estado inválido"""
        controller = LEDController(simulate=True)
        
        # Esto no debería lanzar excepción
        try:
            controller.set_state("invalid_state")
            assert False, "Should have raised an exception"
        except (ValueError, AttributeError):
            assert True
    
    def test_empty_pattern(self):
        """Test patrón vacío"""
        pattern = SolidPattern([])
        color = pattern.get_color(0, 0)
        
        assert color.red == 0
        assert color.green == 0
        assert color.blue == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

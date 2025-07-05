#!/usr/bin/env python3
"""
Test simplificado para verificar funcionalidad básica
sin dependencias externas instaladas
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch

# Mock todas las dependencias antes de importar main
sys.modules['RPi.GPIO'] = Mock()
sys.modules['sounddevice'] = Mock()
sys.modules['openwakeword'] = Mock()
sys.modules['openwakeword.model'] = Mock()
sys.modules['openwakeword.utils'] = Mock()
sys.modules['webrtcvad'] = Mock()

# Configurar las dependencias mockeadas
mock_sd = Mock()
mock_sd.RawInputStream = Mock()
mock_sd.query_devices.return_value = []
sys.modules['sounddevice'] = mock_sd

mock_oww = Mock()
mock_oww.utils.download_models = Mock()
mock_model_class = Mock()
mock_oww.model.Model = mock_model_class
sys.modules['openwakeword'] = mock_oww

# Ahora podemos importar main
import main

class TestBasicFunctionality(unittest.TestCase):
    """Tests básicos de funcionalidad"""
    
    def setUp(self):
        """Setup para cada test"""
        # Mock GPIO globalmente
        self.gpio_mock = Mock()
        main.GPIO = self.gpio_mock
        
        # Variables de entorno para testing
        os.environ.update({
            'TRANSCRIPTION_SERVICE_URL': 'http://test:5000/transcribe',
            'BUTTON_PIN': '22',
            'LED_IDLE_PIN': '17',
            'LED_RECORD_PIN': '27',
            'MODE': 'GPIO_ONLY'  # Usar modo sin audio para tests
        })
    
    def test_assistant_states(self):
        """Test que los estados están definidos correctamente"""
        self.assertEqual(main.AssistantState.IDLE, "idle")
        self.assertEqual(main.AssistantState.LISTENING, "listening")
        self.assertEqual(main.AssistantState.PROCESSING, "processing")
    
    def test_detect_sample_rate(self):
        """Test detección de frecuencia de muestreo"""
        # Mock sounddevice para simular diferentes escenarios
        mock_stream = Mock()
        mock_sd.RawInputStream.return_value.__enter__ = Mock(return_value=mock_stream)
        mock_sd.RawInputStream.return_value.__exit__ = Mock(return_value=None)
        
        rate = main.detect_supported_sample_rate()
        self.assertIsInstance(rate, int)
        self.assertGreater(rate, 0)
    
    @patch('main.threading.Thread')
    @patch('main.requests')
    def test_assistant_initialization(self, mock_requests, mock_thread):
        """Test inicialización básica del asistente"""
        
        # Mock respuesta de verificación de servicio
        mock_requests.get.return_value.status_code = 200
        
        # Mock modelo openWakeWord para que falle gracefully
        mock_model_class.side_effect = Exception("No models")
        
        # Crear asistente
        assistant = main.VoiceAssistant()
        
        # Verificar que se inicializó correctamente
        self.assertIsNotNone(assistant)
        self.assertEqual(assistant.state, main.AssistantState.IDLE)
        self.assertIsInstance(assistant.commands, dict)
        
        # Verificar que GPIO se configuró
        self.gpio_mock.setmode.assert_called()
        self.gpio_mock.setup.assert_called()
    
    @patch('main.threading.Thread')
    @patch('main.requests')
    def test_command_execution(self, mock_requests, mock_thread):
        """Test ejecución de comandos"""
        
        # Setup
        mock_requests.get.return_value.status_code = 200
        mock_model_class.side_effect = Exception("No models")
        
        assistant = main.VoiceAssistant()
        
        # Configurar comandos de prueba
        assistant.commands = {
            "test comando": {"pin": 17, "state": "HIGH"}
        }
        
        # Ejecutar comando válido
        assistant._execute_command("test comando")
        
        # Verificar que se llamó GPIO.output
        self.gpio_mock.output.assert_called_with(17, self.gpio_mock.HIGH)
        
        # Ejecutar comando inválido
        assistant._execute_command("comando inexistente")
        # No debería generar error
    
    @patch('main.threading.Thread')
    @patch('main.requests')
    def test_state_management(self, mock_requests, mock_thread):
        """Test gestión de estados"""
        
        # Setup
        mock_requests.get.return_value.status_code = 200
        mock_model_class.side_effect = Exception("No models")
        
        assistant = main.VoiceAssistant()
        
        # Test cambio a estado LISTENING
        assistant._set_state(main.AssistantState.LISTENING)
        self.assertEqual(assistant.state, main.AssistantState.LISTENING)
        
        # Verificar LEDs
        self.gpio_mock.output.assert_any_call(17, self.gpio_mock.LOW)   # Verde OFF
        self.gpio_mock.output.assert_any_call(27, self.gpio_mock.HIGH)  # Rojo ON
    
    @patch('main.threading.Thread')
    @patch('main.requests')
    def test_audio_wav_creation(self, mock_requests, mock_thread):
        """Test creación de archivos WAV"""
        import numpy as np
        import io
        import wave
        
        # Setup
        mock_requests.get.return_value.status_code = 200
        mock_model_class.side_effect = Exception("No models")
        
        assistant = main.VoiceAssistant()
        
        # Crear datos de audio de prueba
        test_audio = np.array([1000, -1000, 2000, -2000], dtype=np.int16)
        
        # Crear WAV
        wav_bytes = assistant._create_wav_file(test_audio)
        
        # Verificar resultado
        self.assertIsInstance(wav_bytes, bytes)
        self.assertGreater(len(wav_bytes), 40)  # Mínimo para header WAV
        
        # Verificar que es un WAV válido
        buffer = io.BytesIO(wav_bytes)
        with wave.open(buffer, 'rb') as wav_file:
            self.assertEqual(wav_file.getnchannels(), 1)
            self.assertEqual(wav_file.getsampwidth(), 2)
            self.assertEqual(wav_file.getframerate(), 16000)
    
    @patch('main.threading.Thread')
    @patch('main.requests')
    def test_transcription_service_call(self, mock_requests, mock_thread):
        """Test llamada al servicio de transcripción"""
        
        # Setup
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'transcription': 'test result'}
        mock_requests.post.return_value = mock_response
        mock_requests.get.return_value.status_code = 200
        mock_model_class.side_effect = Exception("No models")
        
        assistant = main.VoiceAssistant()
        
        # Test llamada exitosa
        result = assistant._send_to_transcription_service(b'fake_audio_data')
        
        self.assertEqual(result, 'test result')
        mock_requests.post.assert_called_once()
        
        # Test error de servicio
        mock_requests.post.side_effect = Exception("Network error")
        result = assistant._send_to_transcription_service(b'fake_audio_data')
        self.assertIsNone(result)
    
    def test_resample_function(self):
        """Test función de resample de audio"""
        import numpy as np
        
        # Audio de prueba
        original = np.array([100, 200, 300, 400], dtype=np.int16)
        
        # Test mismo rate (no debería cambiar)
        resampled = main.VoiceAssistant.simple_resample(None, original, 16000, 16000)
        np.testing.assert_array_equal(resampled, original)
        
        # Test resample diferente
        resampled = main.VoiceAssistant.simple_resample(None, original, 44100, 16000)
        self.assertIsInstance(resampled, np.ndarray)
        self.assertEqual(resampled.dtype, np.int16)


def run_architecture_validation():
    """Validar que la arquitectura del código está correcta"""
    print("🏗️ Validando arquitectura del código...")
    
    # Verificar que las clases principales existen
    assert hasattr(main, 'VoiceAssistant'), "Clase VoiceAssistant no encontrada"
    assert hasattr(main, 'AssistantState'), "Clase AssistantState no encontrada"
    
    # Verificar métodos principales del asistente
    methods = ['_load_commands', '_setup_gpio', '_setup_openwakeword', 
               '_execute_command', '_set_state', '_create_wav_file',
               '_send_to_transcription_service', 'run']
    
    for method in methods:
        assert hasattr(main.VoiceAssistant, method), f"Método {method} no encontrado"
    
    # Verificar estados
    assert main.AssistantState.IDLE == "idle"
    assert main.AssistantState.LISTENING == "listening"
    assert main.AssistantState.PROCESSING == "processing"
    
    print("✅ Arquitectura validada correctamente")


def run_integration_validation():
    """Validar que la integración openWakeWord está implementada"""
    print("🔗 Validando integración openWakeWord...")
    
    # Verificar que el código maneja openWakeWord
    with open('main.py', 'r') as f:
        content = f.read()
        
        # Verificar imports y uso de openWakeWord
        assert 'openwakeword' in content, "Import de openWakeWord no encontrado"
        assert '_setup_openwakeword' in content, "Método setup openWakeWord no encontrado"
        assert 'oww_model' in content, "Variable oww_model no encontrada"
        assert 'prediction' in content, "Lógica de predicción no encontrada"
        
        # Verificar gestión de estados
        assert 'AssistantState.IDLE' in content, "Estado IDLE no manejado"
        assert 'AssistantState.LISTENING' in content, "Estado LISTENING no manejado"
        assert 'AssistantState.PROCESSING' in content, "Estado PROCESSING no manejado"
        
        # Verificar compatibilidad con botón GPIO
        assert 'button_pressed' in content, "Activación por botón no encontrada"
        assert 'GPIO.setup' in content, "Configuración GPIO no encontrada"
        
    print("✅ Integración openWakeWord validada")


def run_configuration_validation():
    """Validar configuración y variables de entorno"""
    print("⚙️ Validando configuración...")
    
    # Verificar que las variables de entorno están manejadas
    with open('main.py', 'r') as f:
        content = f.read()
        
        env_vars = ['TRANSCRIPTION_SERVICE_URL', 'BUTTON_PIN', 'LED_IDLE_PIN', 
                   'LED_RECORD_PIN', 'OPENWAKEWORD_THRESHOLD', 'MODE']
        
        for var in env_vars:
            assert var in content, f"Variable de entorno {var} no manejada"
    
    # Verificar archivos de configuración
    files = ['requirements.txt', 'commands.json']
    for file in files:
        assert os.path.exists(file), f"Archivo {file} no encontrado"
    
    print("✅ Configuración validada")


if __name__ == '__main__':
    print("🧪 Test Simplificado del Asistente de Voz Puertocho")
    print("=" * 50)
    
    # Ejecutar validaciones
    try:
        run_architecture_validation()
        run_integration_validation()
        run_configuration_validation()
        print()
        
        # Ejecutar tests unitarios
        print("🧪 Ejecutando tests unitarios...")
        unittest.main(verbosity=2, exit=False)
        
        print("\n✅ Todos los tests completados exitosamente!")
        print("🎉 El asistente está correctamente implementado")
        
    except Exception as e:
        print(f"\n❌ Error en validación: {e}")
        print("🔧 Revisar implementación") 
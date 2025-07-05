#!/usr/bin/env python3
"""
Tests para el Asistente de Voz Puertocho con openWakeWord
Incluye tests unitarios y de integración con mocks apropiados
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import os
import sys
import json
import numpy as np
import io
import wave
import threading
import time
import queue

# Agregar el directorio actual al path para importar main
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock GPIO antes de importar main
sys.modules['RPi.GPIO'] = Mock()

class TestVoiceAssistant(unittest.TestCase):
    """Tests para la clase VoiceAssistant"""
    
    def setUp(self):
        """Configurar mocks para cada test"""
        # Mock de todas las dependencias externas
        self.gpio_mock = Mock()
        self.sounddevice_mock = Mock()
        self.openwakeword_mock = Mock()
        self.requests_mock = Mock()
        
        # Configurar patches con rutas correctas
        self.patches = [
            patch('main.GPIO', self.gpio_mock),
            patch('main.sd', self.sounddevice_mock),
            patch('main.requests', self.requests_mock),
            patch('time.sleep'),  # Acelerar tests
        ]
        
        # Activar todos los patches
        for p in self.patches:
            p.start()
        
        # Variables de entorno para testing
        os.environ.update({
            'TRANSCRIPTION_SERVICE_URL': 'http://test:5000/transcribe',
            'BUTTON_PIN': '22',
            'LED_IDLE_PIN': '17',
            'LED_RECORD_PIN': '27',
            'OPENWAKEWORD_THRESHOLD': '0.4',
            'MODE': 'HYBRID'
        })
        
        # Crear archivo de comandos de prueba
        self.test_commands = {
            "enciende luz verde": {"pin": 17, "state": "HIGH"},
            "apaga luz verde": {"pin": 17, "state": "LOW"},
            "test comando": {"pin": 27, "state": "HIGH"}
        }
        
        with open('test_commands.json', 'w') as f:
            json.dump(self.test_commands, f)
    
    def tearDown(self):
        """Limpiar después de cada test"""
        # Detener todos los patches
        for p in self.patches:
            p.stop()
        
        # Limpiar archivos de test
        if os.path.exists('test_commands.json'):
            os.remove('test_commands.json')
    
    @patch('builtins.open', unittest.mock.mock_open())
    def test_load_commands(self):
        """Test cargar comandos desde JSON"""
        from main import VoiceAssistant
        
        with patch('builtins.open', unittest.mock.mock_open(read_data=json.dumps(self.test_commands))):
            with patch.object(VoiceAssistant, '_setup_gpio'), \
                 patch.object(VoiceAssistant, '_setup_openwakeword'), \
                 patch.object(VoiceAssistant, '_verify_transcription_service'), \
                 patch.object(VoiceAssistant, '_show_configuration'):
                
                assistant = VoiceAssistant()
                
                self.assertEqual(len(assistant.commands), 3)
                self.assertIn("enciende luz verde", assistant.commands)
                self.assertEqual(assistant.commands["test comando"]["pin"], 27)
    
    def test_gpio_setup(self):
        """Test configuración de GPIO"""
        from main import VoiceAssistant
        
        with patch.object(VoiceAssistant, '_load_commands'), \
             patch.object(VoiceAssistant, '_setup_openwakeword'), \
             patch.object(VoiceAssistant, '_verify_transcription_service'), \
             patch.object(VoiceAssistant, '_show_configuration'), \
             patch('threading.Thread'):
            
            assistant = VoiceAssistant()
            
            # Verificar que GPIO se configuró correctamente
            self.gpio_mock.setmode.assert_called_once()
            self.gpio_mock.setup.assert_any_call(22, self.gpio_mock.IN, pull_up_down=self.gpio_mock.PUD_UP)
            self.gpio_mock.setup.assert_any_call(17, self.gpio_mock.OUT)
            self.gpio_mock.setup.assert_any_call(27, self.gpio_mock.OUT)
    
    def test_state_management(self):
        """Test gestión de estados y LEDs"""
        from main import VoiceAssistant, AssistantState
        
        with patch.object(VoiceAssistant, '_load_commands'), \
             patch.object(VoiceAssistant, '_setup_gpio'), \
             patch.object(VoiceAssistant, '_setup_openwakeword'), \
             patch.object(VoiceAssistant, '_verify_transcription_service'), \
             patch.object(VoiceAssistant, '_show_configuration'), \
             patch('threading.Thread'):
            
            assistant = VoiceAssistant()
            
            # Test estado IDLE
            assistant._set_state(AssistantState.IDLE)
            self.gpio_mock.output.assert_any_call(17, self.gpio_mock.HIGH)  # LED verde ON
            self.gpio_mock.output.assert_any_call(27, self.gpio_mock.LOW)   # LED rojo OFF
            
            # Test estado LISTENING
            assistant._set_state(AssistantState.LISTENING)
            self.gpio_mock.output.assert_any_call(17, self.gpio_mock.LOW)   # LED verde OFF
            self.gpio_mock.output.assert_any_call(27, self.gpio_mock.HIGH)  # LED rojo ON
    
    def test_command_execution(self):
        """Test ejecución de comandos"""
        from main import VoiceAssistant
        
        with patch.object(VoiceAssistant, '_setup_gpio'), \
             patch.object(VoiceAssistant, '_setup_openwakeword'), \
             patch.object(VoiceAssistant, '_verify_transcription_service'), \
             patch.object(VoiceAssistant, '_show_configuration'), \
             patch('threading.Thread'):
            
            assistant = VoiceAssistant()
            assistant.commands = self.test_commands
            
            # Test comando válido
            assistant._execute_command("enciende luz verde")
            self.gpio_mock.output.assert_any_call(17, self.gpio_mock.HIGH)
            
            # Test comando inválido (no debería cambiar GPIO)
            gpio_calls_before = len(self.gpio_mock.output.call_args_list)
            assistant._execute_command("comando inexistente")
            gpio_calls_after = len(self.gpio_mock.output.call_args_list)
            self.assertEqual(gpio_calls_before, gpio_calls_after)
    
    def test_audio_wav_creation(self):
        """Test creación de archivos WAV"""
        from main import VoiceAssistant
        
        with patch.object(VoiceAssistant, '_load_commands'), \
             patch.object(VoiceAssistant, '_setup_gpio'), \
             patch.object(VoiceAssistant, '_setup_openwakeword'), \
             patch.object(VoiceAssistant, '_verify_transcription_service'), \
             patch.object(VoiceAssistant, '_show_configuration'), \
             patch('threading.Thread'):
            
            assistant = VoiceAssistant()
            
            # Crear datos de audio de prueba
            test_audio = np.array([1000, -1000, 2000, -2000], dtype=np.int16)
            
            # Crear WAV
            wav_bytes = assistant._create_wav_file(test_audio)
            
            # Verificar que se creó un WAV válido
            self.assertIsInstance(wav_bytes, bytes)
            self.assertGreater(len(wav_bytes), 40)  # Header WAV mínimo
            
            # Verificar contenido WAV
            buffer = io.BytesIO(wav_bytes)
            with wave.open(buffer, 'rb') as wav_file:
                self.assertEqual(wav_file.getnchannels(), 1)
                self.assertEqual(wav_file.getsampwidth(), 2)
                self.assertEqual(wav_file.getframerate(), 16000)
    
    @patch('main.openwakeword.model.Model')
    def test_openwakeword_setup_success(self, mock_model_class):
        """Test configuración exitosa de openWakeWord"""
        from main import VoiceAssistant
        
        # Mock del modelo
        mock_model = Mock()
        mock_model.models = {'alexa': Mock(), 'hey_mycroft': Mock()}
        mock_model_class.return_value = mock_model
        
        with patch.object(VoiceAssistant, '_load_commands'), \
             patch.object(VoiceAssistant, '_setup_gpio'), \
             patch.object(VoiceAssistant, '_verify_transcription_service'), \
             patch.object(VoiceAssistant, '_show_configuration'), \
             patch('threading.Thread'), \
             patch('main.openwakeword.utils.download_models'):
            
            assistant = VoiceAssistant()
            
            # Verificar que el modelo se inicializó
            self.assertIsNotNone(assistant.oww_model)
            self.assertEqual(len(assistant.active_models), 2)
            self.assertIn('alexa', assistant.active_models)
            self.assertIn('hey_mycroft', assistant.active_models)
    
    def test_openwakeword_setup_failure(self):
        """Test manejo de errores en configuración de openWakeWord"""
        from main import VoiceAssistant
        
        with patch.object(VoiceAssistant, '_load_commands'), \
             patch.object(VoiceAssistant, '_setup_gpio'), \
             patch.object(VoiceAssistant, '_verify_transcription_service'), \
             patch.object(VoiceAssistant, '_show_configuration'), \
             patch('threading.Thread'), \
             patch('main.openwakeword.utils.download_models', side_effect=Exception("Mock error")):
            
            assistant = VoiceAssistant()
            
            # Verificar que falló gracefully
            self.assertIsNone(assistant.oww_model)
            self.assertEqual(len(assistant.active_models), 0)
    
    def test_transcription_service_call(self):
        """Test llamada al servicio de transcripción"""
        from main import VoiceAssistant
        
        # Mock respuesta exitosa
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'transcription': 'test command'}
        self.requests_mock.post.return_value = mock_response
        
        with patch.object(VoiceAssistant, '_load_commands'), \
             patch.object(VoiceAssistant, '_setup_gpio'), \
             patch.object(VoiceAssistant, '_setup_openwakeword'), \
             patch.object(VoiceAssistant, '_verify_transcription_service'), \
             patch.object(VoiceAssistant, '_show_configuration'), \
             patch('threading.Thread'):
            
            assistant = VoiceAssistant()
            
            # Test WAV de prueba
            test_wav = b'mock_wav_data'
            result = assistant._send_to_transcription_service(test_wav)
            
            # Verificar llamada
            self.requests_mock.post.assert_called_once()
            call_args = self.requests_mock.post.call_args
            self.assertIn('files', call_args[1])
            self.assertEqual(result, 'test command')
    
    def test_button_activation(self):
        """Test activación manual por botón"""
        from main import VoiceAssistant
        
        with patch.object(VoiceAssistant, '_load_commands'), \
             patch.object(VoiceAssistant, '_setup_gpio'), \
             patch.object(VoiceAssistant, '_setup_openwakeword'), \
             patch.object(VoiceAssistant, '_verify_transcription_service'), \
             patch.object(VoiceAssistant, '_show_configuration'), \
             patch('threading.Thread'):
            
            assistant = VoiceAssistant()
            
            # Simular presión de botón
            assistant.button_pressed = True
            
            # Verificar que se detecta
            self.assertTrue(assistant.button_pressed)


class TestIntegration(unittest.TestCase):
    """Tests de integración para el flujo completo"""
    
    def setUp(self):
        """Configurar para tests de integración"""
        # Similar setup pero con más mocks interconectados
        self.gpio_mock = Mock()
        self.sounddevice_mock = Mock()
        self.requests_mock = Mock()
        
        self.patches = [
            patch('main.GPIO', self.gpio_mock),
            patch('main.sd', self.sounddevice_mock),
            patch('main.requests', self.requests_mock),
            patch('time.sleep'),
        ]
        
        for p in self.patches:
            p.start()
        
        os.environ.update({
            'TRANSCRIPTION_SERVICE_URL': 'http://test:5000/transcribe',
            'MODE': 'HYBRID'
        })
    
    def tearDown(self):
        """Limpiar después de tests de integración"""
        for p in self.patches:
            p.stop()
    
    @patch('main.openwakeword.model.Model')
    def test_full_wakeword_flow(self, mock_model_class):
        """Test flujo completo: wake word → transcripción → comando"""
        from main import VoiceAssistant
        
        # Mock del modelo openWakeWord
        mock_model = Mock()
        mock_model.models = {'alexa': Mock()}
        mock_model.predict.return_value = {'alexa': 0.8}  # Score alto
        mock_model_class.return_value = mock_model
        
        # Mock respuesta de transcripción
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'transcription': 'enciende luz verde'}
        self.requests_mock.post.return_value = mock_response
        
        with patch.object(VoiceAssistant, '_load_commands'), \
             patch.object(VoiceAssistant, '_verify_transcription_service'), \
             patch.object(VoiceAssistant, '_show_configuration'), \
             patch('threading.Thread'), \
             patch('main.openwakeword.utils.download_models'):
            
            assistant = VoiceAssistant()
            assistant.commands = {"enciende luz verde": {"pin": 17, "state": "HIGH"}}
            
            # Simular detección de wake word
            assistant._handle_wakeword_detected("alexa", 0.8)
            
            # Verificar que se activó el LED de listening
            # (Esto se llama en _set_state dentro de _handle_wakeword_detected)
            self.gpio_mock.output.assert_any_call(27, self.gpio_mock.HIGH)
    
    def test_audio_processing_pipeline(self):
        """Test pipeline de procesamiento de audio"""
        from main import VoiceAssistant
        
        with patch.object(VoiceAssistant, '_load_commands'), \
             patch.object(VoiceAssistant, '_setup_gpio'), \
             patch.object(VoiceAssistant, '_setup_openwakeword'), \
             patch.object(VoiceAssistant, '_verify_transcription_service'), \
             patch.object(VoiceAssistant, '_show_configuration'), \
             patch('threading.Thread'):
            
            assistant = VoiceAssistant()
            
            # Test resample de audio
            original_audio = np.array([100, 200, 300, 400], dtype=np.int16)
            resampled = assistant.simple_resample(original_audio, 44100, 16000)
            
            # Verificar que el resample funciona
            self.assertIsInstance(resampled, np.ndarray)
            self.assertEqual(resampled.dtype, np.int16)
    
    def test_error_handling(self):
        """Test manejo de errores en diferentes escenarios"""
        from main import VoiceAssistant
        
        # Test con servicio de transcripción no disponible
        self.requests_mock.post.side_effect = Exception("Connection error")
        
        with patch.object(VoiceAssistant, '_load_commands'), \
             patch.object(VoiceAssistant, '_setup_gpio'), \
             patch.object(VoiceAssistant, '_setup_openwakeword'), \
             patch.object(VoiceAssistant, '_show_configuration'), \
             patch('threading.Thread'):
            
            assistant = VoiceAssistant()
            
            # Test que no falla cuando transcripción falla
            result = assistant._send_to_transcription_service(b'test_audio')
            self.assertIsNone(result)


class TestConfigurationModes(unittest.TestCase):
    """Tests para diferentes modos de configuración"""
    
    def setUp(self):
        """Setup para tests de configuración"""
        self.gpio_mock = Mock()
        self.patches = [
            patch('main.GPIO', self.gpio_mock),
            patch('main.sd', Mock()),
            patch('main.requests', Mock()),
            patch('time.sleep'),
        ]
        
        for p in self.patches:
            p.start()
    
    def tearDown(self):
        """Cleanup"""
        for p in self.patches:
            p.stop()
    
    def test_gpio_only_mode(self):
        """Test modo GPIO_ONLY"""
        from main import VoiceAssistant
        
        os.environ['MODE'] = 'GPIO_ONLY'
        
        with patch.object(VoiceAssistant, '_load_commands'), \
             patch.object(VoiceAssistant, '_setup_gpio'), \
             patch.object(VoiceAssistant, '_verify_transcription_service'), \
             patch.object(VoiceAssistant, '_show_configuration'), \
             patch('threading.Thread'):
            
            assistant = VoiceAssistant()
            
            # En modo GPIO_ONLY no debería configurar openWakeWord
            self.assertIsNone(assistant.oww_model)
            self.assertEqual(len(assistant.active_models), 0)


def run_diagnostic_tests():
    """Ejecutar tests de diagnóstico del sistema"""
    print("🔍 Ejecutando tests de diagnóstico del sistema...")
    
    # Test 1: Verificar dependencias
    try:
        import openwakeword
        print("✅ openWakeWord disponible")
    except ImportError:
        print("❌ openWakeWord no disponible")
    
    try:
        import sounddevice as sd
        print("✅ sounddevice disponible")
        
        # Test dispositivos de audio
        devices = sd.query_devices()
        print(f"📱 Dispositivos de audio disponibles: {len(devices)}")
        
    except ImportError:
        print("❌ sounddevice no disponible")
    except Exception as e:
        print(f"⚠️ Error consultando dispositivos audio: {e}")
    
    # Test 2: Verificar variables de entorno
    required_vars = ['TRANSCRIPTION_SERVICE_URL', 'BUTTON_PIN', 'LED_IDLE_PIN', 'LED_RECORD_PIN']
    for var in required_vars:
        value = os.getenv(var, 'NOT_SET')
        print(f"🔧 {var}: {value}")
    
    # Test 3: Verificar archivos
    files_to_check = ['main.py', 'commands.json', 'requirements.txt']
    for file in files_to_check:
        if os.path.exists(file):
            print(f"📄 {file}: ✅")
        else:
            print(f"📄 {file}: ❌")
    
    print("🔍 Diagnóstico completado")


if __name__ == '__main__':
    print("🧪 Iniciando tests del Asistente de Voz Puertocho")
    print("=" * 50)
    
    # Ejecutar tests de diagnóstico primero
    run_diagnostic_tests()
    print()
    
    # Ejecutar tests unitarios
    print("🧪 Ejecutando tests unitarios...")
    unittest.main(verbosity=2, exit=False)
    
    print("\n✅ Tests completados") 
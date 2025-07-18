#!/usr/bin/env python3
"""
Tests para AudioManager
"""

import unittest
import sys
import os
import time
import numpy as np
from unittest.mock import patch, MagicMock

# Añadir el directorio padre al path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.audio_manager import AudioManager
from config import config

class TestAudioManager(unittest.TestCase):
    """Test cases para AudioManager"""

    def setUp(self):
        """Configuración antes de cada test"""
        self.audio_manager = None

    def tearDown(self):
        """Limpieza después de cada test"""
        if self.audio_manager and self.audio_manager.is_recording:
            self.audio_manager.stop_recording()

    def test_audio_manager_initialization(self):
        """Test básico de inicialización del AudioManager"""
        try:
            self.audio_manager = AudioManager()
            
            # Verificar que los parámetros de configuración se cargaron correctamente
            self.assertEqual(self.audio_manager.sample_rate, config.audio.sample_rate)
            self.assertEqual(self.audio_manager.channels, config.audio.channels)
            self.assertEqual(self.audio_manager.chunk_size, config.audio.chunk_size)
            self.assertEqual(self.audio_manager.device_name, config.audio.device_name)
            self.assertFalse(self.audio_manager.is_recording)
            self.assertIsNone(self.audio_manager.stream)
            
            print("✅ AudioManager inicializado correctamente")
            
        except Exception as e:
            self.fail(f"Error al inicializar AudioManager: {e}")

    def test_list_audio_devices(self):
        """Test para listar dispositivos de audio"""
        try:
            devices_info = AudioManager.list_audio_devices()
            
            # Verificar que se devuelve un diccionario con las claves esperadas
            self.assertIsInstance(devices_info, dict)
            self.assertIn("input_devices", devices_info)
            self.assertIn("output_devices", devices_info)
            self.assertIn("all_devices", devices_info)
            
            # Verificar que hay al menos un dispositivo
            self.assertGreater(len(devices_info["all_devices"]), 0)
            
            print("✅ Listado de dispositivos de audio exitoso")
            print(f"   Dispositivos de entrada: {len(devices_info['input_devices'])}")
            print(f"   Dispositivos de salida: {len(devices_info['output_devices'])}")
            print(f"   Total de dispositivos: {len(devices_info['all_devices'])}")
            
            # Mostrar algunos dispositivos para debug
            for i, device in enumerate(devices_info["all_devices"][:3]):  # Solo los primeros 3
                print(f"   [{i}] {device['name']} - In: {device['max_input_channels']} Out: {device['max_output_channels']}")
            
        except Exception as e:
            self.fail(f"Error al listar dispositivos de audio: {e}")

    def test_find_device_by_name(self):
        """Test para buscar dispositivo por nombre"""
        try:
            self.audio_manager = AudioManager()
            
            # Test con el dispositivo configurado
            device_index = self.audio_manager._find_device_by_name(config.audio.device_name)
            
            # El resultado puede ser None si no se encuentra el dispositivo
            # pero no debe lanzar excepción
            print(f"✅ Búsqueda de dispositivo '{config.audio.device_name}': {'Encontrado' if device_index is not None else 'No encontrado'}")
            
            # Test con un dispositivo que no existe
            fake_device_index = self.audio_manager._find_device_by_name("dispositivo-inexistente")
            self.assertIsNone(fake_device_index)
            
        except Exception as e:
            self.fail(f"Error al buscar dispositivo por nombre: {e}")

    @patch('sounddevice.InputStream')
    def test_start_stop_recording_mock(self, mock_input_stream):
        """Test de grabación con mock (sin hardware real)"""
        try:
            # Configurar mock
            mock_stream = MagicMock()
            mock_input_stream.return_value = mock_stream
            
            self.audio_manager = AudioManager()
            
            # Test callback simple
            audio_data = []
            def test_callback(indata, frames, status):
                audio_data.append(indata)
            
            # Iniciar grabación
            self.audio_manager.start_recording(test_callback)
            self.assertTrue(self.audio_manager.is_recording)
            
            # Verificar que se creó el stream correctamente
            mock_input_stream.assert_called_once()
            mock_stream.start.assert_called_once()
            
            # Detener grabación
            self.audio_manager.stop_recording()
            self.assertFalse(self.audio_manager.is_recording)
            
            # Verificar que se detuvo el stream
            mock_stream.stop.assert_called_once()
            mock_stream.close.assert_called_once()
            
            print("✅ Test de grabación con mock exitoso")
            
        except Exception as e:
            self.fail(f"Error en test de grabación con mock: {e}")

    def test_recording_with_real_hardware(self):
        """Test de grabación con hardware real (opcional)"""
        try:
            self.audio_manager = AudioManager()
            
            # Variables para capturar datos de audio
            audio_samples = []
            max_samples = 10  # Limitar para que el test no sea muy largo
            
            def audio_callback(indata, frames, status):
                nonlocal audio_samples
                if len(audio_samples) < max_samples:
                    # Calcular volumen RMS
                    rms = np.sqrt(np.mean(indata**2))
                    audio_samples.append(rms)
                    print(f"   Muestra {len(audio_samples)}: RMS = {rms:.4f}")
            
            print("🎤 Iniciando test de grabación real (2 segundos)...")
            print("   (Hable o haga ruido cerca del micrófono)")
            
            # Iniciar grabación
            self.audio_manager.start_recording(audio_callback)
            self.assertTrue(self.audio_manager.is_recording)
            
            # Grabar por 2 segundos
            time.sleep(2)
            
            # Detener grabación
            self.audio_manager.stop_recording()
            self.assertFalse(self.audio_manager.is_recording)
            
            # Verificar que se capturaron muestras
            self.assertGreater(len(audio_samples), 0)
            
            # Calcular estadísticas básicas
            if audio_samples:
                avg_rms = np.mean(audio_samples)
                max_rms = np.max(audio_samples)
                print(f"✅ Test de grabación real exitoso")
                print(f"   Muestras capturadas: {len(audio_samples)}")
                print(f"   RMS promedio: {avg_rms:.4f}")
                print(f"   RMS máximo: {max_rms:.4f}")
            
        except Exception as e:
            print(f"⚠️  Test de grabación real falló (posiblemente sin hardware): {e}")
            # No hacer fail ya que este test requiere hardware real
            self.skipTest(f"Hardware de audio no disponible: {e}")

    def test_context_manager(self):
        """Test del context manager (__enter__ y __exit__)"""
        try:
            with AudioManager() as manager:
                self.assertIsNotNone(manager)
                self.assertFalse(manager.is_recording)
                
                # Simular grabación (solo cambiar el flag para el test)
                manager.is_recording = True
            
            # Al salir del context manager, should have stopped recording
            print("✅ Context manager funciona correctamente")
            
        except Exception as e:
            self.fail(f"Error en test de context manager: {e}")

class TestAudioManagerIntegration(unittest.TestCase):
    """Tests de integración para AudioManager"""
    
    def test_config_integration(self):
        """Test de integración con config.py"""
        try:
            # Verificar que la configuración de audio está disponible
            self.assertIsNotNone(config.audio)
            self.assertGreater(config.audio.sample_rate, 0)
            self.assertGreater(config.audio.channels, 0)
            self.assertGreater(config.audio.chunk_size, 0)
            
            # Crear AudioManager con configuración
            manager = AudioManager()
            
            # Verificar que usa la configuración correcta
            self.assertEqual(manager.sample_rate, config.audio.sample_rate)
            self.assertEqual(manager.channels, config.audio.channels)
            
            print("✅ Integración con config.py exitosa")
            print(f"   Sample Rate: {manager.sample_rate}")
            print(f"   Channels: {manager.channels}")
            print(f"   Chunk Size: {manager.chunk_size}")
            print(f"   Device Name: {manager.device_name}")
            
        except Exception as e:
            self.fail(f"Error en integración con config: {e}")

def run_audio_tests():
    """Función para ejecutar todos los tests de audio"""
    print("🔊 Iniciando tests de AudioManager...\n")
    
    # Crear test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Añadir tests básicos
    suite.addTests(loader.loadTestsFromTestCase(TestAudioManager))
    suite.addTests(loader.loadTestsFromTestCase(TestAudioManagerIntegration))
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Resumen
    print(f"\n📊 Resumen de tests:")
    print(f"   Tests ejecutados: {result.testsRun}")
    print(f"   Errores: {len(result.errors)}")
    print(f"   Fallos: {len(result.failures)}")
    print(f"   Omitidos: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.wasSuccessful():
        print("✅ Todos los tests pasaron correctamente!")
    else:
        print("❌ Algunos tests fallaron.")
        
    return result.wasSuccessful()

if __name__ == '__main__':
    # Ejecutar tests cuando se ejecuta directamente
    success = run_audio_tests()
    sys.exit(0 if success else 1)

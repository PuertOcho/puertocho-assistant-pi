#!/usr/bin/env python3
"""
Test script para demostrar las nuevas funcionalidades de la Fase 3.

Este script prueba:
1. AudioProcessor unificado
2. ButtonHandler mejorado con callbacks múltiples
3. LEDController con feedback de audio y transiciones
4. Integración entre componentes
"""

import sys
import os
import time
import threading
import numpy as np
import logging
from pathlib import Path

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Añadir el path del proyecto
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "app"))

# Configurar variable de entorno para logs locales
os.environ['LOG_DIR'] = str(project_root / "app" / "logs")

# Crear logger simple para la demo
demo_logger = logging.getLogger("fase3_demo")

class Fase3Demo:
    """Demostración de las funcionalidades de la Fase 3"""
    
    def __init__(self):
        self.logger = demo_logger
        self.setup_components()
        self.demo_running = False
        
    def setup_components(self):
        """Configurar componentes para la demo"""
        self.logger.info("Configurando componentes para la demo...")
        
        try:
            # Importar componentes
            from utils.audio_processor import AudioProcessor, AudioProcessorFactory, ProcessingConfig
            from core.button_handler import ButtonHandler, ButtonEvent, ButtonEventData
            from core.led_controller import LEDController, LEDState, LEDColor
            
            # Guardar referencias a las clases
            self.AudioProcessor = AudioProcessor
            self.AudioProcessorFactory = AudioProcessorFactory
            self.ProcessingConfig = ProcessingConfig
            self.ButtonHandler = ButtonHandler
            self.ButtonEvent = ButtonEvent
            self.ButtonEventData = ButtonEventData
            self.LEDController = LEDController
            self.LEDState = LEDState
            self.LEDColor = LEDColor
            
            # 1. AudioProcessor unificado
            self.audio_processor = self.AudioProcessorFactory.create_for_wake_word()
            
            # 2. ButtonHandler mejorado
            self.button_handler = self.ButtonHandler(simulate=True)
            self.setup_button_callbacks()
            
            # 3. LEDController con nuevas funcionalidades
            self.led_controller = self.LEDController(simulate=True)
            self.setup_led_audio_callbacks()
            
            self.logger.info("Componentes configurados correctamente")
            
        except Exception as e:
            self.logger.error(f"Error configurando componentes: {e}")
            raise
    
    def setup_button_callbacks(self):
        """Configurar callbacks del botón con diferentes prioridades"""
        
        # Callback de alta prioridad para pulsaciones largas
        def high_priority_long_press(event):
            self.logger.info(f"🔴 HIGH PRIORITY: Pulsación larga detectada - {event.press_duration:.2f}s")
            self.led_controller.set_state(self.LEDState.ERROR)
        
        # Callback de prioridad media para doble click
        def medium_priority_double_click(event):
            self.logger.info(f"🟡 MEDIUM PRIORITY: Doble click detectado")
            self.led_controller.set_state(self.LEDState.PROCESSING)
        
        # Callback de baja prioridad para pulsaciones cortas
        def low_priority_short_press(event):
            self.logger.info(f"🟢 LOW PRIORITY: Pulsación corta - {event.click_count} clicks")
            self.led_controller.set_state(self.LEDState.LISTENING)
        
        # Callback para cambios de estado
        def state_change_callback(event):
            state = "PRESIONADO" if event.is_pressed else "LIBERADO"
            self.logger.info(f"📱 ESTADO: Botón {state}")
        
        # Registrar callbacks con prioridades
        self.button_handler.register_callback(
            self.ButtonEvent.LONG_PRESS, high_priority_long_press, 
            priority=100, name="emergency_stop"
        )
        
        self.button_handler.register_callback(
            self.ButtonEvent.DOUBLE_CLICK, medium_priority_double_click,
            priority=50, name="processing_trigger"
        )
        
        self.button_handler.register_callback(
            self.ButtonEvent.SHORT_PRESS, low_priority_short_press,
            priority=10, name="basic_interaction"
        )
        
        self.button_handler.register_state_callback(
            state_change_callback, priority=5, name="state_monitor"
        )
        
        self.logger.info("Callbacks del botón configurados")
    
    def setup_led_audio_callbacks(self):
        """Configurar callbacks de audio para LEDs"""
        
        def audio_level_visualizer(level: float, peak: float):
            """Visualizar nivel de audio en LEDs"""
            # Solo procesar si el nivel es significativo
            if level > 0.1:
                self.led_controller.pulse_with_audio_level(
                    level, peak, self.LEDColor(0, 255, 255)  # Cyan
                )
        
        self.led_controller.register_audio_callback(audio_level_visualizer)
        self.logger.info("Callbacks de audio configurados")
    
    def demo_audio_processor(self):
        """Demostrar AudioProcessor unificado"""
        self.logger.info("=== DEMO: AudioProcessor Unificado ===")
        
        # Simular diferentes tipos de audio
        test_audio_configs = [
            ("Wake Word Detection", self.AudioProcessorFactory.create_for_wake_word()),
            ("Audio Recording", self.AudioProcessorFactory.create_for_recording()),
            ("Audio Playback", self.AudioProcessorFactory.create_for_playback())
        ]
        
        for name, processor in test_audio_configs:
            self.logger.info(f"Probando configuración: {name}")
            
            # Generar audio sintético
            sample_rate = processor.config.input_sample_rate
            duration = 0.5  # 500ms
            samples = int(sample_rate * duration)
            
            # Generar tono de prueba
            frequency = 440  # La4
            t = np.linspace(0, duration, samples)
            audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)
            
            # Procesar audio
            start_time = time.time()
            processed = processor.process_chunk(audio_data)
            process_time = (time.time() - start_time) * 1000
            
            if processed is not None:
                self.logger.info(f"  ✅ Procesado en {process_time:.2f}ms")
                
                # Obtener métricas
                metrics = processor.get_metrics()
                self.logger.info(f"  � Buffer stats: {metrics['buffer_stats']}")
                self.logger.info(f"  � Samples procesados: {metrics['total_samples_processed']}")
            else:
                self.logger.error(f"  ❌ Error en procesamiento")
            
            # Limpiar para siguiente prueba
            processor.clear_buffers()
            time.sleep(0.5)
    
    def demo_button_handler(self):
        """Demostrar ButtonHandler mejorado"""
        self.logger.info("=== DEMO: ButtonHandler Mejorado ===")
        
        # Mostrar estado inicial
        status = self.button_handler.get_status()
        self.logger.info(f"Estado inicial del botón: {status['is_pressed']}")
        self.logger.info(f"Callbacks registrados: {len(status['callbacks_registered'])}")
        
        # Simular diferentes tipos de interacciones
        interactions = [
            ("Pulsación corta", lambda: self.button_handler.simulate_button_press(0.1)),
            ("Pulsación larga", lambda: self.button_handler.simulate_button_press(2.5)),
            ("Doble click", lambda: self.button_handler.simulate_double_click()),
            ("Triple click", lambda: self.button_handler.simulate_triple_click())
        ]
        
        for name, action in interactions:
            self.logger.info(f"Simulando: {name}")
            action()
            time.sleep(1.0)  # Esperar para que se procesen eventos
        
        # Demostrar consulta de estado en tiempo real
        self.logger.info("Demostrando consulta de estado en tiempo real...")
        self.button_handler.simulate_button_press(3.0)  # Pulsación de 3 segundos
        
        # Monitorear durante la pulsación
        for i in range(5):
            time.sleep(0.6)
            is_pressed = self.button_handler.is_pressed()
            duration = self.button_handler.get_press_duration()
            self.logger.info(f"  Estado: {'PRESIONADO' if is_pressed else 'LIBERADO'}, Duración: {duration:.1f}s")
    
    def demo_led_controller(self):
        """Demostrar LEDController con nuevas funcionalidades"""
        self.logger.info("=== DEMO: LEDController con Feedback de Audio ===")
        
        # 1. Demostrar transiciones suaves
        self.logger.info("Demostrando transiciones suaves...")
        states_with_transitions = [
            (self.LEDState.IDLE, "fade", 1.0),
            (self.LEDState.LISTENING, "slide", 0.8),
            (self.LEDState.PROCESSING, "fade", 0.5),
            (self.LEDState.SPEAKING, "slide", 0.7),
        ]
        
        for state, transition_type, duration in states_with_transitions:
            self.logger.info(f"  Transición a {state.value} ({transition_type}, {duration}s)")
            pattern = self.led_controller._get_pattern_for_state(state)
            self.led_controller.set_pattern_with_transition(
                pattern, duration, transition_type, priority=80
            )
            time.sleep(duration + 0.5)
        
        # 2. Demostrar feedback de audio
        self.logger.info("Demostrando feedback de audio...")
        
        # Simular niveles de audio variables
        for i in range(20):
            # Generar nivel de audio sintético
            t = i * 0.1
            audio_level = (np.sin(t * 2) + 1) * 0.5  # 0 a 1
            peak_level = audio_level * 1.2 if audio_level > 0.7 else audio_level
            
            self.led_controller.pulse_with_audio_level(audio_level, peak_level)
            self.led_controller._notify_audio_callbacks(audio_level, peak_level)
            
            time.sleep(0.1)
        
        # 3. Demostrar visualización de espectro
        self.logger.info("Demostrando visualización de espectro...")
        
        for i in range(10):
            # Simular bins de frecuencia
            freq_bins = [
                np.random.random() * 0.8,  # Graves
                np.random.random() * 0.6,  # Medios
                np.random.random() * 0.4   # Agudos
            ]
            
            self.led_controller.visualize_spectrum(freq_bins)
            time.sleep(0.2)
        
        # 4. Demostrar sistema de cola de animaciones
        self.logger.info("Demostrando cola de animaciones...")
        
        # Añadir múltiples animaciones con diferentes prioridades
        colors = [self.LEDColor(255, 0, 0), self.LEDColor(0, 255, 0), self.LEDColor(0, 0, 255)]
        
        for i, color in enumerate(colors):
            from core.led_controller import SolidPattern
            pattern = SolidPattern([color])
            self.led_controller.queue_animation(pattern, priority=i*10, interrupting=True)
            time.sleep(0.3)        # Mostrar estado de animaciones
        status = self.led_controller.get_animation_status()
        self.logger.info(f"Estado de animaciones: {status}")
    
    def run_integrated_demo(self):
        """Ejecutar demo integrada de todos los componentes"""
        self.logger.info("=== DEMO INTEGRADA: Todos los Componentes ===")
        
        self.demo_running = True
        
        # Iniciar componentes
        self.button_handler.start()
        self.led_controller.start_animation()
        self.audio_processor.start_continuous_processing()
        
        try:
            # Estado inicial
            self.led_controller.set_state(self.LEDState.IDLE)
            
            # Simular secuencia de interacciones
            interactions = [
                (2, "Pulsación corta -> Listening", 
                 lambda: self.button_handler.simulate_button_press(0.1)),
                
                (3, "Simulando procesamiento de audio",
                 self._simulate_audio_processing),
                
                (2, "Doble click -> Processing", 
                 lambda: self.button_handler.simulate_double_click()),
                
                (3, "Visualización de espectro",
                 self._simulate_spectrum_visualization),
                
                (2, "Pulsación larga -> Error", 
                 lambda: self.button_handler.simulate_button_press(2.0)),
                
                (2, "Volviendo a estado inicial",
                 lambda: self.led_controller.set_pattern_with_transition(
                     self.led_controller._get_pattern_for_state(self.LEDState.IDLE),
                     transition_duration=1.0
                 ))
            ]
            
            for duration, description, action in interactions:
                self.logger.info(f"🎬 {description}")
                action()
                time.sleep(duration)
            
        finally:
            # Limpiar
            self.demo_running = False
            self.audio_processor.stop_continuous_processing()
            self.led_controller.stop_animation()
            self.button_handler.stop()
    
    def _simulate_audio_processing(self):
        """Simular procesamiento de audio con visualización"""
        for i in range(15):
            # Generar datos de audio sintéticos
            level = np.random.random() * 0.8
            peak = level * (1.1 + np.random.random() * 0.3)
            
            # Actualizar visualización de LEDs
            self.led_controller.pulse_with_audio_level(level, peak)
            
            # Simular procesamiento
            sample_audio = np.random.random(1024).astype(np.float32) * level
            self.audio_processor.process_chunk(sample_audio)
            
            time.sleep(0.1)
    
    def _simulate_spectrum_visualization(self):
        """Simular visualización de espectro"""
        for i in range(20):
            # Generar espectro sintético
            freq_bins = [
                np.sin(i * 0.5) * 0.5 + 0.5,      # Graves
                np.sin(i * 0.3 + 1) * 0.4 + 0.4,  # Medios  
                np.sin(i * 0.7 + 2) * 0.3 + 0.3   # Agudos
            ]
            
            self.led_controller.visualize_spectrum(freq_bins)
            time.sleep(0.15)
    
    def run_all_demos(self):
        """Ejecutar todas las demos"""
        self.logger.info("🚀 Iniciando demostración completa de Fase 3")
        
        try:
            # Demos individuales
            self.demo_audio_processor()
            time.sleep(1)
            
            self.demo_button_handler()
            time.sleep(1)
            
            self.demo_led_controller()
            time.sleep(1)
            
            # Demo integrada
            self.run_integrated_demo()
            
            self.logger.info("✅ Demostración de Fase 3 completada exitosamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error en la demostración: {e}")
            raise
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Limpiar recursos"""
        self.logger.info("Limpiando recursos...")
        
        if hasattr(self, 'audio_processor'):
            self.audio_processor.stop_continuous_processing()
        
        if hasattr(self, 'button_handler'):
            self.button_handler.stop()
        
        if hasattr(self, 'led_controller'):
            self.led_controller.cleanup()


def main():
    """Función principal"""
    print("=" * 60)
    print("🎯 DEMOSTRACIÓN DE FASE 3 - NUEVAS FUNCIONALIDADES")
    print("=" * 60)
    print()
    print("Esta demo demuestra:")
    print("1. 🎵 AudioProcessor unificado")
    print("2. 🔘 ButtonHandler con callbacks múltiples")
    print("3. 💡 LEDController con feedback de audio y transiciones")
    print("4. 🔗 Integración entre todos los componentes")
    print()
    
    demo = Fase3Demo()
    
    try:
        demo.run_all_demos()
        print("\n🎉 ¡Demo completada exitosamente!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrumpida por el usuario")
        
    except Exception as e:
        print(f"\n❌ Error en la demo: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        demo.cleanup()


if __name__ == "__main__":
    main()

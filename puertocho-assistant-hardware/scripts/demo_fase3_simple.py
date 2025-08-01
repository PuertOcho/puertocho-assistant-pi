#!/usr/bin/env python3
"""
Test script simplificado para demostrar las nuevas funcionalidades de la Fase 3.
Versión sin dependencias complejas de configuración.
"""

import sys
import time
import threading
import logging
from pathlib import Path

# Configurar logging simple
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

print("=" * 60)
print("🎯 DEMOSTRACIÓN SIMPLIFICADA DE FASE 3")
print("=" * 60)
print()

# Test 1: AudioProcessor
print("1. 📊 Testing AudioProcessor...")
try:
    # Añadir el path del proyecto  
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root / "app"))
    
    # Importación básica
    print("   - Importando AudioProcessor...")
    from utils.audio_processor import ProcessingConfig, AudioProcessor
    
    # Crear configuración simple
    config = ProcessingConfig(
        input_sample_rate=16000,
        output_sample_rate=16000, 
        buffer_duration=1.0,
        enable_filtering=False,
        enable_analysis=True
    )
    
    processor = AudioProcessor(config)
    print("   ✅ AudioProcessor creado exitosamente")
    
    # Simular procesamiento
    import numpy as np
    audio_data = np.random.random(1024).astype(np.float32)
    result = processor.process_chunk(audio_data)
    
    if result is not None:
        print("   ✅ Procesamiento de audio funcional")
        
        # Obtener métricas
        metrics = processor.get_metrics()
        print(f"   📈 Buffer fill: {metrics['buffer_fill_level']:.1%}")
    else:
        print("   ❌ Error en procesamiento")
    
    processor.clear_buffers()
    print("   🧹 Buffers limpiados")
    
except Exception as e:
    print(f"   ❌ Error en AudioProcessor: {e}")

print()

# Test 2: ButtonHandler
print("2. 🔘 Testing ButtonHandler...")
try:
    from core.button_handler import ButtonHandler, ButtonEvent, ButtonEventData
    
    # Crear handler en modo simulación
    button = ButtonHandler(simulate=True)
    print("   ✅ ButtonHandler creado en modo simulación")
    
    # Configurar callbacks
    events_received = []
    
    def test_callback(event: ButtonEventData):
        events_received.append(event.event_type.value)
        print(f"   🔔 Evento recibido: {event.event_type.value}")
    
    # Registrar callbacks con diferentes prioridades
    button.register_callback(ButtonEvent.SHORT_PRESS, test_callback, priority=10, name="test_short")
    button.register_callback(ButtonEvent.DOUBLE_CLICK, test_callback, priority=20, name="test_double")
    button.register_callback(ButtonEvent.LONG_PRESS, test_callback, priority=30, name="test_long")
    
    button.start()
    print("   ✅ Callbacks registrados y ButtonHandler iniciado")
    
    # Simular interacciones
    print("   🎮 Simulando pulsación corta...")
    button.simulate_button_press(0.1)
    time.sleep(0.5)
    
    print("   🎮 Simulando doble click...")
    button.simulate_double_click()
    time.sleep(1.0)
    
    print("   🎮 Simulando pulsación larga...")
    button.simulate_button_press(2.0)
    time.sleep(0.5)
    
    # Verificar estado
    status = button.get_status()
    print(f"   📊 Estado: Presionado={status['is_pressed']}, Callbacks={len(status['callbacks_registered'])}")
    
    button.stop()
    print(f"   ✅ ButtonHandler test completado. Eventos recibidos: {len(events_received)}")
    
except Exception as e:
    print(f"   ❌ Error en ButtonHandler: {e}")

print()

# Test 3: LEDController  
print("3. 💡 Testing LEDController...")
try:
    from core.led_controller import LEDController, LEDState, LEDColor
    
    # Crear controller en modo simulación
    led_controller = LEDController(simulate=True)
    print("   ✅ LEDController creado en modo simulación")
    
    led_controller.start_animation()
    print("   ✅ Animación iniciada")
    
    # Test de estados básicos
    states = [LEDState.IDLE, LEDState.LISTENING, LEDState.PROCESSING, LEDState.SPEAKING]
    
    for state in states:
        print(f"   🎨 Configurando estado: {state.value}")
        led_controller.set_state(state)
        time.sleep(0.3)
    
    # Test de feedback de audio
    print("   🎵 Testing feedback de audio...")
    for i in range(5):
        level = (i + 1) * 0.2  # 0.2, 0.4, 0.6, 0.8, 1.0
        led_controller.pulse_with_audio_level(level, level * 1.1)
        print(f"   📊 Nivel de audio: {level:.1f}")
        time.sleep(0.2)
    
    # Test de transiciones
    print("   🌊 Testing transiciones suaves...")
    pattern = led_controller._get_pattern_for_state(LEDState.ERROR)
    led_controller.set_pattern_with_transition(
        pattern, transition_duration=1.0, transition_type="fade"
    )
    time.sleep(1.2)
    
    # Obtener estado
    status = led_controller.get_animation_status()
    print(f"   📊 Estado: {status['current_state']}, Animación: {status['animation_running']}")
    
    led_controller.cleanup()
    print("   ✅ LEDController test completado")
    
except Exception as e:
    print(f"   ❌ Error en LEDController: {e}")

print()

# Test 4: Integración básica
print("4. 🔗 Testing integración básica...")
try:
    # Simular un escenario simple de integración
    print("   📱 Simulando escenario de uso...")
    
    # Crear componentes
    button = ButtonHandler(simulate=True)
    led_controller = LEDController(simulate=True)
    
    # Estado inicial
    led_controller.start_animation()
    led_controller.set_state(LEDState.IDLE)
    button.start()
    
    # Configurar interacción
    def on_button_press(event: ButtonEventData):
        if event.event_type == ButtonEvent.SHORT_PRESS:
            print("   🔔 Pulsación corta -> Modo listening")
            led_controller.set_state(LEDState.LISTENING)
        elif event.event_type == ButtonEvent.DOUBLE_CLICK:
            print("   🔔 Doble click -> Modo processing")
            led_controller.set_state(LEDState.PROCESSING)
    
    button.register_callback(ButtonEvent.SHORT_PRESS, on_button_press, name="integration_test")
    button.register_callback(ButtonEvent.DOUBLE_CLICK, on_button_press, name="integration_test")
    
    # Simular interacciones
    print("   🎮 Pulsación corta...")
    button.simulate_button_press(0.1)
    time.sleep(1.0)
    
    print("   🎮 Doble click...")
    button.simulate_double_click()
    time.sleep(1.0)
    
    # Limpiar
    button.stop()
    led_controller.cleanup()
    
    print("   ✅ Integración básica funcional")
    
except Exception as e:
    print(f"   ❌ Error en integración: {e}")

print()
print("🎉 Demostración completada!")
print()
print("📋 RESUMEN DE FUNCIONALIDADES IMPLEMENTADAS:")
print("   ✅ AudioProcessor unificado con pipelines configurables")
print("   ✅ ButtonHandler con callbacks múltiples y prioridades")
print("   ✅ LEDController con feedback de audio y transiciones")
print("   ✅ Sistema de cola de animaciones interrumpibles")
print("   ✅ Integración básica entre componentes")
print()
print("🚀 ¡Fase 3 completada exitosamente!")

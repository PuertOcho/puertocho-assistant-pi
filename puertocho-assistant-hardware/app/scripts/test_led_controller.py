#!/usr/bin/env python3
"""
Script de prueba para el controlador de LEDs APA102
Prueba únicamente la clase LEDController - no controla LEDs directamente
"""

import time
import sys
import argparse
import os
from pathlib import Path

# Agregar el directorio app al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.led_controller import LEDController, LEDState, LEDColor
from config import config

def test_basic_colors():
    """Prueba colores básicos usando LEDController"""
    print("🎨 Testing basic colors...")
    
    # Usar configuración por defecto
    with LEDController() as controller:
        colors = ['red', 'green', 'blue', 'yellow', 'white', 'purple', 'orange']
        
        for color_name in colors:
            color = controller.COLORS[color_name]
            print(f"  Setting color: {color_name}")
            controller.set_custom_color(color)
            time.sleep(1)
        
        print("  ✅ Basic colors test completed")

def test_states():
    """Prueba estados del asistente"""
    print("🤖 Testing assistant states...")
    
    with LEDController() as controller:
        states = [
            (LEDState.IDLE, "Idle (blue pulse)"),
            (LEDState.LISTENING, "Listening (green solid)"),
            (LEDState.PROCESSING, "Processing (yellow rotating)"),
            (LEDState.SPEAKING, "Speaking (white pulse)"),
            (LEDState.ERROR, "Error (red blink)"),
            (LEDState.OFF, "Off")
        ]
        
        for state, description in states:
            print(f"  {description}")
            controller.set_state(state)
            time.sleep(3)
        
        print("  ✅ States test completed")

def test_brightness():
    """Prueba control de brillo"""
    print("💡 Testing brightness control...")
    
    with LEDController() as controller:
        controller.set_custom_color(LEDColor(255, 255, 255))  # Blanco
        
        brightness_levels = [50, 100, 150, 200, 255]
        
        for brightness in brightness_levels:
            print(f"  Setting brightness: {brightness}")
            controller.set_brightness(brightness)
            time.sleep(1)
        
        print("  ✅ Brightness test completed")

def test_rainbow():
    """Prueba patrón arcoíris"""
    print("🌈 Testing rainbow pattern...")
    
    with LEDController() as controller:
        print("  Running rainbow pattern for 10 seconds...")
        controller.set_rainbow_pattern(duration=2.0)
        time.sleep(10)
        
        print("  ✅ Rainbow test completed")

def test_custom_patterns():
    """Prueba patrones personalizados"""
    print("✨ Testing custom patterns...")
    
    with LEDController() as controller:
        # Patrón personalizado: gradiente de azul a verde
        print("  Custom gradient pattern...")
        colors = [
            LEDColor(0, 0, 255),    # Azul
            LEDColor(0, 128, 128),  # Azul-verde
            LEDColor(0, 255, 0),    # Verde
        ]
        
        from core.led_controller import SolidPattern
        pattern = SolidPattern(colors)
        controller.set_pattern(pattern)
        time.sleep(3)
        
        print("  ✅ Custom patterns test completed")

def test_performance():
    """Prueba rendimiento"""
    print("⚡ Testing performance...")
    
    with LEDController() as controller:
        start_time = time.time()
        
        # Cambiar estados rápidamente
        for i in range(100):
            state = LEDState.IDLE if i % 2 == 0 else LEDState.PROCESSING
            controller.set_state(state)
            time.sleep(0.01)  # 10ms
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        print(f"  100 state changes in {elapsed:.2f}s ({100/elapsed:.1f} changes/sec)")
        print("  ✅ Performance test completed")

def test_error_handling():
    """Prueba manejo de errores"""
    print("🚨 Testing error handling...")
    
    with LEDController() as controller:
        try:
            # Probar valores inválidos
            controller.set_brightness(-1)
            print("  ❌ Should have raised ValueError for negative brightness")
        except ValueError:
            print("  ✅ Correctly handled negative brightness")
        
        try:
            controller.set_brightness(300)
            print("  ❌ Should have raised ValueError for brightness > 255")
        except ValueError:
            print("  ✅ Correctly handled brightness > 255")
        
        try:
            # Probar color inválido
            LEDColor(256, 0, 0)
            print("  ❌ Should have raised ValueError for color > 255")
        except ValueError:
            print("  ✅ Correctly handled color > 255")
        
        print("  ✅ Error handling test completed")

def test_controller_functionality():
    """Prueba funcionalidad completa del controlador"""
    print("🎮 Testing full LED Controller functionality...")
    
    with LEDController() as controller:
        print(f"  Using {'simulation' if controller.simulate else 'real hardware'} mode")
        print(f"  LEDs: {controller.num_leds}, Brightness: {controller.brightness}")
        print(f"  Animation speed: {config.led.animation_speed}s")
        # Probar estados básicos
        states = [
            (LEDState.IDLE, "Idle (blue pulse)"),
            (LEDState.LISTENING, "Listening (green solid)"),
            (LEDState.PROCESSING, "Processing (yellow rotating)"),
            (LEDState.SPEAKING, "Speaking (white pulse)"),
            (LEDState.ERROR, "Error (red blink)"),
            (LEDState.OFF, "Off")
        ]
        
        for state, description in states:
            print(f"  {description}")
            controller.set_state(state)
            time.sleep(2)
        
        # Probar patrón de prueba integrado
        print("  Running integrated test pattern...")
        controller.test_pattern(duration=5.0)
        
        print("  ✅ LED Controller functionality test completed")

def run_interactive_test():
    """Prueba interactiva usando solo LEDController"""
    print("🎮 Interactive LED test mode - Using LEDController only")
    print("Commands:")
    print("  1: Basic colors test")
    print("  2: States test")  
    print("  3: Brightness test")
    print("  4: Rainbow pattern")
    print("  5: Custom patterns")
    print("  6: Performance test")
    print("  7: Error handling test")
    print("  8: Full functionality test")
    print("  i: Set to IDLE")
    print("  l: Set to LISTENING")
    print("  p: Set to PROCESSING")
    print("  s: Set to SPEAKING")
    print("  e: Set to ERROR")
    print("  r: Red color")
    print("  g: Green color")
    print("  b: Blue color")
    print("  w: White color")
    print("  o: Turn off")
    print("  q: Quit")
    
    with LEDController() as controller:
        print(f"\nUsing {'simulation' if controller.simulate else 'real hardware'} mode")
        print(f"Configuration: {controller.num_leds} LEDs, brightness {controller.brightness}")
        print(f"Animation speed: {config.led.animation_speed}s\n")
        while True:
            try:
                command = input("\nEnter command: ").strip().lower()
                
                if command == 'q':
                    break
                elif command == '1':
                    test_basic_colors()
                elif command == '2':
                    test_states()
                elif command == '3':
                    test_brightness()
                elif command == '4':
                    test_rainbow()
                elif command == '5':
                    test_custom_patterns()
                elif command == '6':
                    test_performance()
                elif command == '7':
                    test_error_handling()
                elif command == '8':
                    test_controller_functionality()
                elif command == 'i':
                    print("  Setting to IDLE state")
                    controller.set_state(LEDState.IDLE)
                elif command == 'l':
                    print("  Setting to LISTENING state")
                    controller.set_state(LEDState.LISTENING)
                elif command == 'p':
                    print("  Setting to PROCESSING state")
                    controller.set_state(LEDState.PROCESSING)
                elif command == 's':
                    print("  Setting to SPEAKING state")
                    controller.set_state(LEDState.SPEAKING)
                elif command == 'e':
                    print("  Setting to ERROR state")
                    controller.set_state(LEDState.ERROR)
                elif command == 'r':
                    print("  Setting red color")
                    controller.set_custom_color(controller.COLORS['red'])
                elif command == 'g':
                    print("  Setting green color")
                    controller.set_custom_color(controller.COLORS['green'])
                elif command == 'b':
                    print("  Setting blue color")
                    controller.set_custom_color(controller.COLORS['blue'])
                elif command == 'w':
                    print("  Setting white color")
                    controller.set_custom_color(controller.COLORS['white'])
                elif command == 'o':
                    print("  Turning off")
                    controller.turn_off()
                else:
                    print("Unknown command")
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Test LED Controller")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Run in interactive mode")
    parser.add_argument("--colors", "-c", action="store_true",
                       help="Run basic colors test only")
    parser.add_argument("--states", "-s", action="store_true",
                       help="Run states test only")
    parser.add_argument("--brightness", "-b", action="store_true",
                       help="Run brightness test only")
    parser.add_argument("--rainbow", "-r", action="store_true",
                       help="Run rainbow pattern test only")
    parser.add_argument("--performance", "-p", action="store_true",
                       help="Run performance test only")
    parser.add_argument("--errors", "-e", action="store_true",
                       help="Run error handling test only")
    
    args = parser.parse_args()
    
    print("🔮 PuertoCho Assistant - LED Controller Test")
    print("=" * 50)
    
    if args.interactive:
        run_interactive_test()
    elif args.colors:
        test_basic_colors()
    elif args.states:
        test_states()
    elif args.brightness:
        test_brightness()
    elif args.rainbow:
        test_rainbow()
    elif args.performance:
        test_performance()
    elif args.errors:
        test_error_handling()
    else:
        # Ejecutar todas las pruebas
        success_count = 0
        total_tests = 7
        
        print("Running comprehensive LED Controller tests...")
        print()
        
        try:
            test_basic_colors()
            success_count += 1
        except Exception as e:
            print(f"❌ Basic colors test failed: {e}")
        print()
        
        try:
            test_states()
            success_count += 1
        except Exception as e:
            print(f"❌ States test failed: {e}")
        print()
        
        try:
            test_brightness()
            success_count += 1
        except Exception as e:
            print(f"❌ Brightness test failed: {e}")
        print()
        
        try:
            test_rainbow()
            success_count += 1
        except Exception as e:
            print(f"❌ Rainbow test failed: {e}")
        print()
        
        try:
            test_custom_patterns()
            success_count += 1
        except Exception as e:
            print(f"❌ Custom patterns test failed: {e}")
        print()
        
        try:
            test_performance()
            success_count += 1
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
        print()
        
        try:
            test_error_handling()
            success_count += 1
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
        print()
        
        print(f"🎉 Tests completed: {success_count}/{total_tests} successful")
        
        if success_count == total_tests:
            print("✅ All tests passed!")
        else:
            print("⚠️  Some tests failed - check logs for details")

if __name__ == "__main__":
    main()

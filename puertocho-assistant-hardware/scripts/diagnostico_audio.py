#!/usr/bin/env python3
"""
Diagnóstico de audio para el asistente Puertocho
Ayuda a identificar y solucionar problemas de input overflow
"""

import sounddevice as sd
import numpy as np
import time
import threading
import queue
import os
import json
from collections import deque

class AudioDiagnostic:
    def __init__(self):
        self.sample_rate = 16000
        self.overflow_count = 0
        self.total_callbacks = 0
        self.audio_queue = queue.Queue()
        self.running = False
        self.latency_history = deque(maxlen=100)
        
    def print_header(self, title):
        print("\n" + "="*60)
        print(f"🔧 {title}")
        print("="*60)
        
    def test_audio_devices(self):
        """Probar dispositivos de audio disponibles"""
        self.print_header("DISPOSITIVOS DE AUDIO DISPONIBLES")
        
        try:
            devices = sd.query_devices()
            print(f"📱 Dispositivos encontrados: {len(devices)}")
            
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    print(f"  [{i}] {device['name']} - {device['max_input_channels']} canales")
                    print(f"      Tasa: {device['default_samplerate']} Hz")
                    print(f"      Latencia: {device['default_low_input_latency']*1000:.1f}ms")
                    
        except Exception as e:
            print(f"❌ Error consultando dispositivos: {e}")
            
    def test_sample_rates(self):
        """Probar tasas de muestreo soportadas"""
        self.print_header("TASAS DE MUESTREO SOPORTADAS")
        
        rates = [8000, 16000, 22050, 44100, 48000]
        
        for rate in rates:
            try:
                test_stream = sd.RawInputStream(
                    samplerate=rate,
                    blocksize=512,
                    dtype='int16',
                    channels=1
                )
                test_stream.close()
                print(f"✅ {rate} Hz - Soportado")
            except Exception as e:
                print(f"❌ {rate} Hz - No soportado: {e}")
                
    def test_chunk_sizes(self):
        """Probar diferentes chunk sizes"""
        self.print_header("CHUNK SIZES ÓPTIMOS")
        
        chunk_sizes = [128, 256, 512, 1024, 2048, 4096]
        
        for chunk_size in chunk_sizes:
            try:
                test_stream = sd.RawInputStream(
                    samplerate=16000,
                    blocksize=chunk_size,
                    dtype='int16',
                    channels=1,
                    latency='low'
                )
                test_stream.close()
                latency_ms = (chunk_size / 16000) * 1000
                print(f"✅ {chunk_size} - Latencia: {latency_ms:.1f}ms")
            except Exception as e:
                print(f"❌ {chunk_size} - Error: {e}")
                
    def audio_callback(self, indata, frames, time, status):
        """Callback de audio para pruebas"""
        self.total_callbacks += 1
        
        if status:
            if 'input overflow' in str(status):
                self.overflow_count += 1
            print(f"⚠️ Audio status: {status}")
        
        # Calcular latencia
        latency_ms = (frames / self.sample_rate) * 1000
        self.latency_history.append(latency_ms)
        
        # Añadir audio a la cola
        if self.audio_queue.qsize() < 50:
            self.audio_queue.put(indata.copy())
            
    def test_real_time_audio(self, chunk_size=1024, duration=10):
        """Probar captura en tiempo real"""
        self.print_header(f"PRUEBA EN TIEMPO REAL (chunk_size={chunk_size})")
        
        self.overflow_count = 0
        self.total_callbacks = 0
        self.running = True
        
        print(f"🎤 Iniciando captura por {duration} segundos...")
        print("💡 Habla o haz ruido para probar")
        
        try:
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=chunk_size,
                dtype='int16',
                channels=1,
                callback=self.audio_callback,
                latency='low'
            ):
                # Monitorear en tiempo real
                start_time = time.time()
                while time.time() - start_time < duration:
                    time.sleep(1)
                    
                    elapsed = time.time() - start_time
                    overflow_rate = (self.overflow_count / max(self.total_callbacks, 1)) * 100
                    
                    print(f"⏱️ {elapsed:.0f}s - Callbacks: {self.total_callbacks}, "
                          f"Overflow: {self.overflow_count} ({overflow_rate:.1f}%)")
                    
        except Exception as e:
            print(f"❌ Error en captura: {e}")
            
        self.running = False
        
        # Estadísticas finales
        print("\n📊 ESTADÍSTICAS FINALES:")
        print(f"   Total callbacks: {self.total_callbacks}")
        print(f"   Overflow count: {self.overflow_count}")
        print(f"   Overflow rate: {(self.overflow_count / max(self.total_callbacks, 1)) * 100:.2f}%")
        
        if self.latency_history:
            avg_latency = sum(self.latency_history) / len(self.latency_history)
            print(f"   Latencia promedio: {avg_latency:.1f}ms")
            
    def generate_recommendations(self):
        """Generar recomendaciones basadas en las pruebas"""
        self.print_header("RECOMENDACIONES")
        
        print("📋 Configuración recomendada para .env:")
        print()
        
        if self.overflow_count > 0:
            print("🔧 Para resolver overflow:")
            print("   AUDIO_CHUNK_SIZE=2048  # Aumentar chunk size")
            print("   # O probar con 1024 si 2048 causa demasiada latencia")
            print()
            
        print("⚡ Optimizaciones generales:")
        print("   # Usar dispositivo específico si hay múltiples")
        print("   # ALSA_CARD=1")
        print("   # ALSA_DEVICE=0")
        print()
        print("   # Reducir carga del sistema")
        print("   # Cerrar aplicaciones innecesarias")
        print("   # Usar modo 'performance' del CPU")
        print()
        
        print("🐳 Optimizaciones Docker:")
        print("   # En docker-compose.yml:")
        print("   #   ulimits:")
        print("   #     rtprio: 99")
        print("   #     memlock: -1")
        
    def run_full_diagnostic(self):
        """Ejecutar diagnóstico completo"""
        print("🎯 DIAGNÓSTICO COMPLETO DE AUDIO - PUERTOCHO")
        print("Detectando problemas de input overflow...")
        
        self.test_audio_devices()
        self.test_sample_rates()
        self.test_chunk_sizes()
        
        # Pruebas en tiempo real
        self.test_real_time_audio(chunk_size=512, duration=5)
        self.test_real_time_audio(chunk_size=1024, duration=5)
        self.test_real_time_audio(chunk_size=2048, duration=5)
        
        self.generate_recommendations()
        
        print("\n🎉 Diagnóstico completado!")
        print("💡 Aplica las recomendaciones y reinicia el asistente")

def main():
    """Función principal"""
    try:
        diagnostic = AudioDiagnostic()
        diagnostic.run_full_diagnostic()
    except KeyboardInterrupt:
        print("\n🛑 Diagnóstico interrumpido por el usuario")
    except Exception as e:
        print(f"❌ Error durante el diagnóstico: {e}")
        
if __name__ == "__main__":
    main()

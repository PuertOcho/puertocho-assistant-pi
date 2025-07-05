#!/usr/bin/env python3
"""
🎤 Asistente Puertocho con Modelo Personalizado
Usa directamente nuestro modelo ONNX entrenado
"""

import os
import time
import queue
import threading
import numpy as np
import sounddevice as sd
import onnxruntime as ort
from pathlib import Path

class PuertochoAssistant:
    def __init__(self):
        self.model_path = Path('checkpoints/puertocho.onnx')
        self.threshold = 0.5
        self.sample_rate = 16000
        self.chunk_size = 1280  # 80ms chunks
        self.audio_buffer = []
        self.running = False
        
        # Cargar modelo ONNX
        print(f"🎯 Cargando modelo Puertocho desde {self.model_path}")
        self.session = ort.InferenceSession(str(self.model_path))
        print("✅ Modelo cargado exitosamente")
        
        # Buffer para audio
        self.audio_queue = queue.Queue()
        
    def audio_callback(self, indata, frames, time, status):
        """Callback para captura de audio"""
        if status:
            print(f"⚠️ Audio status: {status}")
        
        # Convertir a mono si es estéreo
        if len(indata.shape) > 1:
            audio_data = indata[:, 0]
        else:
            audio_data = indata.flatten()
            
        self.audio_queue.put(audio_data)
    
    def process_audio(self):
        """Procesar audio en tiempo real"""
        print("🎤 Iniciando procesamiento de audio...")
        
        while self.running:
            try:
                # Obtener chunk de audio
                chunk = self.audio_queue.get(timeout=1.0)
                
                # Añadir al buffer
                self.audio_buffer.extend(chunk)
                
                # Mantener buffer de 1 segundo (16000 samples)
                if len(self.audio_buffer) >= 16000:
                    # Tomar últimos 16000 samples
                    audio_window = np.array(self.audio_buffer[-16000:], dtype=np.float32)
                    
                    # Preparar input para el modelo
                    model_input = audio_window.reshape(1, -1)
                    
                    # Ejecutar inferencia
                    result = self.session.run(None, {'audio': model_input})
                    score = result[0][0][0]
                    
                    # Aplicar sigmoid para obtener probabilidad
                    probability = 1 / (1 + np.exp(-score))
                    
                    # Verificar detección
                    if probability > self.threshold:
                        print(f"🎉 ¡PUERTOCHO DETECTADO! Probabilidad: {probability:.3f}")
                        self.on_wake_word_detected()
                    
                    # Mostrar estado cada cierto tiempo
                    if len(self.audio_buffer) % (16000 * 5) == 0:  # Cada 5 segundos
                        print(f"🔊 Escuchando... Última probabilidad: {probability:.3f}")
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Error procesando audio: {e}")
    
    def on_wake_word_detected(self):
        """Acción cuando se detecta la wake word"""
        print("🗣️ ¡Hola! Soy Puertocho. ¿En qué puedo ayudarte?")
        # Aquí se puede integrar con el resto del sistema
        
    def start(self):
        """Iniciar el asistente"""
        print("🚀 Iniciando Asistente Puertocho...")
        print(f"📊 Threshold: {self.threshold}")
        print(f"🎵 Sample rate: {self.sample_rate} Hz")
        print("💡 Di 'Puertocho' para activar el asistente")
        print("🛑 Presiona Ctrl+C para salir")
        
        self.running = True
        
        # Iniciar hilo de procesamiento
        process_thread = threading.Thread(target=self.process_audio)
        process_thread.daemon = True
        process_thread.start()
        
        # Iniciar captura de audio
        try:
            with sd.InputStream(
                callback=self.audio_callback,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                dtype=np.float32
            ):
                print("🎤 Escuchando...")
                while self.running:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo asistente...")
            self.running = False
        except Exception as e:
            print(f"❌ Error en captura de audio: {e}")
            self.running = False

if __name__ == "__main__":
    assistant = PuertochoAssistant()
    assistant.start()

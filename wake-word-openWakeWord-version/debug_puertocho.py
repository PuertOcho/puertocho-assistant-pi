#!/usr/bin/env python3
"""
Debug del modelo Puertocho - versión simplificada para diagnosticar
"""

import os
import time
import numpy as np
import sounddevice as sd
import onnxruntime as ort
from pathlib import Path

# Configurar entorno
os.environ['OPENWAKEWORD_THRESHOLD'] = '0.3'  # Threshold más bajo para debug

class PuertochoDebug:
    def __init__(self):
        self.model_path = Path('checkpoints/puertocho.onnx')
        self.threshold = 0.3  # Más sensible para debug
        self.sample_rate = 16000
        self.audio_buffer = []
        
        # Cargar modelo
        print(f"🎯 Cargando modelo desde {self.model_path}")
        self.session = ort.InferenceSession(str(self.model_path))
        print("✅ Modelo cargado")
        
    def audio_callback(self, indata, frames, time, status):
        if status:
            print(f"⚠️ Audio status: {status}")
        
        # Convertir a mono si es estéreo
        if len(indata.shape) > 1:
            audio_data = indata[:, 0]
        else:
            audio_data = indata.flatten()
            
        # Convertir a float32
        audio_float = audio_data.astype(np.float32)
        
        # Añadir al buffer
        self.audio_buffer.extend(audio_float)
        
        # Procesar ventana de 1 segundo
        if len(self.audio_buffer) >= 16000:
            # Tomar últimos 16000 samples
            audio_window = np.array(self.audio_buffer[-16000:], dtype=np.float32)
            
            # Preparar input para ONNX
            model_input = audio_window.reshape(1, -1)
            
            try:
                # Ejecutar inferencia
                result = self.session.run(None, {'audio': model_input})
                raw_score = result[0][0][0]
                probability = 1 / (1 + np.exp(-raw_score))
                
                # Mostrar información cada 2 segundos
                if not hasattr(self, 'last_print_time'):
                    self.last_print_time = time.time()
                
                if time.time() - self.last_print_time > 2:
                    print(f"🔊 Audio - Raw: {raw_score:.3f}, Prob: {probability:.3f}, Thresh: {self.threshold}")
                    if probability > 0.1:  # Mostrar actividad significativa
                        print(f"   📈 ACTIVIDAD DETECTADA - Prob: {probability:.3f}")
                    self.last_print_time = time.time()
                
                # Verificar detección
                if probability > self.threshold:
                    print(f"🎉 ¡PUERTOCHO DETECTADO! Prob: {probability:.3f}, Raw: {raw_score:.3f}")
                    time.sleep(2)  # Cooldown
                    self.audio_buffer = []  # Limpiar buffer
                
            except Exception as e:
                print(f"❌ Error en inferencia: {e}")
            
            # Limitar buffer
            if len(self.audio_buffer) > 32000:
                self.audio_buffer = self.audio_buffer[-16000:]
    
    def start(self):
        print("🚀 Iniciando debug de Puertocho...")
        print(f"🎚️ Threshold: {self.threshold}")
        print("💡 Di 'Puertocho' claramente")
        print("🛑 Presiona Ctrl+C para salir")
        
        try:
            with sd.InputStream(
                callback=self.audio_callback,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=1280,
                dtype=np.float32
            ):
                print("🎤 Escuchando...")
                while True:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\n🛑 Debug detenido")

if __name__ == "__main__":
    debug = PuertochoDebug()
    debug.start()

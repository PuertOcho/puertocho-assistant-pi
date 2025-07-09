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
import asyncio
import websockets
import json
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class WebSocketServer:
    def __init__(self, assistant):
        self.assistant = assistant
        self.clients = set()
        self.host = "0.0.0.0"
        self.port = 8765

    async def register(self, websocket):
        self.clients.add(websocket)
        logging.info(f"Nuevo cliente conectado: {websocket.remote_address}")
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
            logging.info(f"Cliente desconectado: {websocket.remote_address}")

    async def handle_messages(self, websocket):
        async for message in websocket:
            data = json.loads(message)
            if data.get("type") == "manual_activation":
                logging.info("Activación manual recibida desde el dashboard.")
                # Aquí se podría llamar a una función en el asistente
                # self.assistant.trigger_listening()

    async def broadcast(self, message):
        if self.clients:
            await asyncio.wait([client.send(json.dumps(message)) for client in self.clients])

    async def start(self):
        logging.info(f"Iniciando servidor WebSocket en ws://{self.host}:{self.port}")
        async with websockets.serve(self.register, self.host, self.port):
            await asyncio.Future()  # Correr indefinidamente

    def run_in_thread(self):
        asyncio.run(self.start())

class PuertochoAssistant:
    def __init__(self):
        self.model_path = Path('checkpoints/puertocho.onnx')
        self.threshold = 0.5
        self.sample_rate = 16000
        self.chunk_size = 1280  # 80ms chunks
        self.audio_buffer = []
        self.running = False
        self.status = "idle" # idle, listening, processing, error
        self.ws_server = WebSocketServer(self)
        
        # Cargar modelo ONNX
        print(f"🎯 Cargando modelo Puertocho desde {self.model_path}")
        self.session = ort.InferenceSession(str(self.model_path))
        print("✅ Modelo cargado exitosamente")
        
        # Buffer para audio
        self.audio_queue = queue.Queue()
        
    def set_status(self, new_status):
        if self.status != new_status:
            self.status = new_status
            logging.info(f"Cambiando estado a: {self.status}")
            asyncio.run(self.ws_server.broadcast({
                "type": "status_update",
                "payload": {"status": self.status}
            }))

    def log_command(self, command_text):
        logging.info(f"Comando reconocido: {command_text}")
        asyncio.run(self.ws_server.broadcast({
            "type": "command_log",
            "payload": {
                "command": command_text,
                "timestamp": time.time() * 1000 # JS usa milisegundos
            }
        }))

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
        self.set_status("listening")
        
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
                logging.error(f"Error procesando audio: {e}")
                self.set_status("error")
                time.sleep(5)
                self.set_status("idle")

    def on_wake_word_detected(self):
        """Acción cuando se detecta la wake word"""
        print("🗣️ ¡Hola! Soy Puertocho. ¿En qué puedo ayudarte?")
        # Aquí se puede integrar con el resto del sistema
        
    def start(self):
        """Iniciar el asistente y el servidor de audio"""
        if self.running:
            print("El asistente ya está en ejecución.")
            return

        self.running = True
        
        # Iniciar servidor WebSocket en un hilo separado
        ws_thread = threading.Thread(target=self.ws_server.run_in_thread, daemon=True)
        ws_thread.start()

        # Iniciar procesamiento de audio en otro hilo
        audio_thread = threading.Thread(target=self.process_audio, daemon=True)
        audio_thread.start()

        # Iniciar stream de audio
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                blocksize=self.chunk_size,
                callback=self.audio_callback,
                dtype='float32'
            ):
                print("🎧 Stream de audio iniciado. El asistente está escuchando.")
                self.set_status("idle")
                # Mantener el hilo principal vivo
                while self.running:
                    time.sleep(1)
        except Exception as e:
            logging.error(f"No se pudo iniciar el stream de audio: {e}")
            self.set_status("error")
            self.running = False

    def stop(self):
        """Detener el asistente"""
        print("Deteniendo el asistente...")
        self.running = False
        self.set_status("idle")

if __name__ == "__main__":
    assistant = PuertochoAssistant()
    try:
        assistant.start()
    except KeyboardInterrupt:
        assistant.stop()
        print("\n👋 Asistente detenido por el usuario.")

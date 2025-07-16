"""
Controlador de efectos LED para ReSpeaker 2-Mic Pi HAT V1.0
Patrones de LEDs similares a Google Home para diferentes estados del asistente
"""

import time
import threading
try:
    import queue as Queue
except ImportError:
    import Queue as Queue

from utils.apa102 import APA102
from utils.logging_config import get_logger

logger = get_logger('led_controller')

class LEDController:
    """
    Controlador de LEDs RGB para ReSpeaker con patrones de estado.
    Maneja los 3 LEDs APA102 integrados en el módulo.
    """
    
    PIXELS_N = 3  # ReSpeaker tiene 3 LEDs RGB

    def __init__(self, brightness=10):
        """
        Inicializar controlador de LEDs.
        
        Args:
            brightness: Brillo global (0-31, recomendado 5-15)
        """
        try:
            # Patrón base para los LEDs
            self.basis = [0] * 3 * self.PIXELS_N
            self.basis[0] = 2  # LED 0: Rojo
            self.basis[3] = 1  # LED 1: Verde
            self.basis[4] = 1  # LED 1: Rojo
            self.basis[7] = 2  # LED 2: Azul
            
            self.colors = [0] * 3 * self.PIXELS_N
            self.dev = APA102(num_led=self.PIXELS_N, global_brightness=brightness)
            
            # Sistema de hilos para efectos
            self.next = threading.Event()
            self.queue = Queue.Queue()
            self.thread = threading.Thread(target=self._run)
            self.thread.daemon = True
            self.thread.start()
            
            self.enabled = True
            logger.info("✅ LEDs RGB integrados inicializados")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando LEDs RGB: {e}")
            self.enabled = False
            self.dev = None

    def is_enabled(self) -> bool:
        """Verificar si los LEDs están habilitados."""
        return self.enabled and self.dev is not None

    def idle(self):
        """Estado idle - LEDs apagados o luz suave."""
        if not self.is_enabled():
            return
        self.next.set()
        self.queue.put(self._idle)

    def wakeup(self, direction=0):
        """Efecto de activación - wake word detectado."""
        if not self.is_enabled():
            return
        def f():
            self._wakeup(direction)
        self.next.set()
        self.queue.put(f)

    def listening(self):
        """Estado escuchando - luz constante."""
        if not self.is_enabled():
            return
        self.next.set()
        self.queue.put(self._listening)

    def thinking(self):
        """Estado procesando - efecto rotatorio."""
        if not self.is_enabled():
            return
        self.next.set()
        self.queue.put(self._thinking)

    def speaking(self):
        """Estado hablando - efecto pulsante."""
        if not self.is_enabled():
            return
        self.next.set()
        self.queue.put(self._speaking)

    def error(self):
        """Estado de error - parpadeo rojo."""
        if not self.is_enabled():
            return
        self.next.set()
        self.queue.put(self._error)

    def off(self):
        """Apagar todos los LEDs."""
        if not self.is_enabled():
            return
        self.next.set()
        self.queue.put(self._off)

    def _run(self):
        """Hilo principal para ejecutar efectos."""
        while True:
            try:
                func = self.queue.get()
                func()
            except Exception as e:
                logger.error(f"❌ Error en efecto LED: {e}")

    def _idle(self):
        """Efecto idle - luz muy tenue."""
        # Luz azul muy suave
        colors = [0, 0, 1] * self.PIXELS_N  # Azul suave en todos los LEDs
        self.write(colors)

    def _wakeup(self, direction=0):
        """Efecto de activación - incremento gradual de brillo."""
        for i in range(1, 25):
            colors = [i * v for v in self.basis]
            self.write(colors)
            time.sleep(0.01)
        self.colors = colors

    def _listening(self):
        """Efecto escuchando - luz constante."""
        # Usar patrón base con brillo medio
        colors = [12 * v for v in self.basis]
        self.write(colors)
        self.colors = colors

    def _thinking(self):
        """Efecto pensando - rotación continua."""
        colors = self.colors
        
        self.next.clear()
        while not self.next.is_set():
            colors = colors[3:] + colors[:3]  # Rotar colores
            self.write(colors)
            time.sleep(0.2)
        
        # Fade out gradual
        t = 0.1
        for i in range(0, 5):
            colors = colors[3:] + colors[:3]
            self.write([(v * (4 - i) / 4) for v in colors])
            time.sleep(t)
            t /= 2
        
        self.colors = colors

    def _speaking(self):
        """Efecto hablando - pulsación."""
        colors = self.colors
        gradient = -1
        position = 24
        
        self.next.clear()
        while not self.next.is_set():
            position += gradient
            self.write([(v * position / 24) for v in colors])
            
            if position == 24 or position == 4:
                gradient = -gradient
                time.sleep(0.2)
            else:
                time.sleep(0.01)
        
        # Fade out
        while position > 0:
            position -= 1
            self.write([(v * position / 24) for v in colors])
            time.sleep(0.01)

    def _error(self):
        """Efecto de error - parpadeo rojo."""
        red_colors = [20, 0, 0] * self.PIXELS_N  # Rojo en todos los LEDs
        
        for _ in range(6):  # Parpadear 3 veces
            self.write(red_colors)
            time.sleep(0.2)
            self.write([0, 0, 0] * self.PIXELS_N)
            time.sleep(0.2)
        
        # Volver a idle
        self._idle()

    def _off(self):
        """Apagar todos los LEDs."""
        self.write([0] * 3 * self.PIXELS_N)

    def write(self, colors):
        """
        Escribir colores a los LEDs.
        
        Args:
            colors: Lista de valores RGB [R,G,B,R,G,B,R,G,B] para 3 LEDs
        """
        if not self.is_enabled():
            return
            
        try:
            for i in range(self.PIXELS_N):
                self.dev.set_pixel(i, 
                                 int(colors[3*i]),     # Rojo
                                 int(colors[3*i + 1]), # Verde
                                 int(colors[3*i + 2])) # Azul
            self.dev.show()
        except Exception as e:
            logger.error(f"❌ Error escribiendo LEDs: {e}")

    def cleanup(self):
        """Limpiar recursos."""
        if self.is_enabled():
            self.off()
            time.sleep(0.1)
            self.dev.cleanup()
            logger.info("✅ LEDs RGB limpiados")

    def set_state(self, state: str):
        """
        Cambiar estado de los LEDs según el estado del asistente.
        
        Args:
            state: Estado del asistente ('idle', 'listening', 'processing', 'error')
        """
        if not self.is_enabled():
            return
            
        if state == 'idle':
            self.idle()
        elif state == 'listening':
            self.listening()
        elif state == 'processing':
            self.thinking()
        elif state == 'error':
            self.error()
        else:
            logger.warning(f"⚠️ Estado LED desconocido: {state}")

    def test_sequence(self):
        """Secuencia de prueba para verificar todos los efectos."""
        if not self.is_enabled():
            logger.warning("⚠️ LEDs no habilitados, no se puede hacer prueba")
            return
            
        logger.info("🧪 Iniciando secuencia de prueba de LEDs...")
        
        try:
            logger.info("  - Wakeup")
            self.wakeup()
            time.sleep(2)
            
            logger.info("  - Listening")
            self.listening()
            time.sleep(2)
            
            logger.info("  - Thinking")
            self.thinking()
            time.sleep(3)
            
            logger.info("  - Speaking")
            self.speaking()
            time.sleep(3)
            
            logger.info("  - Error")
            self.error()
            time.sleep(2)
            
            logger.info("  - Off")
            self.off()
            time.sleep(1)
            
            logger.info("  - Idle")
            self.idle()
            
            logger.info("✅ Secuencia de prueba completada")
            
        except Exception as e:
            logger.error(f"❌ Error en secuencia de prueba: {e}")


# Instancia global del controlador
led_controller = None

def get_led_controller(brightness=10) -> LEDController:
    """Obtener instancia global del controlador de LEDs."""
    global led_controller
    if led_controller is None:
        led_controller = LEDController(brightness)
    return led_controller

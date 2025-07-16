"""
Controlador de LEDs RGB APA102 para ReSpeaker 2-Mic Pi HAT V1.0
Basado en el código original de https://github.com/respeaker/mic_hat
"""

import spidev
from math import ceil

RGB_MAP = { 'rgb': [3, 2, 1], 'rbg': [3, 1, 2], 'grb': [2, 3, 1],
            'gbr': [2, 1, 3], 'brg': [1, 3, 2], 'bgr': [1, 2, 3] }

class APA102:
    """
    Driver para LEDs APA102 (aka "DotStar").
    Controlador de los 3 LEDs RGB integrados en el ReSpeaker.
    """
    
    # Constantes
    MAX_BRIGHTNESS = 0b11111  # Máximo brillo seguro
    LED_START = 0b11100000    # Tres bits "1", seguidos de 5 bits de brillo

    def __init__(self, num_led=3, global_brightness=MAX_BRIGHTNESS,
                 order='rgb', bus=0, device=1, max_speed_hz=8000000):
        self.num_led = num_led  # ReSpeaker tiene 3 LEDs
        order = order.lower()
        self.rgb = RGB_MAP.get(order, RGB_MAP['rgb'])
        
        # Limitar brillo al máximo si es mayor
        if global_brightness > self.MAX_BRIGHTNESS:
            self.global_brightness = self.MAX_BRIGHTNESS
        else:
            self.global_brightness = global_brightness

        self.leds = [self.LED_START, 0, 0, 0] * self.num_led  # Buffer de píxeles
        self.spi = spidev.SpiDev()  # Inicializar SPI
        self.spi.open(bus, device)  # Abrir puerto SPI 0, dispositivo 1
        
        # Aumentar velocidad para pintado más rápido
        if max_speed_hz:
            self.spi.max_speed_hz = max_speed_hz

    def clock_start_frame(self):
        """Envía frame de inicio a la tira de LEDs."""
        self.spi.xfer2([0] * 4)  # Frame de inicio, 32 bits cero

    def clock_end_frame(self):
        """Envía frame de fin a la tira de LEDs."""
        self.spi.xfer2([0xFF] * 4)

    def clear_strip(self):
        """Apaga la tira y muestra el resultado inmediatamente."""
        for led in range(self.num_led):
            self.set_pixel(led, 0, 0, 0)
        self.show()

    def set_pixel(self, led_num, red, green, blue, bright_percent=100):
        """
        Establece el color de un píxel en la tira LED.
        
        Args:
            led_num: Número del LED (0-2)
            red: Valor rojo (0-255)
            green: Valor verde (0-255)
            blue: Valor azul (0-255)
            bright_percent: Porcentaje de brillo (0-100)
        """
        if led_num < 0 or led_num >= self.num_led:
            return  # LED invisible, ignorar

        # Calcular brillo como porcentaje del brillo global
        brightness = int(ceil(bright_percent * self.global_brightness / 100.0))

        # Frame de inicio del LED
        ledstart = (brightness & 0b00011111) | self.LED_START

        start_index = 4 * led_num
        self.leds[start_index] = ledstart
        self.leds[start_index + self.rgb[0]] = red
        self.leds[start_index + self.rgb[1]] = green
        self.leds[start_index + self.rgb[2]] = blue

    def set_pixel_rgb(self, led_num, rgb_color, bright_percent=100):
        """
        Establece el color de un píxel usando color RGB combinado.
        
        Args:
            led_num: Número del LED (0-2)
            rgb_color: Color RGB como entero (0xRRGGBB)
            bright_percent: Porcentaje de brillo (0-100)
        """
        self.set_pixel(led_num, (rgb_color & 0xFF0000) >> 16,
                       (rgb_color & 0x00FF00) >> 8, rgb_color & 0x0000FF,
                       bright_percent)

    def rotate(self, positions=1):
        """Rota los LEDs por el número especificado de posiciones."""
        cutoff = 4 * (positions % self.num_led)
        self.leds = self.leds[cutoff:] + self.leds[:cutoff]

    def show(self):
        """Envía el contenido del buffer de píxeles a la tira."""
        self.clock_start_frame()
        # xfer2 modifica la lista, así que debe copiarse primero
        data = list(self.leds)
        while data:
            self.spi.xfer2(data[:32])
            data = data[32:]
        self.clock_end_frame()

    def cleanup(self):
        """Libera el dispositivo SPI; llamar al final"""
        self.spi.close()

    @staticmethod
    def combine_color(red, green, blue):
        """Combina valores RGB en un solo valor de color."""
        return (red << 16) + (green << 8) + blue

    def wheel(self, wheel_pos):
        """Obtiene un color de una rueda de colores; Verde -> Rojo -> Azul -> Verde"""
        if wheel_pos > 255:
            wheel_pos = 255  # Protección
        if wheel_pos < 85:  # Verde -> Rojo
            return self.combine_color(wheel_pos * 3, 255 - wheel_pos * 3, 0)
        if wheel_pos < 170:  # Rojo -> Azul
            wheel_pos -= 85
            return self.combine_color(255 - wheel_pos * 3, 0, wheel_pos * 3)
        # Azul -> Verde
        wheel_pos -= 170
        return self.combine_color(0, wheel_pos * 3, 255 - wheel_pos * 3)

    def dump_array(self):
        """Para depuración: volcar el array de LEDs en la consola."""
        print(self.leds)

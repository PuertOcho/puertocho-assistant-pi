import sounddevice as sd
import sys

def list_audio_devices():
    """
    Lists available audio input and output devices.
    """
    try:
        print("Buscando dispositivos de audio...")
        devices = sd.query_devices()
        print("Dispositivos de audio disponibles:")
        
        # Mostrar todos los dispositivos con índice
        for i, device in enumerate(devices):
            if isinstance(device, dict):
                print(f"  {i}: {device.get('name', 'Unknown')} - Max inputs: {device.get('max_input_channels', 0)}, Max outputs: {device.get('max_output_channels', 0)}")

        # Buscar dispositivos que contengan 'seeed', '2mic' o 'voicecard'
        seeed_devices = []
        for i, device in enumerate(devices):
            if isinstance(device, dict):
                name = device.get('name', '').lower()
                if any(keyword in name for keyword in ['seeed', '2mic', 'voicecard']):
                    seeed_devices.append((i, device))

        if not seeed_devices:
            print("\n[ATENCIÓN] No se ha detectado ningún dispositivo de audio relacionado con 'seeed', '2mic' o 'voicecard'.")
            print("Asegúrate de que el driver del ReSpeaker 2-Mic Pi HAT está instalado correctamente.")
            print("Puedes encontrar instrucciones en 'docs/respeaker-2mic-hat-v1.md'.")
            sys.exit(1)
        else:
            print(f"\n[ÉXITO] Se han detectado {len(seeed_devices)} dispositivo(s) relacionado(s):")
            for idx, device in seeed_devices:
                print(f"  - Índice {idx}: {device['name']} (Entradas: {device.get('max_input_channels', 0)}, Salidas: {device.get('max_output_channels', 0)})")

    except Exception as e:
        print(f"\n[ERROR] Ocurrió un error al buscar dispositivos de audio: {e}")
        print("Asegúrate de que 'portaudio' está instalado en el sistema (sudo apt-get install libportaudio2).")
        sys.exit(1)

if __name__ == "__main__":
    list_audio_devices()

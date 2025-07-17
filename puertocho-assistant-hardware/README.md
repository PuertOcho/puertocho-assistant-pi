# PuertoCho Assistant Hardware Service

🎙️ **Hardware service for PuertoCho Assistant on Raspberry Pi**

## 📋 Description

This service manages all hardware components of the PuertoCho Assistant running on a Raspberry Pi 4B with ReSpeaker 2-Mic Pi HAT V1.0. It handles audio recording, LED control, button detection, NFC operations, and wake word detection.

## 🔧 Hardware Components

### Primary Hardware
- **Raspberry Pi 4B** - Main computing unit
- **ReSpeaker 2-Mic Pi HAT V1.0** - Audio input/output, LEDs, button
- **NFC Module** - I2C connected NFC reader/writer

### ReSpeaker Features
- 2x Microphones (stereo input)
- 3x APA102 RGB LEDs
- 1x Button (GPIO17)
- Audio codec WM8960
- 3.5mm audio output

## 🚀 Quick Start

### Prerequisites
- Raspberry Pi 4B with Raspberry Pi OS
- ReSpeaker 2-Mic Pi HAT V1.0 installed
- Docker and Docker Compose installed
- I2C and SPI enabled

### Setup
1. **Run setup script**:
   ```bash
   ./scripts/setup.sh
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Build and start service**:
   ```bash
   docker-compose build puertocho-assistant-hardware
   docker-compose up puertocho-assistant-hardware
   ```

## 📁 Project Structure

```
puertocho-assistant-hardware/
├── Dockerfile                 # Container configuration
├── README.md                  # This file
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── app/                      # Main application
│   ├── main.py               # Entry point
│   ├── config.py             # Configuration management
│   ├── requirements.txt      # Python dependencies
│   ├── core/                 # Core hardware modules
│   │   ├── audio_manager.py  # Audio recording/playback
│   │   ├── led_controller.py # LED control
│   │   ├── button_handler.py # Button detection
│   │   ├── nfc_manager.py    # NFC operations
│   │   ├── state_machine.py  # State management
│   │   └── wake_word_detector.py # Wake word detection
│   ├── api/                  # HTTP/WebSocket API
│   │   ├── http_server.py    # HTTP endpoints
│   │   └── websocket_client.py # WebSocket communication
│   ├── utils/                # Utilities
│   │   ├── logger.py         # Logging system
│   │   ├── metrics.py        # Performance metrics
│   │   └── calibration.py    # Hardware calibration
│   └── tests/                # Test modules
├── scripts/                  # Setup and utility scripts
│   ├── setup.sh              # Installation script
│   ├── test_hardware.py      # Hardware tests
│   └── calibrate.py          # Calibration tool
├── logs/                     # Log files
├── config/                   # Configuration files
└── models/                   # Wake word models
    ├── porcupine_params_es.pv
    └── Puerto-ocho_es_raspberry-pi_v3_0_0.ppn
```

## 🔌 Hardware Configuration

### GPIO Pins Used
- **GPIO17**: Button (built-in on ReSpeaker)
- **GPIO2/3**: I2C (SDA/SCL) - for NFC module
- **GPIO12/13**: Available for expansion
- **SPI0**: LEDs control (APA102)
- **I2S**: Audio (WM8960 codec)

### I2C Devices
- **NFC Module**: Address 0x48 (configurable)

### SPI Devices
- **LED Controller**: SPI bus 0, device 0

## 🎛️ Configuration

### Environment Variables
Key configuration options in `.env`:

```bash
# Audio
AUDIO_DEVICE_NAME=seeed-voicecard
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=2

# Wake Word
WAKE_WORD_MODEL_PATH=/app/models/Puerto-ocho_es_raspberry-pi_v3_0_0.ppn
WAKE_WORD_SENSITIVITY=0.5
PORCUPINE_ACCESS_KEY=your_key_here

# Hardware
BUTTON_PIN=17
LED_COUNT=3
LED_BRIGHTNESS=128

# Backend
BACKEND_URL=http://localhost:8765
BACKEND_WS_URL=ws://localhost:8765/ws
```

## 🌐 API Endpoints

### HTTP Endpoints
- `GET /health` - Service health check
- `POST /audio/start` - Start audio recording
- `POST /audio/stop` - Stop audio recording
- `GET /audio/status` - Get audio status
- `POST /nfc/read` - Read NFC tag
- `POST /nfc/write` - Write NFC tag
- `GET /nfc/status` - Get NFC status
- `POST /led/pattern` - Change LED pattern

### WebSocket Events
**Sent to backend**:
- Audio data
- Button events
- NFC events
- State changes
- Hardware metrics

**Received from backend**:
- Control commands
- Configuration updates
- LED patterns

## 🎨 LED States

The RGB LEDs indicate different assistant states:

- 🔵 **Blue (pulsing)**: Idle/Available
- 🟢 **Green (solid)**: Listening
- 🟡 **Yellow (spinning)**: Processing
- 🔴 **Red (blinking)**: Error
- 🟣 **Purple**: Wake word detected

## 🧪 Testing

### Run Basic Tests
```bash
# Test configuration and basic functionality
python app/tests/test_basic.py

# Test hardware components
python scripts/test_hardware.py
```

### Hardware Tests
```bash
# Test audio recording
arecord -D plughw:X,0 -f S16_LE -r 16000 -d 5 test.wav

# Test I2C
i2cdetect -y 1

# Test SPI
ls /dev/spidev*
```

## 📊 Monitoring

### Health Checks
- HTTP health endpoint: `GET /health`
- Docker health check configured
- Automatic restart on failure

### Logging
- Structured JSON logging
- Log rotation (10MB files, 5 backups)
- Real-time log streaming

### Metrics
- Audio latency
- Button press counts
- NFC read/write operations
- LED pattern changes
- System resource usage

## 🔧 Troubleshooting

### Common Issues

1. **Audio device not found**
   ```bash
   # Check available audio devices
   aplay -l
   arecord -l
   
   # Install ReSpeaker driver
   # Follow: https://github.com/respeaker/seeed-voicecard
   ```

2. **I2C permission denied**
   ```bash
   sudo usermod -a -G i2c $USER
   # Reboot required
   ```

3. **SPI not working**
   ```bash
   # Enable SPI
   sudo raspi-config nonint do_spi 0
   sudo reboot
   ```

4. **GPIO permission denied**
   ```bash
   sudo usermod -a -G gpio $USER
   # Reboot required
   ```

### Debug Mode
Enable debug logging:
```bash
DEBUG_MODE=true
LOG_LEVEL=DEBUG
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Porcupine](https://github.com/Picovoice/porcupine) for wake word detection
- [ReSpeaker](https://github.com/respeaker/seeed-voicecard) for audio HAT support
- [FastAPI](https://fastapi.tiangolo.com/) for web framework
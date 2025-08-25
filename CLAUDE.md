# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PuertoCho Assistant is a Raspberry Pi-based voice assistant system with distributed architecture consisting of:
- **Hardware Service** (port 8080): Manages ReSpeaker 2-Mic HAT, audio capture, wake word detection, and LED control
- **Backend Gateway** (port 8000): Orchestrates communication between hardware, web interface, and remote backend
- **Web Dashboard** (port 3000): Svelte-based interface for monitoring and control, with kiosk mode support
- **Remote Backend** (port 10002): Java microservices for intent processing, conversation management, and AI responses

## Development Commands

### Docker Compose Operations
```bash
# Start all services
docker compose up -d

# Start with hot reload for web development
HOT_RELOAD_ENABLED=true docker compose up -d

# Start in kiosk mode (for Raspberry Pi with display)
KIOSK_MODE=true docker compose up -d

# View logs
docker compose logs -f [service-name]

# Stop services
docker compose down
```

### Service-Specific Commands

**Web Dashboard (Svelte)**:
```bash
cd puertocho-assistant-web-view
npm run dev              # Development server
npm run dev:host         # Development server accessible on network
npm run build            # Production build
npm run check            # Type checking
```

**Backend Gateway (Python)**:
```bash
cd puertocho-assistant-backend
python src/main.py       # Direct Python execution
# Usually run via docker compose
```

**Hardware Service (Python)**:
```bash
cd puertocho-assistant-hardware
python app/main.py       # Direct Python execution (requires GPIO access)
# Usually run via docker compose with privileged mode
```

## Architecture Overview

### Core Communication Flow
```
Hardware (8080) ←→ Backend Gateway (8000) ←→ Remote Backend (10002)
                         ↕
                   Web Dashboard (3000)
```

### Key Components

**Hardware Service** (`puertocho-assistant-hardware/`):
- `app/main.py`: Main service orchestrator with EventBus and StateManager
- `app/core/state_manager.py`: Manages assistant states (IDLE, LISTENING, PROCESSING, SPEAKING)
- `app/core/audio_manager.py`: Handles ReSpeaker 2-Mic HAT audio capture and playback
- `app/core/wake_word_detector.py`: Porcupine wake word detection
- `app/core/vad_handler.py`: Voice Activity Detection for audio segmentation
- `app/core/led_controller.py`: RGB LED control for visual feedback
- `app/api/http_server.py`: FastAPI endpoints for hardware control

**Backend Gateway** (`puertocho-assistant-backend/`):
- `src/main.py`: FastAPI application with WebSocket support
- `src/core/state_manager.py`: Replicates and manages hardware state
- `src/clients/hardware_client.py`: HTTP client for hardware communication
- `src/clients/remote_backend_client.py`: Handles authentication and communication with remote backend
- `src/services/audio_processor.py`: Manages audio processing pipeline and remote backend integration

**Web Dashboard** (`puertocho-assistant-web-view/`):
- `src/routes/+page.svelte`: Main dashboard interface
- `src/lib/services/websocketService.ts`: Real-time communication with backend
- `src/lib/stores/`: Svelte stores for state management
- `src/lib/components/`: Modular UI components (audio controls, status indicators, etc.)

### Remote Backend Integration

The system connects to a Java microservices backend at `192.168.1.88:10002` for:
- Intent classification and conversation management
- Text-to-speech and speech-to-text processing
- AI-powered response generation

Authentication is handled automatically with JWT tokens:
- Email: `service@puertocho.local`
- Password: `servicepass123`

## Configuration

### Environment Variables

**Docker Compose** (`docker-compose.yml`):
```bash
# Hardware
ALSA_CARD=3                    # Audio device
HARDWARE_LOG_LEVEL=INFO

# Backend Gateway
HARDWARE_BASE_URL=http://localhost:8080
REMOTE_BACKEND_URL=http://192.168.1.88:10002
AUDIO_VERIFICATION_ENABLED=true

# Web Dashboard
HOT_RELOAD_ENABLED=false       # Enable for development
KIOSK_MODE=false              # Enable for Raspberry Pi display
VITE_BACKEND_WS_URL=ws://localhost:8000/ws
```

**Hardware Service** (`.env` in hardware directory):
```bash
WAKE_WORD_MODEL_PATH=/app/models/Puerto-ocho_es_raspberry-pi_v3_0_0.ppn
WAKE_WORD_SENSITIVITY=0.5
BACKEND_WS_URL=ws://localhost:8000/ws
```

### Kiosk Mode Setup

For Raspberry Pi with touchscreen:
1. Configure X11 access: `xhost +local:docker`
2. Set environment variables:
   ```bash
   KIOSK_MODE=true
   DISPLAY=:0
   KIOSK_RESOLUTION=1920x1080
   ```
3. Mount X11 socket in docker-compose.yml (already configured)

## Development Guidelines

### Adding New Features

1. **Hardware Features**: Extend `puertocho-assistant-hardware/app/core/` modules
2. **Backend Logic**: Add services in `puertocho-assistant-backend/src/services/`
3. **UI Components**: Create Svelte components in `puertocho-assistant-web-view/src/lib/components/`
4. **API Endpoints**: Add to respective `http_server.py` or `gateway_endpoints.py`

### Testing

**Hardware Service**:
```bash
cd puertocho-assistant-hardware
python -m pytest app/tests/  # Unit tests
python app/scripts/test_*.py  # Integration tests
```

**Backend Gateway**:
```bash
cd puertocho-assistant-backend
python -m pytest            # Unit tests (when available)
```

**Web Dashboard**:
```bash
cd puertocho-assistant-web-view
npm run check               # Type checking
```

### Audio Processing Pipeline

1. **Capture**: Hardware captures audio via ReSpeaker 2-Mic HAT
2. **Wake Word**: Porcupine detects "Puerto Ocho" wake phrase
3. **VAD**: Voice Activity Detection segments user speech
4. **Processing**: Audio sent to remote backend for intent processing
5. **Response**: TTS response played through hardware speakers
6. **Verification**: Audio copies saved to `audio_verification/` for debugging

### State Management

The system uses a unified state machine:
- **IDLE**: Waiting for wake word
- **LISTENING**: Recording user input after wake word
- **PROCESSING**: Sending audio to backend for analysis
- **SPEAKING**: Playing response audio
- **ERROR**: Handling system errors

State changes are synchronized across all components via WebSocket connections.

## Troubleshooting

### Common Issues

**Audio Issues**:
- Check `docker compose logs puertocho-assistant-hardware`
- Verify audio device: `aplay -l` on host
- Ensure ALSA_CARD environment variable matches device

**WebSocket Connection Issues**:
- Verify backend is running: `curl http://localhost:8000/health`
- Check firewall settings for ports 8000, 8080, 3000
- Review WebSocket logs in browser developer tools

**Kiosk Mode Issues**:
- Ensure X11 is running: `ps aux | grep -i xorg`
- Check display variable: `echo $DISPLAY`
- Verify xhost permissions: `xhost +local:docker`

**Remote Backend Connection**:
- Check network connectivity to `192.168.1.88:10002`
- Verify authentication endpoint: `/api/v1/auth/login`
- Review backend gateway logs for authentication errors

### Log Locations

- Hardware: `docker compose logs puertocho-assistant-hardware`
- Backend: `docker compose logs puertocho-backend`
- Web Dashboard: `docker compose logs puertocho-web-dashboard`
- Audio verification: `puertocho-assistant-backend/audio_verification/`
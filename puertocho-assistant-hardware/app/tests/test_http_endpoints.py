#!/usr/bin/env python3
"""
Tests unitarios para los endpoints HTTP del servidor hardware
Valida las respuestas de todos los endpoints implementados en HW-API-01 a HW-API-05
"""

import pytest
import sys
import os
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime

# Agregar el directorio app al path para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from api.http_server import HTTPServer
from core.state_manager import StateManager, AssistantState

class TestHTTPServerEndpoints:
    """Tests para todos los endpoints del servidor HTTP"""
    
    @pytest.fixture
    def client(self):
        """Fixture para crear un cliente de pruebas"""
        # Crear StateManager mock
        state_manager = StateManager()
        
        # Crear servidor HTTP
        server = HTTPServer(state_manager=state_manager, port=8080)
        
        # Crear cliente de pruebas
        client = TestClient(server.app)
        return client, server
    
    def test_health_endpoint(self, client):
        """Test del endpoint GET /health"""
        test_client, server = client
        
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura de respuesta
        assert "status" in data
        assert "timestamp" in data
        assert "service" in data
        assert "version" in data
        
        assert data["status"] == "ok"
        assert data["service"] == "puertocho-hardware"
        assert data["version"] == "1.0.0"
        
        # Verificar que timestamp es válido
        timestamp = datetime.fromisoformat(data["timestamp"])
        assert isinstance(timestamp, datetime)
    
    def test_get_state_endpoint(self, client):
        """Test del endpoint GET /state"""
        test_client, server = client
        
        response = test_client.get("/state")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura de respuesta
        assert "state" in data
        assert "timestamp" in data
        assert "listening_start_time" in data
        assert "listening_duration_seconds" in data
        
        assert data["state"] in ["IDLE", "LISTENING", "PROCESSING", "SPEAKING", "ERROR"]
    
    def test_post_state_endpoint_valid(self, client):
        """Test del endpoint POST /state con estado válido"""
        test_client, server = client
        
        # Cambiar a estado LISTENING
        response = test_client.post("/state", json={"state": "LISTENING"})
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura de respuesta
        assert "success" in data
        assert "old_state" in data
        assert "new_state" in data
        assert "timestamp" in data
        
        assert data["success"] is True
        assert data["new_state"] == "LISTENING"
    
    def test_post_state_endpoint_invalid(self, client):
        """Test del endpoint POST /state con estado inválido"""
        test_client, server = client
        
        response = test_client.post("/state", json={"state": "INVALID_STATE"})
        
        assert response.status_code == 400
        data = response.json()
        
        assert "detail" in data
        # El detail es un dict con error y valid_states
        assert isinstance(data["detail"], dict)
        assert "error" in data["detail"]
        assert "valid_states" in data["detail"]
    
    def test_audio_status_endpoint(self, client):
        """Test del endpoint GET /audio/status"""
        test_client, server = client
        
        response = test_client.get("/audio/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura de respuesta (campos en el nivel raíz)
        assert "success" in data
        assert "audio_status" in data
        
        assert data["success"] is True
        
        # Verificar estructura de audio_status
        audio_status = data["audio_status"]
        assert "hardware_state" in audio_status
        assert "is_listening" in audio_status
        assert "vad_enabled" in audio_status
        assert "timestamp" in audio_status
        assert "captured_files" in audio_status
        
        assert audio_status["hardware_state"] in ["IDLE", "LISTENING", "PROCESSING", "SPEAKING", "ERROR"]
        assert isinstance(audio_status["is_listening"], bool)
        assert isinstance(audio_status["vad_enabled"], bool)
        
        captured_files = audio_status["captured_files"]
        assert "count" in captured_files
        assert "total_size_bytes" in captured_files
        assert "total_size_mb" in captured_files
    
    def test_audio_capture_endpoint(self, client):
        """Test del endpoint GET /audio/capture"""
        test_client, server = client
        
        response = test_client.get("/audio/capture")
        
        # Como no hay archivos capturados, esperamos 404
        assert response.status_code == 404
        data = response.json()
        
        # Verificar estructura de respuesta de error
        assert "detail" in data
        assert "No captured audio files found" in data["detail"]
    
    def test_metrics_endpoint(self, client):
        """Test del endpoint GET /metrics"""
        test_client, server = client
        
        response = test_client.get("/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura de respuesta
        assert "success" in data
        assert "timestamp" in data
        assert "system" in data
        assert "hardware" in data
        
        assert data["success"] is True
        
        # Verificar métricas del sistema
        system = data["system"]
        assert "cpu_percent" in system
        assert "memory" in system
        assert "disk" in system
        assert "uptime_hours" in system
        
        # Verificar estructura de memoria
        memory = system["memory"]
        assert "total_gb" in memory
        assert "available_gb" in memory
        assert "used_percent" in memory
    
    def test_led_pattern_endpoint_solid(self, client):
        """Test del endpoint POST /led/pattern con patrón sólido"""
        test_client, server = client
        
        # Mock del LEDController para evitar errores de hardware
        with patch.object(server.state_manager, 'led_controller') as mock_led:
            mock_led.COLORS = {'red': Mock(), 'green': Mock(), 'blue': Mock()}
            mock_led.brightness = 128
            
            response = test_client.post("/led/pattern", json={
                "pattern_type": "solid",
                "color": "red",
                "brightness": 200
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verificar estructura de respuesta
            assert "success" in data
            assert "pattern_set" in data
            assert "color" in data
            assert "brightness" in data
            
            assert data["success"] is True
            assert data["pattern_set"] == "solid"
            assert data["color"] == "red"
    
    def test_led_pattern_endpoint_invalid_color(self, client):
        """Test del endpoint POST /led/pattern con color inválido"""
        test_client, server = client
        
        # Mock del LEDController
        with patch.object(server.state_manager, 'led_controller') as mock_led:
            mock_led.COLORS = {'red': Mock(), 'green': Mock(), 'blue': Mock()}
            
            response = test_client.post("/led/pattern", json={
                "pattern_type": "solid",
                "color": "invalid_color"
            })
            
            assert response.status_code == 400
            data = response.json()
            
            assert "detail" in data
            assert "invalid color" in data["detail"].lower()
    
    def test_button_simulate_endpoint_short(self, client):
        """Test del endpoint POST /button/simulate con pulsación corta"""
        test_client, server = client
        
        response = test_client.post("/button/simulate", json={
            "event_type": "short",
            "duration": 0.1
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura de respuesta
        assert "success" in data
        assert "simulated_event" in data
        assert "duration_seconds" in data
        assert "timestamp" in data
        assert "message" in data
        
        assert data["success"] is True
        assert data["simulated_event"] == "short"
        assert data["duration_seconds"] == 0.1
    
    def test_button_simulate_endpoint_invalid_type(self, client):
        """Test del endpoint POST /button/simulate con tipo inválido"""
        test_client, server = client
        
        response = test_client.post("/button/simulate", json={
            "event_type": "invalid",
            "duration": 1.0
        })
        
        assert response.status_code == 400
        data = response.json()
        
        assert "detail" in data
        assert "must be 'short' or 'long'" in data["detail"]
    
    def test_openapi_docs(self, client):
        """Test de documentación OpenAPI"""
        test_client, server = client
        
        # Test Swagger UI
        response = test_client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        # Test ReDoc
        response = test_client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        # Test OpenAPI JSON
        response = test_client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_data = response.json()
        assert "openapi" in openapi_data
        assert "info" in openapi_data
        assert "paths" in openapi_data
        
        # Verificar información básica
        info = openapi_data["info"]
        assert info["title"] == "PuertoCho Hardware API"
        assert info["version"] == "1.0.0"
    
    def test_request_logging_headers(self, client):
        """Test de headers de logging agregados por middleware"""
        test_client, server = client
        
        response = test_client.get("/health")
        
        assert response.status_code == 200
        
        # Verificar que los headers de logging están presentes
        assert "X-Request-ID" in response.headers
        assert "X-Process-Time" in response.headers
        
        # Verificar formato de headers
        request_id = response.headers["X-Request-ID"]
        process_time = response.headers["X-Process-Time"]
        
        assert len(request_id) == 8  # UUID truncado
        assert float(process_time) >= 0  # Tiempo de procesamiento válido
    
    def test_cors_headers(self, client):
        """Test de configuración CORS"""
        test_client, server = client
        
        # Test preflight request
        response = test_client.options("/health", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })
        
        # Verificar headers CORS básicos
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        # El header access-control-allow-headers puede no aparecer si no se solicita específicamente
        # Verificar que la respuesta sea exitosa
        assert response.status_code == 200

if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v"])

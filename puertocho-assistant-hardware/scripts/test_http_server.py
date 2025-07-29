#!/usr/bin/env python3
"""
Script de prueba para el servidor HTTP del hardware
Valida los endpoints básicos implementados en HW-API-01 y HW-API-02
"""

import sys
import os
import logging
from datetime import datetime

# Agregar el directorio padre al path para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from api.http_server import HTTPServer
from core.state_manager import StateManager, AssistantState

def test_http_server():
    """Prueba básica del servidor HTTP"""
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger("test_http_server")
    
    try:
        # Crear StateManager mock para testing
        state_manager = StateManager()
        logger.info("✅ StateManager created successfully")
        
        # Crear servidor HTTP
        http_server = HTTPServer(state_manager, port=8080)
        logger.info("✅ HTTPServer created successfully")
        
        # Verificar que la aplicación FastAPI se creó correctamente
        assert http_server.app is not None, "FastAPI app not created"
        logger.info("✅ FastAPI app initialized")
        
        # Verificar que los endpoints están registrados
        routes = [route.path for route in http_server.app.routes]
        expected_routes = [
            "/health", 
            "/state", 
            "/audio/capture", 
            "/audio/status", 
            "/audio/send"
        ]
        
        for expected_route in expected_routes:
            # Buscar rutas que coincidan (considerando parámetros de path)
            route_found = any(expected_route in route or route.startswith(expected_route) for route in routes)
            assert route_found, f"Route {expected_route} not found in {routes}"
            logger.info(f"✅ Route {expected_route} registered")
        
        # Verificar configuración
        assert http_server.port == 8080, "Port not configured correctly"
        logger.info("✅ Port configured correctly")
        
        # Verificar integración con StateManager
        assert http_server.state_manager.state == AssistantState.IDLE, "Initial state should be IDLE"
        logger.info("✅ StateManager integration working")
        
        logger.info("🎉 All tests passed! HTTP server is ready to start.")
        logger.info(f"🌐 Server will be available at: http://0.0.0.0:8080")
        logger.info(f"📖 API docs will be available at: http://0.0.0.0:8080/docs")
        logger.info("📡 Available endpoints:")
        logger.info("   GET  /health - Health check")
        logger.info("   GET  /state - Get current state")
        logger.info("   POST /state - Change state manually")
        logger.info("   GET  /audio/capture - Get latest captured audio info")
        logger.info("   GET  /audio/status - Get audio and VAD status")
        logger.info("   POST /audio/send - Send audio to backend")
        logger.info("   GET  /audio/download/{filename} - Download specific audio file")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print(f"🧪 Testing HTTP Server Implementation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    success = test_http_server()
    
    print("=" * 60)
    if success:
        print("✅ HTTP Server test completed successfully!")
        print("Ready to proceed with HW-API-04 (hardware control endpoints)")
    else:
        print("❌ HTTP Server test failed!")
        sys.exit(1)

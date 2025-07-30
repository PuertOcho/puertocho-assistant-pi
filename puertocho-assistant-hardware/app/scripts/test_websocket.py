#!/usr/bin/env python3
"""
🌐 WebSocket Complete Test & Demo Suite
All-in-one script for testing and demonstrating WebSocket functionality
"""

import asyncio
import json
import logging
import time
import signal
import sys
import argparse
from pathlib import Path
import websockets
from websockets.exceptions import ConnectionClosed
from typing import Set, Dict, Any

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.websocket_client import WebSocketClient, MessageType, WebSocketMessage
from api.websocket_event_manager import WebSocketEventManager
from core.state_manager import StateManager, AssistantState
from config import config
from utils.logger import get_logger

logger = get_logger(__name__)

class MockBackendServer:
    """Simple mock backend server for testing"""
    
    def __init__(self, host="0.0.0.0", port=8001):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None
        self.running = False
    
    async def start(self):
        """Start mock server"""
        print(f"🏠 Starting mock backend server on {self.host}:{self.port}")
        
        self.server = await websockets.serve(
            self.handle_client, self.host, self.port,
            ping_interval=30, ping_timeout=10
        )
        
        self.running = True
        print(f"✅ Mock server ready at ws://{self.host}:{self.port}")
        
        # Monitor task
        asyncio.create_task(self.monitor_clients())
    
    async def stop(self):
        """Stop mock server"""
        print("🛑 Stopping mock backend server...")
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        print("Mock server stopped")
    
    async def handle_client(self, websocket, path):
        """Handle client connection"""
        client_addr = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        print(f"🤝 Client connected: {client_addr}")
        
        self.clients.add(websocket)
        
        try:
            # Send welcome
            await self.send_message(websocket, {
                "type": "system_command",
                "data": {"command": "welcome", "message": "Connected to mock backend"},
                "timestamp": time.time()
            })
            
            # Handle messages
            async for message in websocket:
                await self.process_message(websocket, message)
                
        except ConnectionClosed:
            print(f"👋 Client disconnected: {client_addr}")
        except Exception as e:
            print(f"❌ Error with client {client_addr}: {e}")
        finally:
            self.clients.discard(websocket)
    
    async def process_message(self, websocket, message_str):
        """Process incoming messages"""
        try:
            message = json.loads(message_str)
            msg_type = message.get("type", "unknown")
            data = message.get("data", {})
            
            print(f"📨 Received: {msg_type}")
            
            # Send responses based on message type
            if msg_type == "audio_captured":
                await self.send_message(websocket, {
                    "type": "set_led_pattern",
                    "data": {"pattern": "pulse", "color": [0, 255, 0]},
                    "timestamp": time.time()
                })
            elif msg_type == "state_changed":
                new_state = data.get("new_state", "unknown")
                if new_state == "LISTENING":
                    await self.send_message(websocket, {
                        "type": "set_led_pattern",
                        "data": {"pattern": "solid", "color": [0, 255, 0], "brightness": 200},
                        "timestamp": time.time()
                    })
            elif msg_type == "ping":
                await self.send_message(websocket, {
                    "type": "pong",
                    "data": data,
                    "timestamp": time.time()
                })
                
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    async def send_message(self, websocket, message):
        """Send message to client"""
        try:
            await websocket.send(json.dumps(message))
        except Exception as e:
            print(f"❌ Failed to send message: {e}")
    
    async def monitor_clients(self):
        """Monitor connected clients"""
        while self.running:
            await asyncio.sleep(30)
            print(f"📈 Connected clients: {len(self.clients)}")

class WebSocketTester:
    """Complete WebSocket test suite"""
    
    def __init__(self):
        self.mock_server = None
        self.client = None
        self.event_manager = None
        self.state_manager = None
    
    async def run_server_mode(self):
        """Run as mock server"""
        print("🚀 Starting in SERVER mode")
        print("This will start a mock backend server that hardware can connect to")
        print("=" * 70)
        
        self.mock_server = MockBackendServer()
        
        try:
            await self.mock_server.start()
            print("Server is running. Press Ctrl+C to stop.")
            
            # Keep running
            while self.mock_server.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Server interrupted by user")
        finally:
            if self.mock_server:
                await self.mock_server.stop()
    
    async def run_client_mode(self):
        """Run as WebSocket client test"""
        print("🚀 Starting in CLIENT mode")
        print("This will test WebSocket client functionality")
        print("=" * 70)
        
        # Test basic connection
        await self.test_basic_connection()
        await asyncio.sleep(2)
        
        # Test event manager
        await self.test_event_manager()
        await asyncio.sleep(2)
        
        # Test with state manager
        await self.test_full_integration()
        
        print("✅ All client tests completed")
    
    async def test_basic_connection(self):
        """Test basic WebSocket connection"""
        print("\n🔧 Testing basic WebSocket connection...")
        
        try:
            self.client = WebSocketClient(
                ws_url=config.backend.ws_url,
                reconnect_interval=2.0,
                max_reconnect_attempts=3
            )
            
            # Add message handler
            def handle_message(message):
                print(f"📬 Received: {message.type} - {message.data}")
            
            self.client.add_message_handler("*", handle_message)
            
            # Test connection
            await self.client.start()
            await asyncio.sleep(3)
            
            if self.client.is_connected:
                print("✅ WebSocket connected successfully")
                
                # Send test message
                await self.client.send_message(
                    MessageType.SYSTEM_EVENT,
                    {"test": "basic_connection_test", "timestamp": time.time()}
                )
                
                await asyncio.sleep(2)
            else:
                print("❌ WebSocket connection failed")
            
            await self.client.stop()
            
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
    
    async def test_event_manager(self):
        """Test WebSocket event manager"""
        print("\n🎯 Testing WebSocket event manager...")
        
        try:
            self.event_manager = WebSocketEventManager(state_manager=None)
            await self.event_manager.start()
            await asyncio.sleep(3)
            
            if self.event_manager.is_connected():
                print("✅ Event manager connected")
                
                # Test various events
                await self.event_manager.emit_button_event("short_press", 0.5)
                print("📤 Button event emitted")
                
                await self.event_manager.emit_system_event("test_event", {"test": True})
                print("📤 System event emitted")
                
                await self.event_manager.emit_hardware_metrics({
                    "cpu_usage": 25.5,
                    "memory_usage": 45.2
                })
                print("📤 Hardware metrics emitted")
                
                # Test ping
                ping_result = await self.event_manager.send_ping()
                print(f"📤 Ping sent: {ping_result}")
                
                await asyncio.sleep(2)
            else:
                print("❌ Event manager connection failed")
            
            await self.event_manager.stop()
            
        except Exception as e:
            print(f"❌ Event manager test failed: {e}")
    
    async def test_full_integration(self):
        """Test full integration with StateManager"""
        print("\n🎭 Testing full integration with StateManager...")
        
        try:
            # Create state manager
            self.state_manager = StateManager()
            
            # Create event manager with state manager
            self.event_manager = WebSocketEventManager(self.state_manager)
            self.state_manager.websocket_manager = self.event_manager
            
            await self.event_manager.start()
            await asyncio.sleep(3)
            
            if self.event_manager.is_connected():
                print("✅ Full integration connected")
                
                # Test state transitions (these will emit WebSocket events)
                print("🔄 Testing state transitions...")
                self.state_manager.set_state(AssistantState.LISTENING)
                await asyncio.sleep(1)
                
                self.state_manager.set_state(AssistantState.PROCESSING)
                await asyncio.sleep(1)
                
                self.state_manager.set_state(AssistantState.IDLE)
                await asyncio.sleep(1)
                
                # Test simulated audio capture
                await self.event_manager.emit_audio_captured(
                    "/tmp/test_audio.wav",
                    {"duration": 3.5, "sample_rate": 16000, "channels": 1}
                )
                print("📤 Audio capture event emitted")
                
                await asyncio.sleep(2)
            else:
                print("❌ Full integration connection failed")
            
            await self.event_manager.stop()
            
        except Exception as e:
            print(f"❌ Full integration test failed: {e}")
    
    async def run_demo_mode(self):
        """Run interactive demo"""
        print("🚀 Starting in DEMO mode")
        print("This will run an interactive demonstration")
        print("=" * 70)
        
        try:
            # Setup state manager and event manager
            self.state_manager = StateManager()
            self.event_manager = WebSocketEventManager(self.state_manager)
            self.state_manager.websocket_manager = self.event_manager
            
            await self.event_manager.start()
            await asyncio.sleep(3)
            
            if self.event_manager.is_connected():
                print("✅ Demo connected to backend")
                await self.run_interactive_demo()
            else:
                print("❌ Demo connection failed - running offline demo")
                await self.run_offline_demo()
            
            await self.event_manager.stop()
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
    
    async def run_interactive_demo(self):
        """Run interactive demo sequence"""
        print("\n🎬 Running interactive demo sequence...")
        
        demos = [
            ("State Transitions", self.demo_state_transitions),
            ("Button Events", self.demo_button_events),
            ("Audio Capture", self.demo_audio_capture),
            ("System Events", self.demo_system_events),
            ("Hardware Metrics", self.demo_hardware_metrics)
        ]
        
        for demo_name, demo_func in demos:
            print(f"\n--- {demo_name} ---")
            await demo_func()
            await asyncio.sleep(2)
        
        print("\n✅ Interactive demo completed!")
    
    async def demo_state_transitions(self):
        """Demo state transitions"""
        states = [AssistantState.LISTENING, AssistantState.PROCESSING, AssistantState.IDLE]
        for state in states:
            print(f"🔄 Transitioning to {state.name}")
            self.state_manager.set_state(state)
            await asyncio.sleep(1.5)
    
    async def demo_button_events(self):
        """Demo button events"""
        events = [("short_press", 0.5), ("long_press", 2.5)]
        for event_type, duration in events:
            print(f"🔘 Simulating {event_type} ({duration}s)")
            await self.event_manager.emit_button_event(event_type, duration)
            await asyncio.sleep(1)
    
    async def demo_audio_capture(self):
        """Demo audio capture"""
        print("🎵 Simulating audio capture...")
        await self.event_manager.emit_audio_captured(
            "/app/captured_audio/demo_audio.wav",
            {"duration": 3.5, "sample_rate": 16000, "channels": 1, "format": "wav"}
        )
    
    async def demo_system_events(self):
        """Demo system events"""
        events = [
            ("demo_started", {"demo_id": "websocket_demo_001"}),
            ("hardware_check", {"status": "ok", "temperature": 45.2})
        ]
        for event_type, details in events:
            print(f"⚡ System event: {event_type}")
            await self.event_manager.emit_system_event(event_type, details)
            await asyncio.sleep(1)
    
    async def demo_hardware_metrics(self):
        """Demo hardware metrics"""
        print("📊 Sending hardware metrics...")
        metrics = {
            "system": {"cpu_percent": 25.5, "memory_percent": 45.2},
            "websocket": {"connected": True, "queue_size": 0},
            "demo_info": {"timestamp": time.time()}
        }
        await self.event_manager.emit_hardware_metrics(metrics)
    
    async def run_offline_demo(self):
        """Run demo when offline"""
        print("\n🔌 Running offline demo...")
        print("Events will be queued until connection is restored")
        
        await self.event_manager.emit_system_event("offline_demo", {
            "message": "This event is queued for when connection is restored"
        })
        
        status = self.event_manager.get_connection_status()
        print(f"📊 Connection status: {status}")

async def main():
    """Main function with command line options"""
    parser = argparse.ArgumentParser(description="WebSocket Test & Demo Suite")
    parser.add_argument("mode", choices=["server", "client", "demo"], 
                       help="Mode to run: server (mock backend), client (test client), demo (interactive demo)")
    parser.add_argument("--port", type=int, default=8001, help="Port for server mode")
    
    args = parser.parse_args()
    
    print("🌐 WebSocket Complete Test & Demo Suite")
    print("=" * 50)
    print(f"Mode: {args.mode.upper()}")
    print(f"WebSocket URL: {config.backend.ws_url}")
    print("=" * 50)
    
    tester = WebSocketTester()
    
    # Setup signal handlers
    def signal_handler():
        print("\n🛑 Interrupted by user")
        return
    
    loop = asyncio.get_running_loop()
    for sig in [signal.SIGINT, signal.SIGTERM]:
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        if args.mode == "server":
            await tester.run_server_mode()
        elif args.mode == "client":
            await tester.run_client_mode()
        elif args.mode == "demo":
            await tester.run_demo_mode()
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

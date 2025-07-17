#!/usr/bin/env python3
"""
Test PulseAudio integration for ReSpeaker 2-Mic Pi HAT V1.0
Tests audio device access with PulseAudio in Docker container
"""

import os
import sys
import subprocess
import sounddevice as sd
import numpy as np
import time
from typing import List, Dict, Optional

def check_pulse_audio():
    """Check if PulseAudio is running and accessible"""
    print("🔊 Checking PulseAudio status...")
    
    try:
        # Check PulseAudio daemon
        result = subprocess.run(['pulseaudio', '--check'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ PulseAudio daemon is running")
        else:
            print("❌ PulseAudio daemon is not running")
            # Try to start it
            print("🔧 Attempting to start PulseAudio...")
            subprocess.run(['pulseaudio', '--start'], check=False)
            time.sleep(2)
    except Exception as e:
        print(f"⚠️  PulseAudio check failed: {e}")

def check_pulse_environment():
    """Check PulseAudio environment variables"""
    print("\n📋 PulseAudio Environment Variables:")
    
    pulse_vars = [
        'PULSE_RUNTIME_PATH',
        'PULSE_SERVER',
        'PULSE_RUNTIME_PATH'
    ]
    
    for var in pulse_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var} = {value}")
        else:
            print(f"  ❌ {var} = Not set")

def list_audio_devices():
    """List available audio devices"""
    print("\n🎵 Available Audio Devices:")
    
    try:
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            device_type = "Input" if device['max_input_channels'] > 0 else "Output"
            if device['max_input_channels'] > 0 and device['max_output_channels'] > 0:
                device_type = "Input/Output"
            
            print(f"  Device {i}: {device['name']}")
            print(f"    Type: {device_type}")
            print(f"    Channels: In={device['max_input_channels']}, Out={device['max_output_channels']}")
            print(f"    Sample Rate: {device['default_samplerate']}")
            print()
            
    except Exception as e:
        print(f"❌ Error listing devices: {e}")

def test_respeaker_device():
    """Test ReSpeaker device specifically"""
    print("\n🎙️  Testing ReSpeaker Device:")
    
    # Environment variables
    device_name = os.getenv('AUDIO_DEVICE_NAME', 'hw:3,0')
    device_index = int(os.getenv('AUDIO_DEVICE_INDEX', '3'))
    
    print(f"  Target device: {device_name} (index: {device_index})")
    
    try:
        # Test device query
        devices = sd.query_devices()
        
        # Look for ReSpeaker device
        respeaker_found = False
        for i, device in enumerate(devices):
            if 'seeed' in device['name'].lower() or 'respeaker' in device['name'].lower():
                print(f"  ✅ Found ReSpeaker device: {device['name']} (index: {i})")
                respeaker_found = True
                
                # Test recording
                try:
                    print(f"  🎤 Testing recording from device {i}...")
                    duration = 2  # seconds
                    sample_rate = int(device['default_samplerate'])
                    
                    recording = sd.rec(int(duration * sample_rate), 
                                     samplerate=sample_rate, 
                                     channels=1, 
                                     device=i)
                    sd.wait()
                    
                    # Check if we got audio data
                    if recording.max() > 0.001:  # Some audio detected
                        print(f"  ✅ Recording successful! Max amplitude: {recording.max():.4f}")
                    else:
                        print(f"  ⚠️  Recording completed but no audio detected (max: {recording.max():.4f})")
                        
                except Exception as e:
                    print(f"  ❌ Recording test failed: {e}")
                
                break
        
        if not respeaker_found:
            print("  ❌ ReSpeaker device not found in device list")
            print("  🔍 Looking for devices with 'card 3' or similar...")
            
            for i, device in enumerate(devices):
                if '3' in device['name'] or 'card' in device['name'].lower():
                    print(f"    Potential match: {device['name']} (index: {i})")
                    
    except Exception as e:
        print(f"❌ ReSpeaker test failed: {e}")

def test_alsa_direct():
    """Test ALSA direct access"""
    print("\n🔧 Testing ALSA Direct Access:")
    
    try:
        # Test arecord
        print("  🎤 Testing arecord...")
        result = subprocess.run([
            'arecord', '-D', 'plughw:3,0', '-f', 'S16_LE', '-r', '16000', 
            '-c', '1', '-t', 'raw', '-d', '2', '/dev/null'
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            print("  ✅ arecord successful")
        else:
            print(f"  ❌ arecord failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("  ⚠️  arecord timeout (might be working)")
    except Exception as e:
        print(f"  ❌ arecord test failed: {e}")

def main():
    """Main test function"""
    print("🚀 PulseAudio + ReSpeaker Integration Test")
    print("=" * 50)
    
    # Check environment
    check_pulse_environment()
    
    # Check PulseAudio
    check_pulse_audio()
    
    # List devices
    list_audio_devices()
    
    # Test ReSpeaker
    test_respeaker_device()
    
    # Test ALSA direct
    test_alsa_direct()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    main()

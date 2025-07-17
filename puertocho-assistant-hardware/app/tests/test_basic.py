#!/usr/bin/env python3
"""
Test script to verify hardware service basic functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from config import config, validate_config
from utils.logger import logger

def test_configuration():
    """Test configuration loading"""
    print("Testing configuration...")
    
    try:
        validate_config()
        print("✅ Configuration validation passed")
        
        # Print some config values
        print(f"📱 Hardware service will run on: {config.hardware.host}:{config.hardware.port}")
        print(f"🎵 Audio device: {config.audio.device_name}")
        print(f"📡 Backend URL: {config.backend.url}")
        print(f"🔘 Button pin: {config.gpio.button_pin}")
        print(f"💡 LED count: {config.led.count}")
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False
    
    return True

def test_logging():
    """Test logging functionality"""
    print("\nTesting logging...")
    
    try:
        logger.debug("Debug message test")
        logger.info("Info message test")
        logger.warning("Warning message test")
        logger.error("Error message test")
        
        print("✅ Logging test passed")
        
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("🧪 PuertoCho Hardware Service - Basic Tests")
    print("=" * 50)
    
    success = True
    
    # Test configuration
    if not test_configuration():
        success = False
    
    # Test logging
    if not test_logging():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All basic tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()

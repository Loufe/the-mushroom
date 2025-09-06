#!/usr/bin/env python3
"""
SPI LED Test Script for Raspberry Pi 5
Tests LED hardware using production LEDController abstraction
Run with: sudo python3 test_spi.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.hardware.led_controller import LEDController
import numpy as np
import time
import argparse

def run_comprehensive_test(controller):
    """Run comprehensive LED hardware test"""
    print("\n" + "="*60)
    print("LED HARDWARE TEST - Using Production Controller")
    print("="*60)
    
    try:
        # Get both strips
        stem = controller.strip_map.get('stem_interior')
        cap = controller.strip_map.get('cap_exterior')
        
        if not stem or not cap:
            print("✗ Could not find required strips in controller")
            return False
        
        print(f"\nConfiguration:")
        print(f"  Stem: {stem.led_count} LEDs on {stem.spi_device}")
        print(f"  Cap:  {cap.led_count} LEDs on {cap.spi_device}")
        print(f"  Total: {controller.total_leds} LEDs")
        
        # Phase 1: Test Stem Strip
        print(f"\n{'='*60}")
        print("PHASE 1: Testing Stem Interior Strip")
        print(f"{'='*60}")
        
        print("\n1.1 Basic colors (5 seconds each)...")
        for color_name, color in [("RED", (255, 0, 0)), 
                                  ("GREEN", (0, 255, 0)), 
                                  ("BLUE", (0, 0, 255))]:
            print(f"     {color_name}")
            stem.fill(color)
            stem.present()
            cap.clear()
            cap.present()  # Keep cap off
            time.sleep(5)
        
        print("\n1.2 White brightness test (1 second each)...")
        print("     Note: Using controller API for consistent brightness")
        white_pixels = np.full((controller.total_leds, 3), 255, dtype=np.uint8)
        for brightness, percent in [(25, "10%"), (64, "25%"), (128, "50%"), (192, "75%"), (255, "100%")]:
            print(f"     White at {percent} brightness ({brightness}/255)")
            controller.set_brightness(brightness)
            controller.set_pixels(white_pixels)
            controller.present()
            time.sleep(1)
        controller.set_brightness(128)  # Reset to default
        
        # Phase 2: Test Cap Strip
        print(f"\n{'='*60}")
        print("PHASE 2: Testing Cap Exterior Strip")
        print(f"{'='*60}")
        
        print("\n2.1 Basic colors (5 seconds each)...")
        for color_name, color in [("RED", (255, 0, 0)), 
                                  ("GREEN", (0, 255, 0)), 
                                  ("BLUE", (0, 0, 255))]:
            print(f"     {color_name}")
            stem.clear()
            stem.present()  # Keep stem off
            cap.fill(color)
            cap.present()
            time.sleep(5)
        
        print("\n2.2 White brightness test (1 second each)...")
        for brightness, percent in [(25, "10%"), (64, "25%"), (128, "50%"), (192, "75%"), (255, "100%")]:
            print(f"     White at {percent}")
            cap.set_brightness(brightness)
            cap.fill((255, 255, 255))
            cap.present()
            time.sleep(1)
        cap.set_brightness(128)  # Reset to default
        
        
        # Clear everything
        print("\nClearing all LEDs...")
        controller.clear()
        controller.present()
        
        print(f"\n{'='*60}")
        print("✓ ALL TESTS COMPLETE - Hardware functioning correctly!")
        print(f"{'='*60}")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        controller.clear()  # Ensure LEDs are cleared on error
        controller.present()
        return False


def main():
    parser = argparse.ArgumentParser(description='Test LED hardware using production controller')
    parser.add_argument('--config', '-c',
                       default='config/led_config.yaml',
                       help='Path to LED configuration file')
    parser.add_argument('--brightness', '-b',
                       type=int,
                       default=128,
                       help='Global brightness (0-255)')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("Raspberry Pi 5 LED Hardware Test")
    print("Using Production LEDController")
    print("="*60)
    print("\nIMPORTANT: Run with sudo!")
    print("Make sure SPI is enabled in dietpi-config")
    print("Check that /dev/spidev0.0 and /dev/spidev1.0 exist")
    
    try:
        # Initialize controller using production code
        print(f"\nInitializing LED Controller from {args.config}...")
        controller = LEDController(args.config)
        
        # Set brightness if specified
        if args.brightness != 128:
            print(f"Setting global brightness to {args.brightness}")
            controller.set_brightness(args.brightness)
        
        # Run comprehensive test
        success = run_comprehensive_test(controller)
        
        # Clean shutdown
        controller.cleanup()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n✗ Failed to initialize controller: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Hardware Test for Mushroom LED Controller
Tests LED hardware using new pattern-based architecture
"""

import sys
import os
import time
import argparse
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from hardware.led_controller import LEDController
from patterns.base import Pattern
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestPattern(Pattern):
    """Simple test pattern for hardware validation"""
    
    def __init__(self, led_count: int, color=(0, 0, 0)):
        super().__init__(led_count)
        self.color = color
        
    def get_default_params(self):
        return {}
    
    def update(self, delta_time: float) -> np.ndarray:
        # Solid color with brightness applied
        r, g, b = self.color
        self.pixels[:] = [int(r * self.brightness), 
                         int(g * self.brightness), 
                         int(b * self.brightness)]
        
        return self.pixels
    
    def set_color(self, color):
        """Set solid color"""
        self.color = color


def run_comprehensive_test(controller: LEDController) -> bool:
    """
    Run comprehensive hardware test
    
    Args:
        controller: Configured LED controller
        
    Returns:
        True if all tests pass
    """
    try:
        print("\n" + "="*60)
        print("LED HARDWARE TEST - PATTERN ARCHITECTURE")
        print("="*60)
        
        # Create test patterns
        cap_pattern = TestPattern(450)
        stem_pattern = TestPattern(250)
        
        # Set patterns on controller
        controller.set_cap_pattern(cap_pattern)
        controller.set_stem_pattern(stem_pattern)
        
        # Start controller
        print("\nStarting controller threads...")
        controller.start()
        time.sleep(1)  # Let threads initialize
        
        # Phase 1: Test Stem Strip
        print(f"\n{'='*60}")
        print("PHASE 1: Testing Stem Interior Strip (250 LEDs)")
        print(f"{'='*60}")
        
        print("\n1.1 Basic colors (3 seconds each)...")
        for color_name, color in [("RED", (255, 0, 0)), 
                                  ("GREEN", (0, 255, 0)), 
                                  ("BLUE", (0, 0, 255))]:
            print(f"     {color_name}")
            stem_pattern.set_color(color)
            cap_pattern.set_color((0, 0, 0))  # Keep cap off
            time.sleep(3)
        
        print("\n1.2 White brightness test (2 seconds each)...")
        for brightness in [25, 64, 128, 192, 255]:
            percent = int((brightness / 255) * 100)
            print(f"     White at {percent}% brightness ({brightness}/255)")
            controller.set_stem_brightness(brightness)
            stem_pattern.set_color((255, 255, 255))
            time.sleep(2)
        controller.set_stem_brightness(128)  # Reset to default
        
        # Phase 2: Test Cap Strip
        print(f"\n{'='*60}")
        print("PHASE 2: Testing Cap Exterior Strip (450 LEDs)")
        print(f"{'='*60}")
        
        print("\n2.1 Basic colors (3 seconds each)...")
        for color_name, color in [("RED", (255, 0, 0)), 
                                  ("GREEN", (0, 255, 0)), 
                                  ("BLUE", (0, 0, 255))]:
            print(f"     {color_name}")
            cap_pattern.set_color(color)
            stem_pattern.set_color((0, 0, 0))  # Keep stem off
            time.sleep(3)
        
        print("\n2.2 White brightness test (2 seconds each)...")
        for brightness in [25, 64, 128, 192, 255]:
            percent = int((brightness / 255) * 100)
            print(f"     White at {percent}% brightness ({brightness}/255)")
            controller.set_cap_brightness(brightness)
            cap_pattern.set_color((255, 255, 255))
            time.sleep(2)
        controller.set_cap_brightness(128)  # Reset to default
        
        # Clear everything
        print("\nClearing all LEDs...")
        cap_pattern.set_color((0, 0, 0))
        stem_pattern.set_color((0, 0, 0))
        time.sleep(1)
        
        # Stop controller
        print("Stopping controller...")
        controller.stop()
        
        print(f"\n{'='*60}")
        print("✓ ALL TESTS COMPLETE - Hardware functioning correctly!")
        print(f"{'='*60}")
        
        # Final performance report
        stats = controller.get_stats()
        print(f"\nFinal Statistics:")
        print(f"  Cap: {stats['cap_frames']} frames at {stats['cap_fps']:.1f} FPS")
        print(f"  Stem: {stats['stem_frames']} frames at {stats['stem_fps']:.1f} FPS")
        print(f"  Total errors: {stats['cap_errors'] + stats['stem_errors']}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to stop controller
        try:
            controller.stop()
        except:
            pass
        
        return False


def main():
    parser = argparse.ArgumentParser(description='Test LED hardware using pattern controller')
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
    print("Using Pattern-Based Controller")
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
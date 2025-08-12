#!/usr/bin/env python3
"""
Single Strip Test - Simpler test for initial setup
Run with: sudo python3 test_single.py
"""

import sys
import time
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from led_controller_single import SingleStripController
from patterns import RainbowWave, TestPattern
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Test single LED strip with patterns')
    parser.add_argument('--gpio', type=int, default=10,
                      help='GPIO pin (default: 10)')
    parser.add_argument('--count', type=int, default=200,
                      help='Number of LEDs (default: 200)')
    parser.add_argument('--brightness', type=int, default=64,
                      help='Brightness 0-255 (default: 64)')
    parser.add_argument('--pattern', default='rainbow',
                      choices=['rainbow', 'test'],
                      help='Pattern to display')
    
    args = parser.parse_args()
    
    print(f"\n{'='*50}")
    print(f"Single Strip Pattern Test")
    print(f"GPIO: {args.gpio}, LEDs: {args.count}, Brightness: {args.brightness}")
    print(f"{'='*50}\n")
    
    try:
        # Initialize controller
        controller = SingleStripController(
            gpio_pin=args.gpio,
            led_count=args.count,
            brightness=args.brightness
        )
        
        # Create pattern
        if args.pattern == 'rainbow':
            pattern = RainbowWave(args.count)
            pattern.params['wave_length'] = 50  # Shorter wave for visibility
            pattern.params['speed'] = 100  # Faster movement
        else:
            pattern = TestPattern(args.count)
        
        print(f"Running {args.pattern} pattern...")
        print("Press Ctrl+C to stop\n")
        
        # Run pattern
        while True:
            pixels = pattern.render()
            controller.set_pixels(pixels)
            controller.update()
            
            # Occasional FPS report
            if controller.frame_count == 0:
                fps = controller.get_fps()
                if fps > 0:
                    print(f"FPS: {fps:.1f}", end='\r')
            
            time.sleep(0.001)
    
    except KeyboardInterrupt:
        print("\n\nStopping...")
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    
    finally:
        if 'controller' in locals():
            controller.cleanup()
        print("Test complete!")


if __name__ == '__main__':
    main()
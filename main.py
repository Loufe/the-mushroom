#!/usr/bin/env python3
"""
Mushroom LED Controller - Main Application
Run with: sudo python3 main.py
"""

import time
import signal
import sys
import logging
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from led_controller import LEDController
from patterns import RainbowWave, RainbowCycle, TestPattern

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MushroomLights:
    """Main application controller"""
    
    def __init__(self, config_path: str = "config/led_config.yaml"):
        logger.info("Starting Mushroom Lights...")
        
        # Initialize LED controller
        self.controller = LEDController(config_path)
        
        # Available patterns
        self.patterns = {
            'test': TestPattern(self.controller.total_leds),
            'rainbow_wave': RainbowWave(self.controller.total_leds),
            'rainbow_cycle': RainbowCycle(self.controller.total_leds),
        }
        
        # Start with rainbow wave
        self.current_pattern_name = 'rainbow_wave'
        self.current_pattern = self.patterns[self.current_pattern_name]
        
        # Control flags
        self.running = True
        
        # Setup signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info(f"Initialized with pattern: {self.current_pattern_name}")
    
    def signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        logger.info("Shutdown signal received")
        self.running = False
    
    def switch_pattern(self, pattern_name: str):
        """Switch to a different pattern"""
        if pattern_name in self.patterns:
            self.current_pattern_name = pattern_name
            self.current_pattern = self.patterns[pattern_name]
            self.current_pattern.reset()
            logger.info(f"Switched to pattern: {pattern_name}")
        else:
            logger.warning(f"Unknown pattern: {pattern_name}")
    
    def run(self):
        """Main application loop"""
        logger.info("Starting main loop...")
        
        # Performance monitoring
        frame_count = 0
        last_log_time = time.time()
        
        try:
            while self.running:
                # Get pattern output
                pixels = self.current_pattern.render()
                
                # Send to LEDs
                self.controller.set_pixels(pixels)
                self.controller.update()
                
                # Performance monitoring
                frame_count += 1
                current_time = time.time()
                if current_time - last_log_time >= 5.0:  # Log every 5 seconds
                    fps = self.controller.get_fps()
                    logger.info(f"Pattern: {self.current_pattern_name} | FPS: {fps:.1f}")
                    last_log_time = current_time
                
                # Small sleep to prevent CPU spinning
                time.sleep(0.001)
        
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
        
        finally:
            # Clean shutdown
            logger.info("Shutting down...")
            self.controller.cleanup()
            logger.info("Shutdown complete")


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(description='Mushroom LED Controller')
    parser.add_argument(
        '--pattern', '-p',
        default='rainbow_wave',
        choices=['test', 'rainbow_wave', 'rainbow_cycle'],
        help='Initial pattern to display'
    )
    parser.add_argument(
        '--config', '-c',
        default='config/led_config.yaml',
        help='Path to LED configuration file'
    )
    parser.add_argument(
        '--brightness', '-b',
        type=int,
        default=128,
        help='Global brightness (0-255)'
    )
    
    args = parser.parse_args()
    
    # Create and run application
    app = MushroomLights(args.config)
    
    # Set initial brightness
    app.controller.set_brightness(args.brightness)
    
    # Set initial pattern
    if args.pattern:
        app.switch_pattern(args.pattern)
    
    # Run
    app.run()


if __name__ == '__main__':
    main()
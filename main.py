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
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Setup logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from hardware.led_controller import LEDController
from patterns import PatternRegistry

# Constants
HEALTH_LOG_INTERVAL = 10.0  # Seconds between health logs
HEALTH_CHECK_INTERVAL = 1.0  # Seconds between health checks


class MushroomLights:
    """Main application controller"""
    
    def __init__(self, config_path: str = "config/led_config.yaml"):
        logger.info("Starting Mushroom Lights...")
        
        # Initialize LED controller
        self.controller = LEDController(config_path)
        
        # Pattern registry
        self.registry = PatternRegistry()
        
        # Control flags
        self.running = True
        
        # Setup signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("Mushroom Lights initialized")
    
    def signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        logger.info("Shutdown signal received")
        self.running = False
    
    def set_patterns(self, cap_pattern_name: str, stem_pattern_name: str) -> bool:
        """
        Set patterns for cap and stem
        
        Args:
            cap_pattern_name: Pattern name for cap LEDs (450 pixels)
            stem_pattern_name: Pattern name for stem LEDs (250 pixels)
            
        Returns:
            True if both patterns set successfully
        """
        success = True
        
        # Create cap pattern
        if cap_pattern_name:
            cap_pattern = self.registry.create_pattern(cap_pattern_name, 450)
            if cap_pattern:
                self.controller.set_cap_pattern(cap_pattern)
                logger.info(f"Set cap pattern: {cap_pattern_name}")
            else:
                logger.error(f"Failed to create cap pattern: {cap_pattern_name}")
                success = False
        
        # Create stem pattern
        if stem_pattern_name:
            stem_pattern = self.registry.create_pattern(stem_pattern_name, 250)
            if stem_pattern:
                self.controller.set_stem_pattern(stem_pattern)
                logger.info(f"Set stem pattern: {stem_pattern_name}")
            else:
                logger.error(f"Failed to create stem pattern: {stem_pattern_name}")
                success = False
        
        return success
    
    def run(self):
        """Main application loop - monitors health"""
        logger.info("Starting LED controller threads...")
        
        # Start the controller (starts all threads)
        self.controller.start()
        
        # Health monitoring
        last_health_log = time.time()
        last_health_check = time.time()
        
        try:
            logger.info("Controller running. Press Ctrl+C to stop.")
            
            while self.running:
                current_time = time.time()
                
                # Check health periodically
                if current_time - last_health_check >= HEALTH_CHECK_INTERVAL:
                    health = self.controller.get_health()
                    
                    # Check for thread failures
                    cap_health = health['cap']
                    stem_health = health['stem']
                    
                    if not cap_health['pattern_alive'] or not cap_health['spi_alive']:
                        logger.error("Cap controller thread died!")
                        self.running = False
                        break
                    
                    if not stem_health['pattern_alive'] or not stem_health['spi_alive']:
                        logger.error("Stem controller thread died!")
                        self.running = False
                        break
                    
                    # Check for excessive errors
                    if cap_health['pattern_errors'] >= 3 or cap_health['spi_errors'] >= 3:
                        logger.error("Cap controller has too many errors!")
                        self.running = False
                        break
                    
                    if stem_health['pattern_errors'] >= 3 or stem_health['spi_errors'] >= 3:
                        logger.error("Stem controller has too many errors!")
                        self.running = False
                        break
                    
                    last_health_check = current_time
                
                # Log performance periodically
                if current_time - last_health_log >= HEALTH_LOG_INTERVAL:
                    stats = self.controller.get_stats()
                    logger.info(
                        f"Performance | Cap: {stats['cap_fps']:.1f} FPS ({stats['cap_frames']} frames) | "
                        f"Stem: {stats['stem_fps']:.1f} FPS ({stats['stem_frames']} frames) | "
                        f"Errors: {stats['cap_errors'] + stats['stem_errors']}"
                    )
                    
                    # Export performance metrics to JSON
                    try:
                        # Get pattern names safely
                        cap_pattern_name = None
                        stem_pattern_name = None
                        
                        try:
                            if hasattr(self.controller.cap_controller, 'pattern') and self.controller.cap_controller.pattern:
                                cap_pattern_name = self.controller.cap_controller.pattern.__class__.__name__
                        except AttributeError:
                            pass
                        
                        try:
                            if hasattr(self.controller.stem_controller, 'pattern') and self.controller.stem_controller.pattern:
                                stem_pattern_name = self.controller.stem_controller.pattern.__class__.__name__
                        except AttributeError:
                            pass
                        
                        metrics = {
                            'timestamp': current_time,
                            'cap': self.controller.cap_controller.get_performance_details(),
                            'stem': self.controller.stem_controller.get_performance_details(),
                            'patterns': {
                                'cap': cap_pattern_name,
                                'stem': stem_pattern_name
                            }
                        }
                        with open('/tmp/mushroom-metrics.json', 'w') as f:
                            json.dump(metrics, f, indent=2)
                    except Exception as e:
                        logger.debug(f"Failed to export metrics: {e}")
                    
                    last_health_log = current_time
                
                # Sleep briefly to avoid busy waiting
                time.sleep(0.1)
        
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
        
        finally:
            # Clean shutdown
            logger.info("Shutting down...")
            self.controller.cleanup()
            logger.info("Shutdown complete")


def main():
    """Entry point"""
    # Get available patterns from registry
    available_patterns = PatternRegistry().list_patterns()
    
    parser = argparse.ArgumentParser(description='Mushroom LED Controller')
    parser.add_argument(
        '--cap-pattern',
        default=None,
        choices=available_patterns if available_patterns else None,
        help='Pattern for cap LEDs (450 pixels)'
    )
    parser.add_argument(
        '--stem-pattern',
        default=None,
        choices=available_patterns if available_patterns else None,
        help='Pattern for stem LEDs (250 pixels)'
    )
    parser.add_argument(
        '--pattern', '-p',
        default=None,
        choices=available_patterns if available_patterns else None,
        help='Pattern for both cap and stem (overrides individual patterns)'
    )
    parser.add_argument(
        '--config', '-c',
        default='config/led_config.yaml',
        help='Path to LED configuration file'
    )
    parser.add_argument(
        '--brightness', '-b',
        type=int,
        default=None,
        help='Global brightness 0-255'
    )
    parser.add_argument(
        '--cap-brightness',
        type=int,
        default=None,
        help='Cap brightness 0-255'
    )
    parser.add_argument(
        '--stem-brightness',
        type=int,
        default=None,
        help='Stem brightness 0-255'
    )
    parser.add_argument(
        '--startup-config', '-s',
        default='config/startup.yaml',
        help='Path to startup configuration file'
    )
    parser.add_argument(
        '--no-startup-config',
        action='store_true',
        help='Ignore startup config file'
    )
    parser.add_argument(
        '--list-patterns',
        action='store_true',
        help='List available patterns and exit'
    )
    
    args = parser.parse_args()
    
    # Handle list patterns request
    if args.list_patterns:
        for pattern in available_patterns:
            print(pattern)
        sys.exit(0)
    
    # Determine patterns to use
    cap_pattern = None
    stem_pattern = None
    brightness = 128
    cap_brightness = None
    stem_brightness = None
    
    # Load startup configuration if it exists and not disabled
    if not args.no_startup_config and Path(args.startup_config).exists():
        try:
            import yaml
            with open(args.startup_config, 'r') as f:
                startup = yaml.safe_load(f)
                cap_pattern = startup.get('cap_pattern', 'rainbow')
                stem_pattern = startup.get('stem_pattern', 'rainbow')
                brightness = startup.get('brightness', 128)
                cap_brightness = startup.get('cap_brightness')
                stem_brightness = startup.get('stem_brightness')
                logger.info(f"Loaded startup config from {args.startup_config}")
        except Exception as e:
            logger.warning(f"Could not load startup config: {e}")
    
    # Command line arguments override startup config
    if args.pattern:
        # Same pattern for both
        cap_pattern = args.pattern
        stem_pattern = args.pattern
    else:
        # Individual patterns
        if args.cap_pattern:
            cap_pattern = args.cap_pattern
        if args.stem_pattern:
            stem_pattern = args.stem_pattern
    
    # Default patterns if none specified
    if not cap_pattern:
        cap_pattern = 'rainbow'
        logger.info(f"No cap pattern specified, using default: {cap_pattern}")
    if not stem_pattern:
        stem_pattern = 'rainbow'
        logger.info(f"No stem pattern specified, using default: {stem_pattern}")
    
    # Brightness overrides
    if args.brightness is not None:
        brightness = args.brightness
    if args.cap_brightness is not None:
        cap_brightness = args.cap_brightness
    if args.stem_brightness is not None:
        stem_brightness = args.stem_brightness
    
    # Create and configure application
    app = MushroomLights(args.config)
    
    # Set patterns
    if not app.set_patterns(cap_pattern, stem_pattern):
        logger.error("Failed to set patterns")
        sys.exit(1)
    
    # Set brightness
    if brightness is not None:
        app.controller.set_brightness(brightness)
        logger.info(f"Set global brightness to {brightness}")
    if cap_brightness is not None:
        app.controller.set_cap_brightness(cap_brightness)
        logger.info(f"Set cap brightness to {cap_brightness}")
    if stem_brightness is not None:
        app.controller.set_stem_brightness(stem_brightness)
        logger.info(f"Set stem brightness to {stem_brightness}")
    
    # Run
    app.run()


if __name__ == '__main__':
    main()
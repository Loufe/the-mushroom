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

from hardware.led_controller import LEDController
from patterns import PatternRegistry
from audio.device import AudioDevice
from audio.stream import AudioStream

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
FPS_LOG_INTERVAL = 5.0  # Seconds between FPS logs
TARGET_FPS = 60  # Maximum FPS to prevent CPU waste


class MushroomLights:
    """Main application controller"""
    
    def __init__(self, config_path: str = "config/led_config.yaml"):
        logger.info("Starting Mushroom Lights...")
        
        # Initialize LED controller
        self.controller = LEDController(config_path)
        
        # Load config for audio settings
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Initialize audio if enabled
        self.audio_stream = None
        audio_config = config.get('audio', {})
        if audio_config.get('enabled', False):
            logger.info("Initializing audio capture...")
            try:
                # Find USB audio device
                device_id = AudioDevice.find_usb_device(audio_config.get('device', 'USB'))
                if device_id is not None:
                    # Create audio stream
                    audio_config['device_id'] = device_id
                    self.audio_stream = AudioStream(audio_config)
                    if self.audio_stream.start():
                        logger.info("Audio capture started successfully")
                    else:
                        logger.warning("Failed to start audio stream")
                        self.audio_stream = None
                else:
                    logger.warning("No USB audio device found")
            except Exception as e:
                logger.error(f"Audio initialization failed: {e}")
                self.audio_stream = None
        
        # Pattern registry
        self.registry = PatternRegistry()
        
        # Create pattern instances
        self.patterns = {}
        for pattern_name in self.registry.list_patterns():
            pattern_instance = self.registry.create_pattern(pattern_name, self.controller.total_leds)
            if pattern_instance:
                self.patterns[pattern_name] = pattern_instance
        
        if not self.patterns:
            raise RuntimeError("No patterns available in registry")
        
        # Start with rainbow wave or first available pattern
        self.current_pattern_name = 'rainbow_wave' if 'rainbow_wave' in self.patterns else list(self.patterns.keys())[0]
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
    
    def switch_pattern(self, pattern_name: str) -> bool:
        """Switch to a different pattern"""
        if pattern_name in self.patterns:
            self.current_pattern_name = pattern_name
            self.current_pattern = self.patterns[pattern_name]
            self.current_pattern.reset()
            logger.info(f"Switched to pattern: {pattern_name}")
            return True
        else:
            logger.error(f"Unknown pattern: {pattern_name}. Available patterns: {list(self.patterns.keys())}")
            return False
    
    def run(self):
        """Main application loop"""
        logger.info("Starting main loop...")
        
        # Performance monitoring
        last_log_time = time.time()
        frame_time = 1.0 / TARGET_FPS
        last_frame_time = time.time()
        
        try:
            while self.running:
                current_time = time.time()
                
                # Get pattern output
                pixels = self.current_pattern.render()
                
                # Send to LEDs with error handling
                try:
                    self.controller.set_pixels(pixels)
                    self.controller.present()
                except Exception as e:
                    logger.error(f"Failed to update LEDs: {e}")
                    # Continue running even if LED update fails
                
                # Performance monitoring
                if current_time - last_log_time >= FPS_LOG_INTERVAL:
                    fps = self.controller.get_fps()
                    logger.info(f"Pattern: {self.current_pattern_name} | FPS: {fps:.1f}")
                    last_log_time = current_time
                
                # Frame rate limiting - sleep only if we're ahead of schedule
                frame_duration = current_time - last_frame_time
                if frame_duration < frame_time:
                    time.sleep(frame_time - frame_duration)
                last_frame_time = time.time()
        
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
        
        finally:
            # Clean shutdown
            logger.info("Shutting down...")
            if self.audio_stream:
                self.audio_stream.stop()
            self.controller.cleanup()
            logger.info("Shutdown complete")


def main():
    """Entry point"""
    # Get available patterns from registry
    available_patterns = PatternRegistry().list_patterns()
    
    parser = argparse.ArgumentParser(description='Mushroom LED Controller')
    parser.add_argument(
        '--pattern', '-p',
        default=None,
        choices=available_patterns if available_patterns else None,
        help='Initial pattern to display (overrides startup config)'
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
        help='Global brightness 0-255 (overrides startup config)'
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
    
    # Load startup configuration if it exists and not disabled
    startup_pattern = 'rainbow_wave'
    startup_brightness = 128
    pattern_params = {}
    
    if not args.no_startup_config and Path(args.startup_config).exists():
        try:
            import yaml
            with open(args.startup_config, 'r') as f:
                startup = yaml.safe_load(f)
                startup_pattern = startup.get('pattern', 'rainbow_wave')
                startup_brightness = startup.get('brightness', 128)
                pattern_params = startup.get('pattern_params', {})
                logger.info(f"Loaded startup config from {args.startup_config}")
        except Exception as e:
            logger.warning(f"Could not load startup config: {e}")
    
    # Command line arguments override startup config
    if args.pattern:
        startup_pattern = args.pattern
    if args.brightness is not None:
        startup_brightness = args.brightness
    
    # Create and run application
    app = MushroomLights(args.config)
    
    # Validate and set initial brightness
    if not 0 <= startup_brightness <= 255:
        logger.warning(f"Invalid brightness {startup_brightness}, clamping to range 0-255")
        startup_brightness = max(0, min(255, startup_brightness))
    app.controller.set_brightness(startup_brightness)
    logger.info(f"Set brightness to {startup_brightness}")
    
    # Validate and set initial pattern
    if not app.switch_pattern(startup_pattern):
        logger.warning(f"Pattern '{startup_pattern}' not found, falling back to 'rainbow_wave'")
        app.switch_pattern('rainbow_wave')
    
    # Apply pattern-specific parameters if available
    if app.current_pattern_name in pattern_params:
        for param, value in pattern_params[app.current_pattern_name].items():
            try:
                app.current_pattern.set_param(param, value)
                logger.info(f"Set {app.current_pattern_name}.{param} = {value}")
            except Exception as e:
                logger.error(f"Failed to set parameter {param}: {e}")
    
    # Run
    app.run()


if __name__ == '__main__':
    main()
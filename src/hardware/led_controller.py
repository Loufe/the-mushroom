#!/usr/bin/env python3
"""
LED Controller - Manages dual LED strips with parallel pattern generation and transmission
Raspberry Pi 5 version using dual SPI channels for cap and stem
"""

import yaml
import logging
import time
from typing import Optional, Dict, Any
from .strip_controller import StripController

logger = logging.getLogger(__name__)


class LEDController:
    """Manages cap and stem LED strips with independent patterns"""
    
    def __init__(self, config_path: str = "config/led_config.yaml"):
        """
        Initialize LED controller with configuration
        
        Args:
            config_path: Path to YAML configuration file
        """
        # Load configuration
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        except (FileNotFoundError, yaml.YAMLError) as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            raise
        
        # Validate config
        if not self.config or 'strips' not in self.config:
            raise ValueError(f"Config missing 'strips' section in {config_path}")
        
        # Get hardware and timing configs - fail fast if missing
        if 'hardware' not in self.config:
            raise ValueError(f"Config missing 'hardware' section in {config_path}")
        hardware_config = self.config['hardware']
        
        if 'timing' not in self.config:
            raise ValueError(f"Config missing 'timing' section in {config_path}")
        timing_config = self.config['timing']
        
        # Find cap and stem configurations
        cap_config = None
        stem_config = None
        
        for strip_config in self.config['strips']:
            if strip_config['id'] == 'cap_exterior':
                cap_config = strip_config
            elif strip_config['id'] == 'stem_interior':
                stem_config = strip_config
        
        if not cap_config or not stem_config:
            raise ValueError("Configuration must define both 'cap_exterior' and 'stem_interior' strips")
        
        # Create strip controllers
        self.cap_controller = StripController('cap', cap_config, hardware_config, timing_config)
        self.stem_controller = StripController('stem', stem_config, hardware_config, timing_config)
        
        # Track total LED count for compatibility
        self.total_leds = cap_config['led_count'] + stem_config['led_count']
        
        # Running state
        self.running = False
        
        logger.info(f"LED Controller initialized with {self.total_leds} total LEDs")
        logger.info(f"  Cap: {cap_config['led_count']} LEDs on {cap_config['spi_device']}")
        logger.info(f"  Stem: {stem_config['led_count']} LEDs on {stem_config['spi_device']}")
    
    def set_cap_pattern(self, pattern):
        """
        Set pattern for cap LEDs
        
        Args:
            pattern: Pattern instance for cap (should be 450 LEDs)
        """
        if self.running:
            raise RuntimeError("Cannot change patterns while running")
        
        if pattern.led_count != self.cap_controller.led_count:
            logger.warning(f"Cap pattern expects {pattern.led_count} LEDs but cap has {self.cap_controller.led_count}")
        
        self.cap_controller.set_pattern(pattern)
    
    def set_stem_pattern(self, pattern):
        """
        Set pattern for stem LEDs
        
        Args:
            pattern: Pattern instance for stem (should be 250 LEDs)
        """
        if self.running:
            raise RuntimeError("Cannot change patterns while running")
        
        if pattern.led_count != self.stem_controller.led_count:
            logger.warning(f"Stem pattern expects {pattern.led_count} LEDs but stem has {self.stem_controller.led_count}")
        
        self.stem_controller.set_pattern(pattern)
    
    def start(self):
        """Start pattern generation and SPI transmission threads"""
        if self.running:
            logger.warning("Controller already running")
            return
        
        logger.info("Starting LED controller")
        
        # Start both strip controllers
        self.cap_controller.start()
        self.stem_controller.start()
        
        self.running = True
        logger.info("LED controller started")
    
    def stop(self):
        """Stop all threads and clear LEDs"""
        if not self.running:
            return
        
        logger.info("Stopping LED controller")
        
        # Stop both strip controllers
        self.cap_controller.stop()
        self.stem_controller.stop()
        
        self.running = False
        logger.info("LED controller stopped")
    
    def set_brightness(self, brightness: int):
        """
        Set global brightness for all strips
        
        Args:
            brightness: 0-255 brightness value
        """
        if not 0 <= brightness <= 255:
            logger.warning(f"Brightness {brightness} out of range, clamping to 0-255")
            brightness = max(0, min(255, brightness))
        
        self.cap_controller.set_brightness(brightness)
        self.stem_controller.set_brightness(brightness)
        logger.info(f"Set global brightness to {brightness}")
    
    def set_cap_brightness(self, brightness: int):
        """Set brightness for cap only"""
        self.cap_controller.set_brightness(brightness)
    
    def set_stem_brightness(self, brightness: int):
        """Set brightness for stem only"""
        self.stem_controller.set_brightness(brightness)
    
    def get_health(self) -> Dict[str, Any]:
        """
        Get health status of all components
        
        Returns:
            Dictionary with health information
        """
        return {
            'running': self.running,
            'cap': self.cap_controller.get_health(),
            'stem': self.stem_controller.get_health(),
            'total_leds': self.total_leds
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics
        
        Returns:
            Dictionary with performance metrics
        """
        cap_health = self.cap_controller.get_health()
        stem_health = self.stem_controller.get_health()
        
        return {
            'cap_fps': cap_health['fps'],
            'stem_fps': stem_health['fps'],
            'cap_frames': cap_health['frames_generated'],
            'stem_frames': stem_health['frames_generated'],
            'cap_errors': cap_health['pattern_errors'] + cap_health['spi_errors'],
            'stem_errors': stem_health['pattern_errors'] + stem_health['spi_errors']
        }
    
    def cleanup(self):
        """Clean shutdown of all resources"""
        logger.info("Cleaning up LED controller")
        
        # Stop if running
        self.stop()
        
        # Cleanup strip controllers (closes SPI devices)
        self.cap_controller.cleanup()
        self.stem_controller.cleanup()
        
        logger.info("LED controller cleanup complete")
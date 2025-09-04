#!/usr/bin/env python3
"""
LED Controller - Hardware abstraction layer for WS2811 LED strips
Raspberry Pi 5 version using Pi5Neo library with dual SPI channels
"""

from pi5neo import Pi5Neo
import numpy as np
import time
import yaml
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class LEDStrip:
    """Manages a single LED strip on one SPI channel"""
    
    def __init__(self, config: dict, hardware_config: dict):
        self.id = config['id']
        self.spi_device = config['spi_device']
        self.led_count = config['led_count']
        self.led_start = config['led_start']
        self.led_end = config['led_end']
        self.location = config['location']
        self.description = config['description']
        
        # Hardware settings from config
        self.spi_speed = hardware_config.get('spi_speed_khz', 800)
        self.brightness = hardware_config.get('brightness', 128)
        
        # Initialize Pi5Neo strip
        try:
            self.strip = Pi5Neo(
                spi_device=self.spi_device,
                num_leds=self.led_count, 
                spi_speed_khz=self.spi_speed
            )
            
            # Clear strip on init
            self.clear()
            
            logger.info(f"Initialized strip {self.id} on {self.spi_device} with {self.led_count} LEDs")
        except Exception as e:
            logger.error(f"Failed to initialize strip {self.id}: {e}")
            raise
    
    def set_pixel(self, index: int, color: Tuple[int, int, int]):
        """Set a single pixel color"""
        if 0 <= index < self.led_count:
            r, g, b = color
            # Apply brightness scaling
            r = int(r * self.brightness / 255)
            g = int(g * self.brightness / 255)
            b = int(b * self.brightness / 255)
            self.strip.set_led_color(index, r, g, b)
    
    def set_pixels(self, colors: np.ndarray):
        """Set all pixels from numpy array of RGB values"""
        for i in range(min(len(colors), self.led_count)):
            r, g, b = colors[i]
            # Apply brightness scaling
            r = int(r * self.brightness / 255)
            g = int(g * self.brightness / 255)
            b = int(b * self.brightness / 255)
            self.strip.set_led_color(i, r, g, b)
    
    def show(self):
        """Update the physical LEDs"""
        self.strip.update_strip()
    
    def clear(self):
        """Turn off all LEDs"""
        self.strip.fill_strip(0, 0, 0)
        self.strip.update_strip()
    
    def set_brightness(self, brightness: int):
        """Set global brightness (0-255)"""
        self.brightness = max(0, min(255, brightness))
    
    def fill(self, color: Tuple[int, int, int]):
        """Fill entire strip with one color"""
        r, g, b = color
        # Apply brightness scaling
        r = int(r * self.brightness / 255)
        g = int(g * self.brightness / 255)
        b = int(b * self.brightness / 255)
        self.strip.fill_strip(r, g, b)
        self.strip.update_strip()


class LEDController:
    """Manages multiple LED strips as one logical display"""
    
    def __init__(self, config_path: str = "config/led_config.yaml"):
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Total LED count
        self.total_leds = sum(strip['led_count'] for strip in self.config['strips'])
        
        # Initialize strips
        self.strips = []
        self.strip_map = {}  # Map strip IDs to strip objects
        hardware_config = self.config.get('hardware', {})
        
        for strip_config in self.config['strips']:
            try:
                strip = LEDStrip(strip_config, hardware_config)
                self.strips.append(strip)
                self.strip_map[strip_config['id']] = strip
            except Exception as e:
                logger.error(f"Failed to initialize strip {strip_config['id']}: {e}")
                # Continue with other strips instead of failing completely
        
        if not self.strips:
            raise RuntimeError("No LED strips could be initialized")
        
        # Create unified pixel buffer
        self.pixels = np.zeros((self.total_leds, 3), dtype=np.uint8)
        
        # Performance tracking
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0
        
        logger.info(f"LED Controller initialized with {len(self.strips)} strips, {self.total_leds} total LEDs")
    
    def set_pixel(self, index: int, color: Tuple[int, int, int]):
        """Set a single pixel in the unified buffer"""
        if 0 <= index < self.total_leds:
            self.pixels[index] = color
    
    def set_pixels(self, colors: np.ndarray):
        """Set all pixels from numpy array"""
        if len(colors) == self.total_leds:
            self.pixels = colors.astype(np.uint8)
        else:
            # Handle size mismatch with warning
            logger.warning(f"Pattern provided {len(colors)} pixels but controller expects {self.total_leds}")
            min_len = min(len(colors), self.total_leds)
            self.pixels[:min_len] = colors[:min_len].astype(np.uint8)
            # Clear any remaining pixels if pattern provided fewer
            if len(colors) < self.total_leds:
                self.pixels[min_len:] = 0
    
    def update(self):
        """Push pixel buffer to all strips"""
        for strip in self.strips:
            try:
                # Get the slice of pixels for this strip
                start = strip.led_start
                end = strip.led_end + 1
                strip_pixels = self.pixels[start:end]
                strip.set_pixels(strip_pixels)
                strip.show()
            except Exception as e:
                logger.error(f"Failed to update strip {strip.id}: {e}")
                # Continue updating other strips even if one fails
        
        # Update FPS counter
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            self.current_fps = self.frame_count / (current_time - self.last_fps_time)
            self.frame_count = 0
            self.last_fps_time = current_time
    
    def clear(self):
        """Clear all LEDs"""
        self.pixels.fill(0)
        for strip in self.strips:
            strip.clear()
    
    def set_brightness(self, brightness: int):
        """Set global brightness for all strips (0-255)"""
        # Validate brightness range
        if not 0 <= brightness <= 255:
            logger.warning(f"Brightness {brightness} out of range, clamping to 0-255")
            brightness = max(0, min(255, brightness))
        
        for strip in self.strips:
            try:
                strip.set_brightness(brightness)
            except Exception as e:
                logger.error(f"Failed to set brightness for strip {strip.id}: {e}")
    
    def get_fps(self) -> float:
        """Get current FPS"""
        return self.current_fps
    
    def get_strip(self, strip_id: str) -> Optional[LEDStrip]:
        """Get a specific strip by ID"""
        return self.strip_map.get(strip_id)
    
    def set_stem_pixels(self, colors: np.ndarray):
        """Set pixels for the stem interior only"""
        strip = self.strip_map.get('stem_interior')
        if strip:
            try:
                if len(colors) != strip.led_count:
                    logger.warning(f"Stem pixels: expected {strip.led_count} pixels, got {len(colors)}")
                strip.set_pixels(colors)
                strip.show()
            except Exception as e:
                logger.error(f"Failed to update stem pixels: {e}")
    
    def set_cap_pixels(self, colors: np.ndarray):
        """Set pixels for the cap exterior only"""
        strip = self.strip_map.get('cap_exterior')
        if strip:
            try:
                if len(colors) != strip.led_count:
                    logger.warning(f"Cap pixels: expected {strip.led_count} pixels, got {len(colors)}")
                strip.set_pixels(colors)
                strip.show()
            except Exception as e:
                logger.error(f"Failed to update cap pixels: {e}")
    
    def cleanup(self):
        """Clean shutdown"""
        self.clear()
        logger.info("LED Controller shutdown complete")
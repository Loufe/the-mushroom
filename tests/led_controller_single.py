#!/usr/bin/env python3
"""
Single Strip LED Controller - Simplified controller for testing with one strip
Raspberry Pi 5 version using Pi5Neo library
"""

from pi5neo import Pi5Neo
import numpy as np
import time
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class SingleStripController:
    """Simplified controller for single strip testing"""
    
    def __init__(self, spi_device: str = '/dev/spidev0.0', led_count: int = 200, brightness: int = 128):
        self.spi_device = spi_device
        self.led_count = led_count
        self.total_leds = led_count  # For compatibility with patterns
        self.brightness = brightness
        
        # Initialize Pi5Neo strip
        try:
            self.strip = Pi5Neo(
                spi_device=spi_device,
                num_leds=led_count,
                spi_speed_khz=800
            )
            
            # Clear on init
            self.clear()
            
        except Exception as e:
            logger.error(f"Failed to initialize strip on {spi_device}: {e}")
            raise
        
        # Pixel buffer
        self.pixels = np.zeros((led_count, 3), dtype=np.uint8)
        
        # FPS tracking
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0
        
        logger.info(f"Single strip controller initialized: {spi_device}, {led_count} LEDs")
    
    def set_pixel(self, index: int, color: Tuple[int, int, int]):
        """Set a single pixel"""
        if 0 <= index < self.led_count:
            self.pixels[index] = color
    
    def set_pixels(self, colors: np.ndarray):
        """Set all pixels from numpy array"""
        if len(colors) >= self.led_count:
            self.pixels = colors[:self.led_count].astype(np.uint8)
        else:
            self.pixels[:len(colors)] = colors.astype(np.uint8)
    
    def update(self):
        """Push pixels to strip"""
        for i in range(self.led_count):
            r, g, b = self.pixels[i]
            # Apply brightness scaling
            r = int(r * self.brightness / 255)
            g = int(g * self.brightness / 255)
            b = int(b * self.brightness / 255)
            self.strip.set_led_color(i, r, g, b)
        self.strip.update_strip()
        
        # Update FPS
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            self.current_fps = self.frame_count / (current_time - self.last_fps_time)
            self.frame_count = 0
            self.last_fps_time = current_time
    
    def clear(self):
        """Clear all LEDs"""
        self.pixels.fill(0)
        self.strip.fill_strip(0, 0, 0)
        self.strip.update_strip()
    
    def set_brightness(self, brightness: int):
        """Set brightness (0-255)"""
        self.brightness = max(0, min(255, brightness))
    
    def get_fps(self) -> float:
        """Get current FPS"""
        return self.current_fps
    
    def cleanup(self):
        """Clean shutdown"""
        self.clear()
        logger.info("Controller shutdown complete")
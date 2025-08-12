#!/usr/bin/env python3
"""
Single Strip LED Controller - Simplified controller for testing with one strip
Use this when testing with a single GPIO pin
"""

from rpi_ws281x import PixelStrip, Color
import numpy as np
import time
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class SingleStripController:
    """Simplified controller for single strip testing"""
    
    def __init__(self, gpio_pin: int = 10, led_count: int = 200, brightness: int = 128):
        self.gpio_pin = gpio_pin
        self.led_count = led_count
        self.total_leds = led_count  # For compatibility with patterns
        
        # Hardware settings
        freq_hz = 800000
        invert = False
        
        # GPIO-specific settings
        if gpio_pin == 10:
            channel = 0
            dma_channel = 10  # SPI
        elif gpio_pin in [12, 18]:
            channel = 0  # PWM0
            dma_channel = 5
        elif gpio_pin == 21:
            channel = 1  # PWM1
            dma_channel = 5
        else:
            # Fallback for testing
            channel = 0
            dma_channel = 10
            logger.warning(f"GPIO {gpio_pin} not in standard config, using defaults")
        
        # Initialize strip
        self.strip = PixelStrip(
            led_count, gpio_pin, freq_hz, dma_channel,
            invert, brightness, channel
        )
        
        self.strip.begin()
        
        # Pixel buffer
        self.pixels = np.zeros((led_count, 3), dtype=np.uint8)
        
        # FPS tracking
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0
        
        logger.info(f"Single strip controller initialized: GPIO {gpio_pin}, {led_count} LEDs")
    
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
            self.strip.setPixelColor(i, Color(int(r), int(g), int(b)))
        self.strip.show()
        
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
        self.update()
    
    def set_brightness(self, brightness: int):
        """Set brightness (0-255)"""
        self.strip.setBrightness(brightness)
    
    def get_fps(self) -> float:
        """Get current FPS"""
        return self.current_fps
    
    def cleanup(self):
        """Clean shutdown"""
        self.clear()
        logger.info("Controller shutdown complete")
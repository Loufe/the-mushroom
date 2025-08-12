#!/usr/bin/env python3
"""
LED Controller - Hardware abstraction layer for WS2811 LED strips
Manages multiple strips across different GPIO pins
"""

from rpi_ws281x import PixelStrip, Color
import numpy as np
import time
import yaml
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class LEDStrip:
    """Manages a single LED strip on one GPIO pin"""
    
    def __init__(self, config: dict, hardware_config: dict):
        self.id = config['id']
        self.gpio_pin = config['gpio_pin']
        self.led_count = config['led_count']
        self.led_start = config['led_start']
        self.led_end = config['led_end']
        
        # Hardware settings from config
        self.freq_hz = hardware_config.get('freq_hz', 800000)
        self.invert = hardware_config.get('invert', False)
        self.brightness = hardware_config.get('brightness', 128)
        
        # GPIO-specific channel and DMA selection
        # GPIO 10 uses SPI (channel 0, DMA 10)
        # GPIO 12, 18 use PWM0 (channel 0, DMA 5)
        # GPIO 21 uses PWM1 (channel 1, DMA 5)
        if self.gpio_pin == 10:
            self.channel = 0
            self.dma_channel = 10  # SPI uses DMA 10
        elif self.gpio_pin in [12, 18]:
            self.channel = 0  # PWM0
            self.dma_channel = 5
        elif self.gpio_pin == 21:
            self.channel = 1  # PWM1
            self.dma_channel = 5
        else:
            raise ValueError(f"Unsupported GPIO pin: {self.gpio_pin}")
        
        # Initialize the strip
        self.strip = PixelStrip(
            self.led_count,
            self.gpio_pin,
            self.freq_hz,
            self.dma_channel,
            self.invert,
            self.brightness,
            self.channel
        )
        
        self.strip.begin()
        logger.info(f"Initialized strip {self.id} on GPIO {self.gpio_pin} with {self.led_count} LEDs")
    
    def set_pixel(self, index: int, color: Tuple[int, int, int]):
        """Set a single pixel color"""
        if 0 <= index < self.led_count:
            self.strip.setPixelColor(index, Color(*color))
    
    def set_pixels(self, colors: np.ndarray):
        """Set all pixels from numpy array of RGB values"""
        for i in range(min(len(colors), self.led_count)):
            r, g, b = colors[i]
            self.strip.setPixelColor(i, Color(int(r), int(g), int(b)))
    
    def show(self):
        """Update the physical LEDs"""
        self.strip.show()
    
    def clear(self):
        """Turn off all LEDs"""
        for i in range(self.led_count):
            self.strip.setPixelColor(i, Color(0, 0, 0))
        self.strip.show()
    
    def set_brightness(self, brightness: int):
        """Set global brightness (0-255)"""
        self.strip.setBrightness(brightness)


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
        hardware_config = self.config.get('hardware', {})
        
        for strip_config in self.config['strips']:
            try:
                strip = LEDStrip(strip_config, hardware_config)
                self.strips.append(strip)
            except Exception as e:
                logger.error(f"Failed to initialize strip {strip_config['id']}: {e}")
                # Continue with other strips instead of failing completely
        
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
            # Handle size mismatch
            min_len = min(len(colors), self.total_leds)
            self.pixels[:min_len] = colors[:min_len].astype(np.uint8)
    
    def update(self):
        """Push pixel buffer to all strips"""
        for strip in self.strips:
            # Get the slice of pixels for this strip
            start = strip.led_start
            end = strip.led_end + 1
            strip_pixels = self.pixels[start:end]
            strip.set_pixels(strip_pixels)
            strip.show()
        
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
        self.update()
    
    def set_brightness(self, brightness: int):
        """Set global brightness for all strips (0-255)"""
        for strip in self.strips:
            strip.set_brightness(brightness)
    
    def get_fps(self) -> float:
        """Get current FPS"""
        return self.current_fps
    
    def cleanup(self):
        """Clean shutdown"""
        self.clear()
        logger.info("LED Controller shutdown complete")
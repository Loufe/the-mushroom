#!/usr/bin/env python3
"""
Rainbow Patterns - Various rainbow effects for LED strips
"""

import numpy as np
from typing import Dict, Any
from .base import Pattern
from .registry import PatternRegistry
from effects.colors import hsv_to_rgb


@PatternRegistry.register("rainbow_wave")
class RainbowWave(Pattern):
    """Rainbow wave that travels along the LED strip"""
    
    def get_default_params(self) -> Dict[str, Any]:
        return {
            'rainbow_count': 1.0,   # Number of complete rainbows visible (1.0 = one full rainbow)
            'cycle_time': 10.0,     # Seconds for pattern to complete one full cycle
            'brightness': 1.0,      # 0-1 brightness
            'saturation': 1.0,      # 0-1 color saturation
        }
    
    def update(self, delta_time: float) -> np.ndarray:
        # Calculate phase (0-1) based on time
        phase = (self.get_time() / self.params['cycle_time']) % 1.0
        
        # Create normalized position array (0-1 across strip)
        positions = np.arange(self.led_count) / self.led_count
        
        # Calculate hue for each LED
        # rainbow_count controls how many rainbows fit across the strip
        # phase shifts the pattern over time
        hues = (((positions + phase) * self.params['rainbow_count']) % 1.0) * 360
        
        # Convert HSV to RGB
        self.pixels = hsv_to_rgb(
            hues, 
            self.params['saturation'], 
            self.params['brightness']
        )
        
        return self.pixels


@PatternRegistry.register("rainbow_cycle")
class RainbowCycle(Pattern):
    """All LEDs cycle through rainbow together"""
    
    def get_default_params(self) -> Dict[str, Any]:
        return {
            'cycle_time': 5.0,      # Seconds per complete rainbow cycle
            'brightness': 1.0,      # 0-1 brightness
            'saturation': 1.0,      # 0-1 color saturation
        }
    
    def update(self, delta_time: float) -> np.ndarray:
        # Calculate current hue based on time
        hue = (self.get_time() / self.params['cycle_time']) * 360
        
        # All LEDs get the same color
        hues = np.full(self.led_count, hue)
        
        # Convert HSV to RGB
        self.pixels = hsv_to_rgb(
            hues,
            self.params['saturation'],
            self.params['brightness']
        )
        
        return self.pixels
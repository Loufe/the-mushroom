#!/usr/bin/env python3
"""
Rainbow Patterns - Various rainbow effects for LED strips
"""

import numpy as np
from typing import Dict, Any
from .base import Pattern
from .registry import PatternRegistry
from effects.colors import hsv_to_rgb


@PatternRegistry.register("rainbow")
class RainbowWave(Pattern):
    """Rainbow wave that travels along the LED strip"""
    
    def get_default_params(self) -> Dict[str, Any]:
        return {
            'rainbow_count': 0.3,   # Number of complete rainbows visible (0.3 = partial rainbow for smooth gradient)
            'cycle_time': 30.0,     # Seconds for pattern to complete one full cycle
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
        
        # Convert HSV to RGB with hardware brightness applied
        self.pixels = hsv_to_rgb(
            hues, 
            self.params['saturation'], 
            self.brightness
        )
        
        return self.pixels



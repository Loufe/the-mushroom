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
            'wave_length': 100,     # LEDs per complete rainbow
            'speed': 50.0,          # LEDs per second travel speed
            'brightness': 1.0,      # 0-1 brightness
            'saturation': 1.0,      # 0-1 color saturation
        }
    
    def update(self, delta_time: float) -> np.ndarray:
        # Calculate position offset based on time and speed
        offset = self.get_time() * self.params['speed']
        
        # Create position array for all LEDs
        positions = np.arange(self.led_count)
        
        # Calculate hue for each LED (0-360 degrees)
        hues = ((positions + offset) / self.params['wave_length']) * 360
        
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
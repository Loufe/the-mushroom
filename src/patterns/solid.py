#!/usr/bin/env python3
"""
Solid Color Pattern - Simple single color pattern
"""

import numpy as np
from typing import Dict, Any
from .base import Pattern
from .registry import PatternRegistry


@PatternRegistry.register("solid")
class SolidPattern(Pattern):
    """Display a solid color across all LEDs"""
    
    def get_default_params(self) -> Dict[str, Any]:
        return {
            'red': 255,
            'green': 0,
            'blue': 0
        }
    
    def update(self, delta_time: float) -> np.ndarray:
        # Set all LEDs to the configured solid color
        self.pixels[:] = [
            self.params['red'],
            self.params['green'],
            self.params['blue']
        ]
        return self.pixels


@PatternRegistry.register("breathing")  
class BreathingPattern(Pattern):
    """Breathing effect - fades in and out smoothly"""
    
    def get_default_params(self) -> Dict[str, Any]:
        return {
            'color': (0, 100, 255),  # Default cyan-blue
            'cycle_time': 3.0,  # Seconds per breath
            'min_brightness': 0.1,  # Minimum brightness (never fully off)
            'max_brightness': 1.0   # Maximum brightness
        }
    
    def update(self, delta_time: float) -> np.ndarray:
        # Calculate breathing intensity using sine wave
        import math
        phase = (self.get_time() / self.params['cycle_time']) * 2 * math.pi
        # Use sine squared for smoother breathing
        intensity = (math.sin(phase) + 1) / 2  # 0 to 1
        
        # Scale between min and max brightness
        min_b = self.params['min_brightness']
        max_b = self.params['max_brightness']
        brightness = min_b + (max_b - min_b) * intensity
        
        # Apply to color
        r, g, b = self.params['color']
        self.pixels[:] = [
            int(r * brightness),
            int(g * brightness),
            int(b * brightness)
        ]
        return self.pixels
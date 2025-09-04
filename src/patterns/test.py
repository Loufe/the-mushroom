#!/usr/bin/env python3
"""
Test Pattern - Simple RGB cycle for testing LED functionality
"""

import numpy as np
from typing import Dict, Any
from .base import Pattern
from .registry import PatternRegistry


@PatternRegistry.register("test")
class TestPattern(Pattern):
    """Simple test pattern - all LEDs cycle through red, green, blue"""
    
    def get_default_params(self) -> Dict[str, Any]:
        return {
            'cycle_time': 3.0  # Seconds per complete cycle
        }
    
    def update(self, delta_time: float) -> np.ndarray:
        # Calculate which color to show (0=red, 1=green, 2=blue)
        phase = (self.get_time() / self.params['cycle_time']) % 3
        color_index = int(phase)
        
        # Set all LEDs to the same color
        self.pixels.fill(0)
        self.pixels[:, color_index] = 255
        
        return self.pixels
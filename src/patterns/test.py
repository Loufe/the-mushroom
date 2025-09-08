#!/usr/bin/env python3
"""
Test Pattern - Comprehensive hardware test sequence
"""

import numpy as np
from typing import Dict, Any
from .base import Pattern
from .registry import PatternRegistry


@PatternRegistry.register("test")
class TestPattern(Pattern):
    """Hardware test pattern - RGB colors then white at 5 brightness levels"""
    
    def get_default_params(self) -> Dict[str, Any]:
        return {
            'step_duration': 3.0  # Seconds per test step
        }
    
    def update(self, delta_time: float) -> np.ndarray:
        step_time = self.params['step_duration']
        elapsed = self.get_time()
        
        # Test sequence:
        # 0-3s: Red
        # 3-6s: Green  
        # 6-9s: Blue
        # 9-12s: White 20% (51/255)
        # 12-15s: White 40% (102/255)
        # 15-18s: White 60% (153/255)
        # 18-21s: White 80% (204/255)
        # 21-24s: White 100% (255/255)
        # Then repeat
        
        total_cycle = 8 * step_time
        phase = elapsed % total_cycle
        step = int(phase / step_time)
        
        # Apply brightness to all colors
        if step == 0:  # Red
            self.pixels[:] = [255 * self.brightness, 0, 0]
        elif step == 1:  # Green
            self.pixels[:] = [0, 255 * self.brightness, 0]
        elif step == 2:  # Blue
            self.pixels[:] = [0, 0, 255 * self.brightness]
        elif step == 3:  # White 20%
            level = int(51 * self.brightness)
            self.pixels[:] = [level, level, level]
        elif step == 4:  # White 40%
            level = int(102 * self.brightness)
            self.pixels[:] = [level, level, level]
        elif step == 5:  # White 60%
            level = int(153 * self.brightness)
            self.pixels[:] = [level, level, level]
        elif step == 6:  # White 80%
            level = int(204 * self.brightness)
            self.pixels[:] = [level, level, level]
        elif step == 7:  # White 100%
            level = int(255 * self.brightness)
            self.pixels[:] = [level, level, level]
        else:
            raise RuntimeError(f"Test pattern logic error: invalid step {step}")
        
        return self.pixels
#!/usr/bin/env python3
"""
Base Pattern Class - Abstract base for all LED patterns
"""

from abc import ABC, abstractmethod
import numpy as np
import time
from typing import Optional, Dict, Any


class Pattern(ABC):
    """Abstract base class for all LED patterns"""
    
    def __init__(self, led_count: int, fps: float = 30.0):
        self.led_count = led_count
        self.fps = fps
        self.frame_time = 1.0 / fps
        
        # Pattern state
        self.start_time = time.time()
        self.frame_number = 0
        self.last_update = time.time()
        
        # Output buffer
        self.pixels = np.zeros((led_count, 3), dtype=np.uint8)
        
        # Pattern parameters (can be modified at runtime)
        self.params = self.get_default_params()
    
    @abstractmethod
    def get_default_params(self) -> Dict[str, Any]:
        """Return default parameters for this pattern"""
        pass
    
    @abstractmethod
    def update(self, delta_time: float) -> np.ndarray:
        """
        Update the pattern and return pixel colors
        
        Args:
            delta_time: Time since last update in seconds
            
        Returns:
            numpy array of shape (led_count, 3) with RGB values 0-255
        """
        pass
    
    def render(self) -> np.ndarray:
        """Main render loop - handles timing and calls update()"""
        current_time = time.time()
        delta_time = current_time - self.last_update
        
        # Only update if enough time has passed
        if delta_time >= self.frame_time:
            self.pixels = self.update(delta_time)
            self.last_update = current_time
            self.frame_number += 1
        
        return self.pixels
    
    def set_param(self, name: str, value: Any):
        """Set a pattern parameter"""
        if name in self.params:
            self.params[name] = value
    
    def get_time(self) -> float:
        """Get time since pattern started"""
        return time.time() - self.start_time
    
    def reset(self):
        """Reset pattern to initial state"""
        self.start_time = time.time()
        self.frame_number = 0
        self.last_update = time.time()
        self.pixels.fill(0)


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
#!/usr/bin/env python3
"""
Rainbow Patterns - Various rainbow effects for LED strips
"""

import numpy as np
from typing import Dict, Any
from .base import Pattern
from .registry import PatternRegistry


def hsv_to_rgb(h: np.ndarray, s: float = 1.0, v: float = 1.0) -> np.ndarray:
    """
    Convert HSV to RGB
    h: hue (0-360)
    s: saturation (0-1)
    v: value/brightness (0-1)
    Returns RGB values 0-255
    """
    h = h % 360
    c = v * s
    x = c * (1 - np.abs((h / 60) % 2 - 1))
    m = v - c
    
    # Create RGB array
    rgb = np.zeros((len(h), 3))
    
    # Determine RGB based on hue sector
    mask1 = (h >= 0) & (h < 60)
    mask2 = (h >= 60) & (h < 120)
    mask3 = (h >= 120) & (h < 180)
    mask4 = (h >= 180) & (h < 240)
    mask5 = (h >= 240) & (h < 300)
    mask6 = (h >= 300) & (h < 360)
    
    rgb[mask1] = np.column_stack([c[mask1], x[mask1], np.zeros(np.sum(mask1))])
    rgb[mask2] = np.column_stack([x[mask2], c[mask2], np.zeros(np.sum(mask2))])
    rgb[mask3] = np.column_stack([np.zeros(np.sum(mask3)), c[mask3], x[mask3]])
    rgb[mask4] = np.column_stack([np.zeros(np.sum(mask4)), x[mask4], c[mask4]])
    rgb[mask5] = np.column_stack([x[mask5], np.zeros(np.sum(mask5)), c[mask5]])
    rgb[mask6] = np.column_stack([c[mask6], np.zeros(np.sum(mask6)), x[mask6]])
    
    rgb = (rgb + m[:, np.newaxis]) * 255
    return rgb.astype(np.uint8)


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
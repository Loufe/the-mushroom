#!/usr/bin/env python3
"""
Color utilities and predefined palettes for the mushroom
"""

import numpy as np
from typing import Tuple, List


# Mushroom-inspired color palettes (from research document)
PALETTES = {
    'mushroom_magic': [
        (36, 40, 25),    # #242819 - Dark moss
        (44, 31, 57),    # #2c1f39 - Deep purple
        (117, 117, 79),  # #75754f - Olive
        (130, 102, 153), # #826699 - Lavender
        (220, 199, 255), # #dcc7ff - Light purple
    ],
    'earth_tones': [
        (168, 156, 144), # #A89C90 - Warm gray
        (215, 196, 171), # #D7C4AB - Beige
        (189, 172, 163), # #BDACA3 - Dusty rose
    ],
    'bioluminescent': [
        (0, 255, 146),   # Cyan-green glow
        (64, 255, 178),  # Lighter cyan
        (0, 200, 100),   # Deep green
    ],
    'fire': [
        (255, 0, 0),     # Red
        (255, 128, 0),   # Orange
        (255, 255, 0),   # Yellow
        (255, 64, 0),    # Red-orange
    ],
    'ocean': [
        (0, 50, 150),    # Deep blue
        (0, 100, 200),   # Medium blue
        (0, 150, 255),   # Light blue
        (100, 200, 255), # Sky blue
    ],
    'forest': [
        (34, 139, 34),   # Forest green
        (0, 100, 0),     # Dark green
        (144, 238, 144), # Light green
        (107, 142, 35),  # Olive drab
    ],
}


def interpolate_color(color1: Tuple[int, int, int], 
                     color2: Tuple[int, int, int], 
                     t: float) -> Tuple[int, int, int]:
    """
    Linearly interpolate between two colors
    t: 0.0 = color1, 1.0 = color2
    """
    t = np.clip(t, 0.0, 1.0)
    r = int(color1[0] * (1 - t) + color2[0] * t)
    g = int(color1[1] * (1 - t) + color2[1] * t)
    b = int(color1[2] * (1 - t) + color2[2] * t)
    return (r, g, b)


def gradient(colors: List[Tuple[int, int, int]], 
            led_count: int) -> np.ndarray:
    """
    Create a smooth gradient across LEDs using multiple colors
    """
    if len(colors) < 2:
        raise ValueError("Need at least 2 colors for gradient")
    
    # Handle edge cases
    if led_count <= 0:
        return np.zeros((0, 3), dtype=np.uint8)
    
    result = np.zeros((led_count, 3), dtype=np.uint8)
    
    # Special case: single LED
    if led_count == 1:
        result[0] = colors[0]
        return result
    
    # Divide LEDs into segments
    segment_size = led_count / (len(colors) - 1)
    
    for i in range(led_count):
        # Find which segment we're in
        segment = min(int(i / segment_size), len(colors) - 2)
        local_pos = (i - segment * segment_size) / segment_size
        
        # Interpolate between segment colors
        color = interpolate_color(colors[segment], colors[segment + 1], local_pos)
        result[i] = color
    
    return result


def apply_brightness(pixels: np.ndarray, brightness: float) -> np.ndarray:
    """
    Apply brightness scaling to pixel array
    brightness: 0.0 = off, 1.0 = full brightness
    """
    brightness = np.clip(brightness, 0.0, 1.0)
    return (pixels * brightness).astype(np.uint8)


def fade(pixels: np.ndarray, fade_amount: float) -> np.ndarray:
    """
    Fade pixels towards black
    fade_amount: 0.0 = no fade, 1.0 = completely black
    """
    fade_amount = np.clip(fade_amount, 0.0, 1.0)
    return (pixels * (1.0 - fade_amount)).astype(np.uint8)
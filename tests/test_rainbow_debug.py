#!/usr/bin/env python3
"""
Debug test to understand rainbow color issue
"""

import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from patterns.rainbow import RainbowWave
import numpy as np

# Create rainbow pattern
pattern = RainbowWave(10)  # Just 10 LEDs for easy debugging

# Generate one frame
pixels = pattern.render()

print("Rainbow pixel values (first 10 LEDs):")
print("LED | R    G    B")
print("----|-------------")
for i in range(min(10, len(pixels))):
    r, g, b = pixels[i]
    print(f"{i:3} | {r:3} {g:3} {b:3}")

print("\nIf these appear as mostly GREEN on your LEDs,")
print("it means your strips are RGB order, not GRB.")
print("\nThe high RED values are being sent to the GREEN channel.")

# Check movement
print("\n" + "="*50)
print("Testing movement speed...")
start_pixels = pattern.render().copy()
time.sleep(1.0)  # Wait 1 second
end_pixels = pattern.render()

# Check if pixels changed
if np.array_equal(start_pixels, end_pixels):
    print("WARNING: No movement detected after 1 second!")
    print("The pattern timing might be broken.")
else:
    diff = np.sum(np.abs(end_pixels - start_pixels))
    print(f"Movement detected: {diff:.1f} total change after 1 second")
    print("(30-second cycle = very slow movement)")
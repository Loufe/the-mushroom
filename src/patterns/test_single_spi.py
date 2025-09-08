#!/usr/bin/env python3
"""
Minimal Single SPI Test - Tests if the issue is dual-SPI interference
This is the simplest possible test to isolate the problem
"""

import sys
import os
import time
from pathlib import Path

# Check if running as root
if os.geteuid() != 0:
    print("ERROR: This script requires root access for SPI")
    print("Please run with: sudo mushroom-env/bin/python tests/test_single_spi.py")
    sys.exit(1)

try:
    from pi5neo import Pi5Neo
except ImportError:
    print("ERROR: pi5neo library not found")
    print("Please ensure you're using the virtual environment:")
    print("  sudo mushroom-env/bin/python tests/test_single_spi.py")
    sys.exit(1)

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_single_spi_cap(spi_speed=None):
    """Direct test using ONLY Pi5Neo on SPI0 (cap) - no other code running"""
    
    # Default to standard Pi5Neo speed that works for others
    if spi_speed is None:
        spi_speed = 800
    
    print("\n" + "="*60)
    print("MINIMAL SINGLE SPI TEST - CAP ONLY")
    print("="*60)
    print("Testing ONLY SPI0 with raw Pi5Neo library")
    print(f"SPI Speed: {spi_speed} kHz")
    print("No controllers, no threads, no other SPI activity\n")
    
    # Create single Pi5Neo instance for cap
    print(f"Creating Pi5Neo for 450 LEDs on /dev/spidev0.0 at {spi_speed}kHz...")
    try:
        spi = Pi5Neo(
            spi_device="/dev/spidev0.0",
            num_leds=450,
            spi_speed_khz=spi_speed
        )
    except Exception as e:
        print(f"ERROR: Failed to initialize SPI device: {e}")
        print("Check that:")
        print("  - SPI is enabled in dietpi-config")
        print("  - /dev/spidev0.0 exists")
        return
    
    print("Testing colors that normally flicker...")
    
    # Test red (normally flickers)
    print("\n1. Testing RED (255, 0, 0) for 5 seconds...")
    for i in range(450):
        spi.set_led_color(i, 255, 0, 0)
    spi.update_strip()
    time.sleep(5)
    
    response = input("Did RED display without flickering? (y/n): ")
    red_works = response.lower() == 'y'
    
    # Test blue (normally flickers)
    print("\n2. Testing BLUE (0, 0, 255) for 5 seconds...")
    for i in range(450):
        spi.set_led_color(i, 0, 0, 255)
    spi.update_strip()
    time.sleep(5)
    
    response = input("Did BLUE display without flickering? (y/n): ")
    blue_works = response.lower() == 'y'
    
    # Test 50% gray (lots of 0 bits, should definitely flicker if timing is the issue)
    print("\n3. Testing 50% GRAY (128, 128, 128) for 5 seconds...")
    for i in range(450):
        spi.set_led_color(i, 128, 128, 128)
    spi.update_strip()
    time.sleep(5)
    
    response = input("Did GRAY display without flickering? (y/n): ")
    gray_works = response.lower() == 'y'
    
    # Test white (should work based on previous tests)
    print("\n4. Testing WHITE (255, 255, 255) for 5 seconds...")
    for i in range(450):
        spi.set_led_color(i, 255, 255, 255)
    spi.update_strip()
    time.sleep(5)
    
    response = input("Did WHITE display without flickering? (y/n): ")
    white_works = response.lower() == 'y'
    
    # Clear
    print("\nClearing LEDs...")
    spi.clear_strip()
    spi.update_strip()
    
    # Results
    print("\n" + "="*60)
    print("RESULTS:")
    print(f"  Red:   {'✓ WORKS' if red_works else '✗ FLICKERS'}")
    print(f"  Blue:  {'✓ WORKS' if blue_works else '✗ FLICKERS'}")
    print(f"  Gray:  {'✓ WORKS' if gray_works else '✗ FLICKERS'}")
    print(f"  White: {'✓ WORKS' if white_works else '✗ FLICKERS'}")
    
    if red_works and blue_works and gray_works:
        print("\n✓✓✓ SINGLE SPI WORKS PERFECTLY ✓✓✓")
        print("This CONFIRMS dual-SPI interference is the root cause!")
    elif white_works and not (red_works or blue_works or gray_works):
        print("\n✗ Single SPI still has the same flickering pattern")
        print("Dual-SPI is NOT the issue - problem exists even with one SPI")
    else:
        print("\n⚠ Mixed results - needs further investigation")
    
    print("="*60)
    
    # Cleanup
    if hasattr(spi, 'spi') and spi.spi:
        spi.spi.close()


def main():
    print("\n" + "="*60)
    print("MINIMAL SINGLE SPI ISOLATION TEST")
    print("="*60)
    print("\nThis is the simplest possible test:")
    print("- Uses Pi5Neo directly (no threading, no controllers)")  
    print("- Tests ONLY ONE SPI channel (cap/SPI0)")
    print("- If this works, dual-SPI is definitely the issue\n")
    
    # Check for speed argument
    spi_speed = None
    if len(sys.argv) > 1:
        try:
            spi_speed = int(sys.argv[1])
            print(f"Using custom SPI speed: {spi_speed} kHz")
        except ValueError:
            print(f"Invalid speed argument: {sys.argv[1]}")
            print("Usage: sudo mushroom-env/bin/python tests/test_single_spi.py [speed_khz]")
            print("Example: sudo mushroom-env/bin/python tests/test_single_spi.py 800")
            sys.exit(1)
    else:
        print("Using default SPI speed: 800 kHz")
        print("To test different speed: sudo mushroom-env/bin/python tests/test_single_spi.py 640")
    
    test_single_spi_cap(spi_speed)

if __name__ == '__main__':
    main()

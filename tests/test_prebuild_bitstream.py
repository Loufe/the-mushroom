#!/usr/bin/env python3
"""
Test pre-built bitstream to eliminate Python GIL/rebuild overhead
"""

import sys
import os
import time
import numpy as np

if os.geteuid() != 0:
    print("ERROR: Requires root for SPI")
    print("Run: sudo mushroom-env/bin/python tests/test_prebuild_bitstream.py")
    sys.exit(1)

try:
    from pi5neo import Pi5Neo
except ImportError:
    print("ERROR: pi5neo not found")
    sys.exit(1)

def test_prebuilt_buffer():
    """Send the SAME pre-built buffer repeatedly to isolate transmission issues"""
    
    spi = Pi5Neo(
        spi_device="/dev/spidev0.0",
        num_leds=50,
        spi_speed_khz=800
    )
    
    print("\n" + "="*60)
    print("TESTING PRE-BUILT BITSTREAM")
    print("="*60)
    print("This eliminates Python bitstream generation overhead")
    print("If this still flickers, it's pure SPI transmission issue\n")
    
    # Pre-build a red pattern ONCE
    print("Building bitstream buffer for RED (255,0,0)...")
    for i in range(50):
        spi.set_led_color(i, 255, 0, 0)
    
    # Force update to build the bitstream
    spi.update_strip(sleep_duration=0)
    
    # Save the pre-built bitstream
    prebuilt_buffer = spi.raw_data.copy()
    print(f"Pre-built buffer size: {len(prebuilt_buffer)} bytes")
    
    # Now send the SAME buffer repeatedly without rebuilding
    print("\nSending pre-built buffer for 5 seconds at 30 FPS (no Python overhead)...")
    start_time = time.time()
    frame_count = 0
    frame_time = 1.0 / 30  # 30 FPS
    
    while time.time() - start_time < 5.0:
        # Directly copy pre-built buffer and send
        spi.raw_data = prebuilt_buffer.copy()
        spi.send_spi_data()
        time.sleep(frame_time)
        frame_count += 1
    
    elapsed = time.time() - start_time
    print(f"Sent {frame_count} frames in {elapsed:.2f}s = {frame_count/elapsed:.1f} FPS")
    
    input("\nDoes it flicker? (Press Enter to continue)")
    
    # Test with different color
    print("\nTesting with 50% gray (128,128,128)...")
    for i in range(50):
        spi.set_led_color(i, 128, 128, 128)
    spi.update_strip(sleep_duration=0)
    prebuilt_buffer = spi.raw_data.copy()
    
    print("Sending gray for 5 seconds...")
    start_time = time.time()
    frame_count = 0
    
    while time.time() - start_time < 5.0:
        spi.raw_data = prebuilt_buffer.copy()
        spi.send_spi_data()
        time.sleep(frame_time)
        frame_count += 1
    
    print(f"Sent {frame_count} frames in 5 seconds")
    
    input("\nDoes gray flicker? (Press Enter to finish)")
    
    spi.clear_strip()
    spi.update_strip()
    
    print("\nIf pre-built buffers still flicker, it's NOT Python overhead")
    print("It's pure SPI/hardware timing issue")

if __name__ == '__main__':
    test_prebuilt_buffer()
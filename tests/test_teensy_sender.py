#!/usr/bin/env python3
"""
Test sender for Teensy OctoWS2811 - 10 LEDs x 8 outputs
Matches Nick Anderson's proven protocol: <> header + raw RGB data
"""

import serial
import time
import numpy as np

def test_teensy():
    # Config
    LEDS_PER_STRIP = 10
    NUM_STRIPS = 8
    TOTAL_LEDS = LEDS_PER_STRIP * NUM_STRIPS
    
    # Start with 115200 for stability
    try:
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
        print(f"Connected at 115200 baud")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return
    
    time.sleep(2)  # Let Teensy initialize
    
    print(f"Sending to {TOTAL_LEDS} LEDs ({LEDS_PER_STRIP} per strip x {NUM_STRIPS} strips)")
    print("Press Ctrl+C to stop\n")
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while True:
            # Just solid red for debugging - no color changes
            r, g, b = 255, 0, 0
            
            # Create frame buffer - all LEDs same color for simplicity
            frame = bytearray(b'<>')  # Header
            
            for led in range(TOTAL_LEDS):
                frame.extend([r, g, b])
            
            # Send frame
            ser.write(frame)
            
            frame_count += 1
            
            # Print FPS every second
            if frame_count % 30 == 0:
                elapsed = time.time() - start_time
                fps = frame_count / elapsed
                print(f"Frame {frame_count}: {fps:.1f} FPS - Color: RGB({r},{g},{b})")
            
            # Slower frame rate for debugging - 10 FPS
            time.sleep(1/10)
            
    except KeyboardInterrupt:
        print("\n\nStopping...")
        
        # Send black frame to clear
        frame = bytearray(b'<>')
        frame.extend([0, 0, 0] * TOTAL_LEDS)
        ser.write(frame)
        
        # Stats
        elapsed = time.time() - start_time
        print(f"\nSent {frame_count} frames in {elapsed:.1f}s")
        print(f"Average FPS: {frame_count/elapsed:.1f}")
        
    finally:
        ser.close()

if __name__ == '__main__':
    test_teensy()
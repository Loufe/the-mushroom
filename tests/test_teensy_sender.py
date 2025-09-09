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
    
    # Open serial - try 2Mbps first, fall back to 115200
    try:
        ser = serial.Serial('/dev/ttyACM0', 2000000, timeout=1)
        print(f"Connected at 2Mbps")
    except:
        try:
            ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
            print(f"Connected at 115200")
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
            # Create test pattern - cycle through colors
            color_phase = (frame_count % 300) / 100  # 0-3 range
            
            if color_phase < 1:
                # Red
                r, g, b = 255, 0, 0
            elif color_phase < 2:
                # Green  
                r, g, b = 0, 255, 0
            else:
                # Blue
                r, g, b = 0, 0, 255
            
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
            
            # Target 30 FPS for testing
            time.sleep(1/30)
            
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
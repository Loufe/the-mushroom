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
            
            # Create frame buffer - organized by strips
            frame = bytearray(b'<>')  # Header
            
            # Teensy expects all pixels of strip 0, then all pixels of strip 1, etc.
            # This matches the i * MAX_PIXELS_PER_STRIP * 3 offset in the Teensy code
            for strip in range(NUM_STRIPS):
                for pixel in range(LEDS_PER_STRIP):
                    frame.extend([r, g, b])
            
            # Debug: Print frame analysis on first send
            if frame_count == 0:
                print(f"\nFrame size: {len(frame)} bytes")
                print(f"Header: {frame[0]:02x} {frame[1]:02x} (should be 3c 3e for <>)")
                print(f"\nFirst 50 bytes: {' '.join(f'{b:02x}' for b in frame[:50])}")
                print(f"\nByte positions Teensy expects:")
                print(f"  Bytes 2-4: Strip0_Pixel0 = {frame[2]:02x} {frame[3]:02x} {frame[4]:02x}")
                print(f"  Bytes 32-34: Strip1_Pixel0 = {frame[32]:02x} {frame[33]:02x} {frame[34]:02x}")
                print(f"  Bytes 62-64: Strip2_Pixel0 = {frame[62]:02x} {frame[63]:02x} {frame[64]:02x}")
                print(f"  All should be ff 00 00 for red\n")
            
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
        
        # Send black frame to clear (organized by strips)
        frame = bytearray(b'<>')
        for strip in range(NUM_STRIPS):
            for pixel in range(LEDS_PER_STRIP):
                frame.extend([0, 0, 0])
        ser.write(frame)
        
        # Stats
        elapsed = time.time() - start_time
        print(f"\nSent {frame_count} frames in {elapsed:.1f}s")
        print(f"Average FPS: {frame_count/elapsed:.1f}")
        
    finally:
        ser.close()

if __name__ == '__main__':
    test_teensy()
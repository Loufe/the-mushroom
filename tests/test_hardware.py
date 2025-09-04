#!/usr/bin/env python3
"""
Hardware Test Script - Test LED strips with simple patterns
Run with: sudo python3 test_hardware.py
"""

from rpi_ws281x import PixelStrip, Color
import time
import argparse


def test_single_strip(gpio_pin, led_count=10):
    """Test a single LED strip"""
    print(f"\nTesting GPIO {gpio_pin} with {led_count} LEDs...")
    
    # LED strip configuration
    LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
    LED_DMA = 10          # DMA channel to use for generating signal
    LED_BRIGHTNESS = 64   # Set to 0 for darkest and 255 for brightest
    LED_INVERT = False    # True to invert the signal
    LED_CHANNEL = 0       # PWM channel
    
    try:
        # Create PixelStrip object
        strip = PixelStrip(led_count, gpio_pin, LED_FREQ_HZ, LED_DMA,
                          LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        strip.begin()
        
        print("1. Testing all RED...")
        for i in range(led_count):
            strip.setPixelColor(i, Color(255, 0, 0))
        strip.show()
        time.sleep(1)
        
        print("2. Testing all GREEN...")
        for i in range(led_count):
            strip.setPixelColor(i, Color(0, 255, 0))
        strip.show()
        time.sleep(1)
        
        print("3. Testing all BLUE...")
        for i in range(led_count):
            strip.setPixelColor(i, Color(0, 0, 255))
        strip.show()
        time.sleep(1)
        
        print("4. Testing all WHITE...")
        for i in range(led_count):
            strip.setPixelColor(i, Color(255, 255, 255))
        strip.show()
        time.sleep(1)
        
        print("5. Testing chase pattern...")
        for _ in range(3):  # Run 3 times
            for i in range(led_count):
                # Clear all
                for j in range(led_count):
                    strip.setPixelColor(j, Color(0, 0, 0))
                # Light current LED
                strip.setPixelColor(i, Color(255, 255, 0))  # Yellow
                strip.show()
                time.sleep(0.05)
        
        print("6. Testing rainbow gradient...")
        for i in range(led_count):
            # Simple rainbow calculation
            hue = int((i / led_count) * 255)
            if hue < 85:
                color = Color(255 - hue * 3, hue * 3, 0)
            elif hue < 170:
                hue -= 85
                color = Color(0, 255 - hue * 3, hue * 3)
            else:
                hue -= 170
                color = Color(hue * 3, 0, 255 - hue * 3)
            strip.setPixelColor(i, color)
        strip.show()
        time.sleep(2)
        
        # Clear at end
        print("7. Clearing...")
        for i in range(led_count):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()
        
        print(f"✓ GPIO {gpio_pin} test complete!")
        return True
        
    except Exception as e:
        print(f"✗ Error testing GPIO {gpio_pin}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Test WS2811 LED strips')
    parser.add_argument('--gpio', type=int, default=10,
                      help='GPIO pin number (default: 10)')
    parser.add_argument('--count', type=int, default=200,
                      help='Number of LEDs to test (default: 200)')
    parser.add_argument('--all', action='store_true',
                      help='Test all configured GPIO pins')
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("WS2811 LED Strip Hardware Test")
    print("=" * 50)
    print("\nIMPORTANT: This script must be run with sudo!")
    print("Make sure your level shifter is powered and connected.")
    print("")
    
    if args.all:
        # Test all configured pins
        pins = [10, 12, 18, 21]
        print(f"Testing all configured GPIO pins: {pins}")
        results = {}
        for pin in pins:
            results[pin] = test_single_strip(pin, args.count)
            time.sleep(1)  # Brief pause between tests
        
        # Summary
        print("\n" + "=" * 50)
        print("Test Summary:")
        for pin, success in results.items():
            status = "✓ PASS" if success else "✗ FAIL"
            print(f"  GPIO {pin}: {status}")
    else:
        # Test single pin
        test_single_strip(args.gpio, args.count)
    
    print("\nTest complete!")


if __name__ == '__main__':
    main()
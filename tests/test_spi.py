#!/usr/bin/env python3
"""
SPI LED Test Script for Raspberry Pi 5
Tests dual SPI channels with Pi5Neo library
Run with: sudo python3 test_spi.py
"""

from pi5neo import Pi5Neo
import time
import argparse
import sys

def test_strip(spi_device, led_count, name="Strip"):
    """Test a single LED strip on SPI"""
    print(f"\n{'='*50}")
    print(f"Testing {name}: {spi_device} with {led_count} LEDs")
    print(f"{'='*50}")
    
    try:
        # Initialize strip
        print(f"Initializing {spi_device}...")
        strip = Pi5Neo(spi_device, led_count, 800)
        
        # Test 1: All RED
        print("1. Testing RED...")
        strip.fill_strip(255, 0, 0)
        strip.update_strip()
        time.sleep(5)
        
        # Test 2: All GREEN
        print("2. Testing GREEN...")
        strip.fill_strip(0, 255, 0)
        strip.update_strip()
        time.sleep(5)
        
        # Test 3: All BLUE
        print("3. Testing BLUE...")
        strip.fill_strip(0, 0, 255)
        strip.update_strip()
        time.sleep(5)
        
        # Test 4: WHITE with 5 brightness levels
        print("4. Testing WHITE (5 brightness levels)...")
        brightness_levels = [
            (25, "10%"),
            (64, "25%"),
            (128, "50%"),
            (192, "75%"),
            (255, "100%")
        ]
        for brightness, percent in brightness_levels:
            print(f"   - Brightness {percent}")
            strip.fill_strip(brightness, brightness, brightness)
            strip.update_strip()
            time.sleep(1)
        
        # Clear at end
        print("5. Clearing...")
        strip.fill_strip(0, 0, 0)
        strip.update_strip()
        
        print(f"✓ {name} test complete!")
        return True
        
    except Exception as e:
        print(f"✗ Error testing {name}: {e}")
        return False


def test_dual_strips():
    """Test both SPI channels simultaneously"""
    print("\n" + "="*50)
    print("Testing Dual SPI Strips")
    print("="*50)
    
    try:
        # Initialize both strips
        print("Initializing both SPI channels...")
        stem = Pi5Neo('/dev/spidev1.0', 250, 800)  # Stem interior
        cap = Pi5Neo('/dev/spidev0.0', 450, 800)   # Cap exterior
        
        print("\n1. Stem RED, Cap BLUE...")
        stem.fill_strip(255, 0, 0)
        stem.update_strip()
        cap.fill_strip(0, 0, 255)
        cap.update_strip()
        time.sleep(1)
        
        print("2. Stem GREEN, Cap YELLOW...")
        stem.fill_strip(0, 255, 0)
        stem.update_strip()
        cap.fill_strip(255, 255, 0)
        cap.update_strip()
        time.sleep(1)
        
        print("3. Both WHITE (dim)...")
        stem.fill_strip(64, 64, 64)
        stem.update_strip()
        cap.fill_strip(64, 64, 64)
        cap.update_strip()
        time.sleep(1)
        
        print("4. Alternating pattern...")
        for _ in range(3):
            stem.fill_strip(255, 0, 128)
            stem.update_strip()
            cap.fill_strip(0, 128, 255)
            cap.update_strip()
            time.sleep(0.5)
            
            stem.fill_strip(0, 128, 255)
            stem.update_strip()
            cap.fill_strip(255, 0, 128)
            cap.update_strip()
            time.sleep(0.5)
        
        # Clear both
        print("5. Clearing both...")
        stem.fill_strip(0, 0, 0)
        stem.update_strip()
        cap.fill_strip(0, 0, 0)
        cap.update_strip()
        
        print("✓ Dual strip test complete!")
        return True
        
    except Exception as e:
        print(f"✗ Error in dual strip test: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Test Pi5Neo LED strips on Raspberry Pi 5')
    parser.add_argument('--mode', choices=['stem', 'cap', 'both', 'dual'], 
                       default='both',
                       help='Test mode: stem only, cap only, both sequential, or dual simultaneous')
    parser.add_argument('--count', type=int, default=10,
                       help='Number of LEDs to test (for single strip tests)')
    
    args = parser.parse_args()
    
    print("\n" + "="*50)
    print("Raspberry Pi 5 SPI LED Test")
    print("Using Pi5Neo Library")
    print("="*50)
    print("\nIMPORTANT: Run with sudo!")
    print("Make sure SPI is enabled in dietpi-config")
    print("Check that /dev/spidev0.0 and /dev/spidev1.0 exist\n")
    
    results = {}
    
    if args.mode == 'stem':
        results['stem'] = test_strip('/dev/spidev1.0', args.count, "Stem Interior")
    elif args.mode == 'cap':
        results['cap'] = test_strip('/dev/spidev0.0', args.count, "Cap Exterior")
    elif args.mode == 'both':
        # Test full configured counts
        results['stem'] = test_strip('/dev/spidev1.0', 250, "Stem Interior")
        time.sleep(1)
        results['cap'] = test_strip('/dev/spidev0.0', 450, "Cap Exterior")
    elif args.mode == 'dual':
        results['dual'] = test_dual_strips()
    
    # Summary
    print("\n" + "="*50)
    print("Test Summary:")
    print("="*50)
    for name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {name}: {status}")
    
    print("\nTest complete!")
    
    # Exit with error if any test failed
    if not all(results.values()):
        sys.exit(1)


if __name__ == '__main__':
    main()
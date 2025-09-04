#!/usr/bin/env python3
"""
GPIO Verification Test
Blue-purple wave on GPIO 10 (SPI0)
Yellow-green wave on GPIO 20 (SPI1)
"""

from pi5neo import Pi5Neo
import time
import math

def run_test():
    print("="*60)
    print("GPIO PIN VERIFICATION TEST")
    print("="*60)
    print("\nThis test will output:")
    print("- BLUE-PURPLE wave on GPIO 10 (Pin 19) via /dev/spidev0.0")
    print("- YELLOW-GREEN wave on GPIO 20 (Pin 38) via /dev/spidev1.0")
    print("\nConnect LEDs to verify correct pins!")
    print("-"*60)
    
    # Number of test LEDs (adjust based on what you have connected)
    TEST_LEDS = 50
    
    try:
        # Initialize both strips
        print("\nInitializing SPI devices...")
        gpio10_strip = Pi5Neo('/dev/spidev0.0', TEST_LEDS, 800)  # GPIO 10
        gpio20_strip = Pi5Neo('/dev/spidev1.0', TEST_LEDS, 800)  # GPIO 20
        
        print("Starting color wave test (press Ctrl+C to stop)...\n")
        
        frame = 0
        while True:
            # Calculate wave position
            wave_pos = (frame % 100) / 100.0
            
            # GPIO 10: Blue-Purple wave
            for i in range(TEST_LEDS):
                # Create wave effect
                led_pos = i / TEST_LEDS
                intensity = (math.sin((led_pos + wave_pos) * 2 * math.pi) + 1) / 2
                
                # Blue to purple gradient
                r = int(100 * intensity)  # Red component for purple
                g = 0
                b = int(150 + 105 * intensity)  # Blue always present
                
                gpio10_strip.set_led_color(i, r, g, b)
            
            # GPIO 20: Yellow-Green wave
            for i in range(TEST_LEDS):
                # Create wave effect
                led_pos = i / TEST_LEDS
                intensity = (math.sin((led_pos - wave_pos) * 2 * math.pi) + 1) / 2
                
                # Yellow to green gradient
                r = int(150 * intensity)  # Red for yellow
                g = int(100 + 155 * intensity)  # Green always strong
                b = 0
                
                gpio20_strip.set_led_color(i, r, g, b)
            
            # Update both strips
            gpio10_strip.update_strip()
            gpio20_strip.update_strip()
            
            # Status update every second
            if frame % 30 == 0:
                print(f"Frame {frame}: GPIO 10 (blue-purple) | GPIO 20 (yellow-green)", end='\r')
            
            frame += 1
            time.sleep(0.033)  # ~30 FPS
            
    except KeyboardInterrupt:
        print("\n\nStopping test...")
        
    except Exception as e:
        print(f"\nError: {e}")
        
    finally:
        # Clear both strips
        print("Clearing LEDs...")
        try:
            gpio10_strip.fill_strip(0, 0, 0)
            gpio10_strip.update_strip()
        except:
            pass
        
        try:
            gpio20_strip.fill_strip(0, 0, 0)
            gpio20_strip.update_strip()
        except:
            pass
        
        print("Test complete!")

if __name__ == '__main__':
    print("\nUSAGE: sudo python3 test_gpio_verify.py")
    print("\nWIRING:")
    print("- Connect first LED strip data to Pin 19 (GPIO 10)")
    print("- Connect second LED strip data to Pin 38 (GPIO 20)")
    print("- Ensure common ground between Pi and LED power supply")
    print()
    
    run_test()
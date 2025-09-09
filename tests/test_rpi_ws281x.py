#!/usr/bin/env python3
import time
from rpi_ws281x import PixelStrip, Color, ws

LED_COUNT = 50
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 128
LED_INVERT = False
LED_CHANNEL = 0
LED_STRIP = ws.WS2811_STRIP_GRB

def main():
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
    strip.begin()
    
    print(f"Testing {LED_COUNT} WS2811 LEDs on GPIO {LED_PIN}")
    print("Blue -> Purple -> Red (1 second each)")
    print("Press Ctrl-C to stop")
    
    try:
        while True:
            for i in range(LED_COUNT):
                strip.setPixelColor(i, Color(0, 0, 255))
            strip.show()
            time.sleep(1)
            
            for i in range(LED_COUNT):
                strip.setPixelColor(i, Color(128, 0, 128))
            strip.show()
            time.sleep(1)
            
            for i in range(LED_COUNT):
                strip.setPixelColor(i, Color(255, 0, 0))
            strip.show()
            time.sleep(1)
            
    except KeyboardInterrupt:
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()
        print("\nLEDs cleared")

if __name__ == '__main__':
    main()
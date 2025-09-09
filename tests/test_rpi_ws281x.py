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

def wheel(pos):
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

def main():
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
    strip.begin()
    
    print(f"Testing {LED_COUNT} WS2811 LEDs on GPIO {LED_PIN}")
    print("Fast rainbow gradient - all LEDs same color")
    print("Press Ctrl-C to stop")
    
    try:
        j = 0
        while True:
            color = wheel(j & 255)
            for i in range(LED_COUNT):
                strip.setPixelColor(i, color)
            strip.show()
            time.sleep(0.01)
            j += 2
            
    except KeyboardInterrupt:
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()
        print("\nLEDs cleared")

if __name__ == '__main__':
    main()
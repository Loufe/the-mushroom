// Simplified from Nick Anderson's battle-tested OctoWS2811 code
// For initial test: 10 LEDs x 8 outputs = 80 LEDs total

#include <OctoWS2811.h>

#define MAX_PIXELS_PER_STRIP 10  // Start small for testing

DMAMEM int displayMemory[MAX_PIXELS_PER_STRIP * 6];
DMAMEM byte drawingMemory[MAX_PIXELS_PER_STRIP * 8 * 3];

// Can adjust color order here - using RGB for now
OctoWS2811 leds(MAX_PIXELS_PER_STRIP, displayMemory, drawingMemory, WS2811_RGB | WS2811_800kHz);

char megaBuffer[MAX_PIXELS_PER_STRIP * 8 * 3];  // 10 * 8 * 3 = 240 bytes

void setup() {
  Serial.begin(115200);  // Match Python sender at 115200
  
  leds.begin();
  leds.show();
  
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);  // LED on = running
}

void loop() {
  // Wait for header
  if (Serial.read() == '<' && Serial.read() == '>') {
    // Read all pixel data at once
    Serial.readBytes(megaBuffer, MAX_PIXELS_PER_STRIP * 8 * 3);
    
    // Simple method - we'll optimize later if this works
    int curItem = 0;
    while (curItem < (MAX_PIXELS_PER_STRIP * 8)) {
      leds.setPixel(curItem, 
                    megaBuffer[curItem * 3], 
                    megaBuffer[curItem * 3 + 1], 
                    megaBuffer[curItem * 3 + 2]);
      curItem++;
    }
    
    leds.show();
    
    // Quick blink to show frame received
    digitalWrite(LED_BUILTIN, LOW);
    delayMicroseconds(100);
    digitalWrite(LED_BUILTIN, HIGH);
  }
}
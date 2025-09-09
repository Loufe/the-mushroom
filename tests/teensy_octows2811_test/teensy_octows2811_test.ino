// Simplified from Nick Anderson's battle-tested OctoWS2811 code
// For initial test: 10 LEDs x 8 outputs = 80 LEDs total

#include <OctoWS2811.h>

#define MAX_PIXELS_PER_STRIP 10  // Start small for testing
#define qBlink() (digitalWriteFast(LED_BUILTIN, !digitalReadFast(LED_BUILTIN)))

DMAMEM int displayMemory[MAX_PIXELS_PER_STRIP * 6];
DMAMEM byte drawingMemory[MAX_PIXELS_PER_STRIP * 8 * 3] __attribute__((aligned(32)));

char megaBuffer[MAX_PIXELS_PER_STRIP * 8 * 3] __attribute__((aligned(2048)));  // 10 * 8 * 3 = 240 bytes

// we use RGB, confirmed.
OctoWS2811 leds(MAX_PIXELS_PER_STRIP, displayMemory, drawingMemory, WS2811_RGB | WS2813_800kHz);


void setup() {
  Serial.begin(115200);  // Match Python sender at 115200
  
  leds.begin();
  leds.show();
  
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);  // LED on = running
}

int offset, curItem, i, mask;
int pixel[8];
byte b;
unsigned long millisSinceBlink = 0;

void loop() {
  // Quickly check if next bytes are the header
  if (Serial.read() == '<' && Serial.read() == '>') {
    Serial.readBytes(megaBuffer, MAX_PIXELS_PER_STRIP * 8 * 3);

    // Original, but slower, method for populating drawingMemory
    // curItem = 0;
    // while (curItem < (MAX_PIXELS_PER_STRIP * 8)) {
    //   leds.setPixel(curItem, megaBuffer[curItem * 3], megaBuffer[curItem * 3 + 1], megaBuffer[curItem * 3 + 2]);
    //   curItem++;
    // }

    // Code is based on movie2serial.pde
    // While loop runs through one strip worth - Number of pixels * 3 channels R,G,B
    // First For loop gets each strip's nth (i) pixel's color data as an int
    // Second For loop set which bit from each pixel we process
    //  Inner For loop gets that bit from each pixel and accumulates them into a byte (b)
    offset = 0;
    curItem = 0;
    while (curItem < MAX_PIXELS_PER_STRIP * 3) {

      for (i = 0; i < 8; i++) {
        // Color order should be managed by the Sequencer (like Vixen/xLights) configuration
        pixel[i] = (megaBuffer[curItem + i * MAX_PIXELS_PER_STRIP * 3] << 16) | (megaBuffer[curItem + 1 + i * MAX_PIXELS_PER_STRIP * 3] << 8) | megaBuffer[curItem + 2 + i * MAX_PIXELS_PER_STRIP * 3];
      }

      for (mask = 0x800000; mask != 0; mask >>= 1) {
        b = 0;
        for (i = 0; i < 8; i++) {
          if ((pixel[i] & mask) != 0) b |= (1 << i);
        }
        // Load data directly into OctoWS2811's drawingMemory
        drawingMemory[offset++] = b;
      }

      curItem += 3;
    }

    leds.show();
  } else {
    // Is there USB Serial data that isn't a header? If so, flash LED every 750ms
    // Flashing can indicate the following:
    //    Serial header of <> is missing (Lights most likely aren't working) - Check FPP settings that the header is set
    //    Serial header of <> isn't where it is expected (Lights might be working) - Verify MAX_PIXELS_PER_STRIP * 8 * 3 matches the number of channels
    //    Serial data not being processed fast enough - Sequence refresh rate should be slowed down until flashing stops (Tested with MAX_PIXELS_PER_STRIP = 517 with 17ms sequence timing)
    if (Serial.peek() != -1 && Serial.peek() != '<' && millis() - millisSinceBlink > 750) {
      qBlink();
      millisSinceBlink = millis();
    } else if (millis() - millisSinceBlink > 3000) // Turn LED back on in case it was left off, but no more data has come in
      digitalWriteFast(LED_BUILTIN, 1);
  }
}
/**
 * Debug test to understand bit/byte interpretation
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <string.h>

#include "pico/stdlib.h"
#include "hardware/pio.h"
#include "hardware/clocks.h"
#include "ws2812.pio.h"

#define IS_RGBW false
#define NUM_PIXELS 5  // Just test first 5
#define PIN_NUM 10

PIO pio;
int sm;
volatile int running = 1;

static inline void put_pixel(uint32_t pixel_rgb) {
    pio_sm_put_blocking(pio, sm, pixel_rgb << 8u);
}

void signal_handler(int sig) {
    running = 0;
}

int main(int argc, const char **argv) {
    uint offset;
    uint gpio = PIN_NUM;
    
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    
    // Initialize PIO
    pio = pio_open(0);
    if (!pio) {
        printf("Failed to open PIO device\n");
        return 1;
    }
    
    sm = pio_claim_unused_sm(pio, true);
    offset = pio_add_program(pio, &ws2812_program);
    
    ws2812_program_init(pio, sm, offset, gpio, 800000, IS_RGBW);
    pio_sm_clear_fifos(pio, sm);
    
    printf("Debug test - sending specific patterns\n");
    printf("Press ENTER after observing each test\n\n");
    
    // Test 1: Send all zeros
    printf("Test 1: Sending all zeros (should be all off)\n");
    for (int i = 0; i < NUM_PIXELS; i++) {
        put_pixel(0);
    }
    getchar();
    
    // Test 2: Send single byte patterns
    printf("Test 2: Sending 0xFF0000 to all pixels (RGB order = RED)\n");
    for (int i = 0; i < NUM_PIXELS; i++) {
        put_pixel(0xFF0000);
    }
    getchar();
    
    printf("Test 3: Sending 0x00FF00 to all pixels (RGB order = GREEN)\n");
    for (int i = 0; i < NUM_PIXELS; i++) {
        put_pixel(0x00FF00);
    }
    getchar();
    
    printf("Test 4: Sending 0x0000FF to all pixels (RGB order = BLUE)\n");
    for (int i = 0; i < NUM_PIXELS; i++) {
        put_pixel(0x0000FF);
    }
    getchar();
    
    // Test 5: Send decreasing values to see pattern
    printf("Test 5: Sending different values to each pixel:\n");
    printf("  Pixel 1: 0xFF0000 (RED)\n");
    printf("  Pixel 2: 0x00FF00 (GREEN)\n");
    printf("  Pixel 3: 0x0000FF (BLUE)\n");
    printf("  Pixel 4: 0xFFFF00 (YELLOW)\n");
    printf("  Pixel 5: 0xFF00FF (MAGENTA)\n");
    put_pixel(0xFF0000);  // Red
    put_pixel(0x00FF00);  // Green
    put_pixel(0x0000FF);  // Blue
    put_pixel(0xFFFF00);  // Yellow
    put_pixel(0xFF00FF);  // Magenta
    getchar();
    
    // Clear
    printf("Clearing...\n");
    for (int i = 0; i < NUM_PIXELS; i++) {
        put_pixel(0);
    }
    
    pio_close(pio);
    return 0;
}
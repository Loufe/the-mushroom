/**
 * Diagnostic test for WS2812/WS2811 color issues
 * Tests different color orders and pixel configurations
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <signal.h>

#include "pico/stdlib.h"
#include "hardware/pio.h"
#include "hardware/clocks.h"
#include "ws2812.pio.h"

#define NUM_PIXELS 25
#define PIN_NUM 10

PIO pio;
int sm;
volatile int running = 1;

static inline void put_pixel(uint32_t pixel_grb) {
    pio_sm_put_blocking(pio, sm, pixel_grb << 8u);
}

// Different color order functions
static inline uint32_t rgb_order(uint8_t r, uint8_t g, uint8_t b) {
    return ((uint32_t)(r) << 16) | ((uint32_t)(g) << 8) | (uint32_t)(b);
}

static inline uint32_t grb_order(uint8_t r, uint8_t g, uint8_t b) {
    return ((uint32_t)(g) << 16) | ((uint32_t)(r) << 8) | (uint32_t)(b);
}

static inline uint32_t brg_order(uint8_t r, uint8_t g, uint8_t b) {
    return ((uint32_t)(b) << 16) | ((uint32_t)(r) << 8) | (uint32_t)(g);
}

void signal_handler(int sig) {
    running = 0;
}

void test_single_pixel(int pixel_num, uint8_t r, uint8_t g, uint8_t b, 
                       uint32_t (*color_func)(uint8_t, uint8_t, uint8_t)) {
    // Clear all pixels first
    for (int i = 0; i < NUM_PIXELS; i++) {
        put_pixel(0);
    }
    usleep(10000); // 10ms delay
    
    // Light only the specified pixel
    for (int i = 0; i < NUM_PIXELS; i++) {
        if (i == pixel_num) {
            put_pixel(color_func(r, g, b));
        } else {
            put_pixel(0);
        }
    }
}

void test_gradient() {
    printf("\nGradient test - each pixel slightly different\n");
    for (int i = 0; i < NUM_PIXELS; i++) {
        uint8_t val = (255 * i) / NUM_PIXELS;
        put_pixel(grb_order(val, 0, 255-val));  // Red to Blue gradient
    }
}

int main(int argc, const char **argv) {
    uint offset;
    uint gpio = PIN_NUM;
    int test_mode = 0;
    
    if (argc >= 2) {
        test_mode = atoi(argv[1]);
    }
    if (argc >= 3) {
        gpio = (uint)strtoul(argv[2], NULL, 0);
    }
    
    printf("WS2812 Diagnostic Test on GPIO %d\n", gpio);
    printf("Testing %d pixels\n\n", NUM_PIXELS);
    
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
    
    // Test both RGB and RGBW modes
    int is_rgbw = (test_mode == 1) ? 1 : 0;
    
    printf("Testing in %s mode\n", is_rgbw ? "RGBW" : "RGB");
    ws2812_program_init(pio, sm, offset, gpio, 800000, is_rgbw);
    
    if (test_mode == 0) {
        printf("\n=== COLOR ORDER TEST ===\n");
        printf("Setting all pixels to pure RED (255,0,0)\n");
        printf("Press Enter to test each color order...\n\n");
        
        // Test RGB order
        printf("Testing RGB order - should be RED if RGB strips: ");
        getchar();
        for (int i = 0; i < NUM_PIXELS; i++) {
            put_pixel(rgb_order(255, 0, 0));
        }
        
        printf("Testing GRB order - should be RED if GRB strips: ");
        getchar();
        for (int i = 0; i < NUM_PIXELS; i++) {
            put_pixel(grb_order(255, 0, 0));
        }
        
        printf("Testing BRG order - should be RED if BRG strips: ");
        getchar();
        for (int i = 0; i < NUM_PIXELS; i++) {
            put_pixel(brg_order(255, 0, 0));
        }
        
    } else if (test_mode == 2) {
        printf("\n=== PIXEL POSITION TEST ===\n");
        printf("Lighting one pixel at a time with pure red\n");
        
        for (int i = 0; i < NUM_PIXELS && running; i++) {
            printf("Pixel %d of %d\n", i+1, NUM_PIXELS);
            test_single_pixel(i, 255, 0, 0, grb_order);
            sleep(1);
        }
        
    } else if (test_mode == 3) {
        printf("\n=== GRADIENT TEST ===\n");
        test_gradient();
        printf("Should see smooth color transition\n");
        while(running) {
            sleep(1);
        }
        
    } else {
        printf("\nUsage: %s [mode] [gpio]\n", argv[0]);
        printf("Modes:\n");
        printf("  0 - Color order test (default)\n");
        printf("  1 - RGBW mode test\n");
        printf("  2 - Individual pixel test\n");
        printf("  3 - Gradient test\n");
    }
    
    // Clear on exit
    printf("\nClearing pixels...\n");
    for (int i = 0; i < NUM_PIXELS; i++) {
        put_pixel(0);
    }
    
    pio_close(pio);
    return 0;
}
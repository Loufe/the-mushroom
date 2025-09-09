/**
 * Simple WS2812 test using PIOlib on Raspberry Pi 5
 * Cycles through primary colors - all pixels same color
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

#define IS_RGBW false  // WS2811 is RGB (24-bit)
#define NUM_PIXELS 25  // Match your config
#define PIN_NUM 10     // GPIO 10

PIO pio;
int sm;
volatile int running = 1;

static inline void put_pixel(uint32_t pixel_rgb) {
    // For RGB mode with pull_threshold=24, PIO uses bits 31-8 of the 32-bit word
    // Must shift our 24-bit RGB data up by 8 bits
    pio_sm_put_blocking(pio, sm, pixel_rgb << 8u);
}

static inline uint32_t urgb_u32(uint8_t r, uint8_t g, uint8_t b) {
    return ((uint32_t)(r) << 16) |  // RGB order for WS2811 (R first)
           ((uint32_t)(g) << 8) |    // G second
           (uint32_t)(b);             // B third
}

void signal_handler(int sig) {
    running = 0;
}

void set_all_pixels(uint8_t r, uint8_t g, uint8_t b) {
    for (int i = 0; i < NUM_PIXELS; i++) {
        put_pixel(urgb_u32(r, g, b));
    }
}

int main(int argc, const char **argv) {
    uint offset;
    uint gpio = PIN_NUM;
    int mode = 0;
    
    // Parse command line arguments
    if (argc >= 2) {
        mode = atoi(argv[1]);
    }
    if (argc >= 3) {
        gpio = (uint)strtoul(argv[2], NULL, 0);
    }
    
    printf("PIO Test on GPIO %d - Mode %d\n", gpio, mode);
    
    // Set up signal handler
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
    
    printf("PIO initialized: program at %d, sm %d\n", offset, sm);
    
    // Debug: Check actual clock speed
    uint32_t sys_clk = clock_get_hz(clk_sys);
    printf("System clock: %u Hz\n", sys_clk);
    
    // Use 400kHz for mode 2, 800kHz otherwise
    uint freq = (mode == 2) ? 400000 : 800000;
    printf("Using %dkHz timing\n", freq/1000);
    
    // Calculate what divider will be used
    int cycles_per_bit = 10; // T1+T2+T3 from ws2812.pio
    float expected_div = (float)sys_clk / (freq * cycles_per_bit);
    printf("Expected clock divider: %.2f\n\n", expected_div);
    
    ws2812_program_init(pio, sm, offset, gpio, freq, IS_RGBW);
    
    // Clear FIFOs before starting (ws2812_program_init already enables the SM)
    pio_sm_clear_fifos(pio, sm);
    
    if (mode == 0) {
        // Mode 0: Basic color cycling
        printf("Mode 0: Color cycling - all pixels same color\n\n");
        while (running) {
        // Red
        printf("RED\n");
        set_all_pixels(255, 0, 0);
        sleep(2);
        if (!running) break;
        
        // Green
        printf("GREEN\n");
        set_all_pixels(0, 255, 0);
        sleep(2);
        if (!running) break;
        
        // Blue
        printf("BLUE\n");
        set_all_pixels(0, 0, 255);
        sleep(2);
        if (!running) break;
        
        // White
        printf("WHITE\n");
        set_all_pixels(255, 255, 255);
        sleep(2);
        if (!running) break;
        
            // Off
            printf("OFF\n");
            set_all_pixels(0, 0, 0);
            sleep(1);
        }
        
    } else if (mode == 1) {
        // Mode 1: Individual pixel test - manual stepping
        printf("Mode 1: Individual pixel test - MANUAL STEPPING\n");
        printf("Sending pure RED (255,0,0) to one pixel at a time\n");
        printf("Press ENTER to advance to next pixel, 'q' to quit\n\n");
        
        for (int i = 0; i < NUM_PIXELS && running; i++) {
            // Show exactly what we're sending
            uint32_t pixel_data = urgb_u32(255, 0, 0);
            uint32_t shifted_data = pixel_data << 8;
            
            printf("\nPixel %d/%d:\n", i+1, NUM_PIXELS);
            printf("  RGB values: R=255, G=0, B=0\n");
            printf("  Raw data: 0x%06X (bits: ", pixel_data);
            for (int bit = 23; bit >= 0; bit--) {
                printf("%d", (pixel_data >> bit) & 1);
                if (bit % 8 == 0 && bit > 0) printf(" ");
            }
            printf(")\n");
            printf("  After << 8: 0x%08X\n", shifted_data);
            printf("  Sending this to pixel %d, zeros to all others\n", i+1);
            
            // Clear all pixels first
            for (int j = 0; j < NUM_PIXELS; j++) {
                put_pixel(0);
            }
            usleep(10000); // 10ms for reset
            
            // Light only pixel i with pure red
            for (int j = 0; j < NUM_PIXELS; j++) {
                if (j == i) {
                    put_pixel(pixel_data);
                } else {
                    put_pixel(0);
                }
            }
            
            // Wait for user input
            printf("What color do you see? ");
            fflush(stdout);
            char input[100];
            if (fgets(input, sizeof(input), stdin) == NULL) {
                break;
            }
            if (input[0] == 'q' || input[0] == 'Q') {
                running = 0;
                break;
            }
        }
        printf("\nTest complete\n");
        
    } else if (mode == 2) {
        // Mode 2: Same as mode 0 but with 400kHz timing
        printf("Mode 2: Testing with 400kHz timing for WS2811\n\n");
        while (running) {
            printf("RED\n");
            set_all_pixels(255, 0, 0);
            sleep(2);
            if (!running) break;
            
            printf("GREEN\n");
            set_all_pixels(0, 255, 0);
            sleep(2);
            if (!running) break;
            
            printf("BLUE\n");
            set_all_pixels(0, 0, 255);
            sleep(2);
            if (!running) break;
            
            printf("WHITE\n");
            set_all_pixels(255, 255, 255);
            sleep(2);
        }
        
    } else if (mode == 3) {
        // Mode 3: Pattern test - each pixel different to stress-test signal
        printf("Mode 3: Pattern test - each pixel different color\n\n");
        
        while (running) {
            printf("Rainbow gradient\n");
            for (int i = 0; i < NUM_PIXELS; i++) {
                uint8_t hue = (255 * i) / NUM_PIXELS;
                uint8_t r = (hue < 85) ? (255 - hue * 3) : (hue < 170) ? 0 : ((hue - 170) * 3);
                uint8_t g = (hue < 85) ? (hue * 3) : (hue < 170) ? (255 - (hue - 85) * 3) : 0;
                uint8_t b = (hue < 85) ? 0 : (hue < 170) ? ((hue - 85) * 3) : (255 - (hue - 170) * 3);
                put_pixel(urgb_u32(r, g, b));
            }
            sleep(5);
        }
        
    } else if (mode == 4) {
        // Mode 4: Test what happens with different bit positions
        printf("Mode 4: Testing bit positions and accumulation\n");
        printf("Watch what happens with different shift amounts\n\n");
        
        while (running) {
            // Test RGB order (should show RED for WS2811)
            printf("RGB order - should be RED\n");
            for (int i = 0; i < NUM_PIXELS; i++) {
                uint32_t rgb = ((uint32_t)(255) << 16) | ((uint32_t)(0) << 8) | (0);
                put_pixel(rgb);
            }
            sleep(3);
            if (!running) break;
            
            // Test GRB order (will show GREEN if WS2812)
            printf("GRB order - will be GREEN if chip expects GRB\n");
            for (int i = 0; i < NUM_PIXELS; i++) {
                uint32_t grb = ((uint32_t)(0) << 16) | ((uint32_t)(255) << 8) | (0);
                put_pixel(grb);
            }
            sleep(3);
            if (!running) break;
            
            // Test pure white
            printf("WHITE test\n");
            for (int i = 0; i < NUM_PIXELS; i++) {
                uint32_t white = ((uint32_t)(255) << 16) | ((uint32_t)(255) << 8) | (255);
                put_pixel(white);
            }
            sleep(3);
        }
        
    } else {
        printf("Usage: %s [mode] [gpio]\n", argv[0]);
        printf("Modes:\n");
        printf("  0 - Basic color cycling (default)\n");
        printf("  1 - Individual pixel test\n");
        printf("  2 - 400kHz timing test\n");
        printf("  3 - Rainbow gradient pattern\n");
        printf("  4 - Color order test\n");
    }
    
    // Clear LEDs on exit
    printf("\nClearing LEDs...\n");
    set_all_pixels(0, 0, 0);
    
    pio_close(pio);
    printf("Done\n");
    return 0;
}
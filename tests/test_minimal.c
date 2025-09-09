// test_minimal.c - Exact copy of piotest.c pattern for debugging
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "piolib.h"
#include "ws2812.pio.h"

int main(int argc, const char **argv) {
    PIO pio;
    int sm;
    uint offset;
    const uint pixels = 25;
    uint8_t databuf[pixels * 4];  // 4 bytes per pixel like piotest
    uint gpio = 10;
    
    if (argc == 2)
        gpio = (uint)strtoul(argv[1], NULL, 0);
    
    // EXACTLY like piotest.c
    pio = pio0;  // Use pio0 macro
    sm = pio_claim_unused_sm(pio, true);
    pio_sm_config_xfer(pio, sm, PIO_DIR_TO_SM, 256, 1);
    
    offset = pio_add_program(pio, &ws2812_program);
    printf("Loaded program at %d, using sm %d, gpio %d\n", offset, sm, gpio);
    
    pio_sm_clear_fifos(pio, sm);
    pio_sm_set_clkdiv(pio, sm, 1.0);
    ws2812_program_init(pio, sm, offset, gpio, 800000.0, false);
    
    printf("Sending RED to all %d pixels\n", pixels);
    
    // Set all pixels to red using piotest format
    for (int i = 0; i < pixels; i++) {
        databuf[4*i + 0] = 0;     // Padding
        databuf[4*i + 1] = 0;     // Green  
        databuf[4*i + 2] = 255;   // Red
        databuf[4*i + 3] = 0;     // Blue
    }
    
    // Send using xfer_data like piotest
    pio_sm_xfer_data(pio, sm, PIO_DIR_TO_SM, sizeof(databuf), databuf);
    sleep_ms(10);
    
    printf("Waiting 5 seconds...\n");
    sleep(5);
    
    printf("Sending GREEN to all pixels\n");
    // Now try green
    for (int i = 0; i < pixels; i++) {
        databuf[4*i + 0] = 0;     // Padding
        databuf[4*i + 1] = 255;   // Green  
        databuf[4*i + 2] = 0;     // Red
        databuf[4*i + 3] = 0;     // Blue
    }
    
    pio_sm_xfer_data(pio, sm, PIO_DIR_TO_SM, sizeof(databuf), databuf);
    sleep_ms(10);
    
    sleep(5);
    
    printf("Clearing LEDs\n");
    // Clear all
    for (int i = 0; i < pixels; i++) {
        databuf[4*i + 0] = 0;
        databuf[4*i + 1] = 0;
        databuf[4*i + 2] = 0;
        databuf[4*i + 3] = 0;
    }
    
    pio_sm_xfer_data(pio, sm, PIO_DIR_TO_SM, sizeof(databuf), databuf);
    sleep_ms(10);
    
    printf("Done\n");
    return 0;
}
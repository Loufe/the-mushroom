# PIO Approach for WS2811 LED Control on Raspberry Pi 5

## Overview

This document details the approach for controlling WS2811 LEDs using the Programmable I/O (PIO) subsystem on Raspberry Pi 5's RP1 chip via the piolib library.

## Background: Why PIO Instead of SPI

### SPI Approach Failed
- **Issue**: Flickering for all colors except pure white (0xFF,0xFF,0xFF)
- **Root Cause**: The 0xC0 bitstream encoding for "0" bits violates WS2811 timing specifications by ~62ns
- **Platform Specific**: Pi 5's RP1 I/O controller cannot maintain timing during rapid SPI updates
- **Evidence**: Single static frames work perfectly, but rapid updates fail consistently

### PIO Advantages
1. **Hardware-level timing control**: PIO state machines run cycle-accurate at configurable frequencies
2. **Independent of CPU**: Runs on RP1 chip, unaffected by Linux scheduler or Python GIL
3. **DMA-driven**: Automatic data transfer without CPU intervention
4. **Precise waveform generation**: Direct control over HIGH/LOW signal durations

## WS2811 Protocol Specifications

### Official Specifications
Based on the WS2811 datasheet and verified sources:

**Data Format (24-bit RGB)**:
```
R7 R6 R5 R4 R3 R2 R1 R0 | G7 G6 G5 G4 G3 G2 G1 G0 | B7 B6 B5 B4 B3 B2 B1 B0
```
- 24 bits per pixel (8 bits each for Red, Green, Blue)
- Data sent MSB first
- RGB color order (not GRB like WS2812)

**Timing Requirements (800kHz mode)**:
- **'0' bit**: T0H = 250ns ± 150ns HIGH, T0L = 1000ns ± 150ns LOW
- **'1' bit**: T1H = 600ns ± 150ns HIGH, T1L = 650ns ± 150ns LOW
- **Reset**: >50µs LOW signal to latch data

**Timing Requirements (400kHz mode)**:
- **'0' bit**: T0H = 500ns ± 150ns HIGH, T0L = 2000ns ± 150ns LOW
- **'1' bit**: T1H = 1200ns ± 150ns HIGH, T1L = 1300ns ± 150ns LOW
- **Reset**: >50µs LOW signal to latch data

### Key Differences: WS2811 vs WS2812
| Aspect | WS2811 | WS2812 |
|--------|--------|--------|
| Color Order | RGB | GRB |
| Speed Options | 400kHz or 800kHz | 800kHz only |
| '0' bit timing | 250ns/1000ns | 400ns/850ns |
| '1' bit timing | 600ns/650ns | 800ns/450ns |
| Data bits | 24 (RGB) | 24 (RGB) or 32 (RGBW) |

## PIOlib Implementation on Raspberry Pi 5

### Installation and Setup

**Prerequisites**:
```bash
sudo apt install build-essential cmake
```

**Build piolib**:
```bash
cd /tmp
git clone https://github.com/raspberrypi/utils.git raspberrypi-utils
cd raspberrypi-utils/piolib
cmake .
make
```

**Device Permissions**:
The `/dev/pio0` device requires proper permissions. Add to `/etc/udev/rules.d/99-com.rules`:
```
SUBSYSTEM=="*-pio", GROUP="gpio", MODE="0660"
```

Then apply:
```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
sudo usermod -a -G gpio $USER
# Log out and back in for group membership to take effect
```

### PIO Architecture on RP1

The RP1 chip on Raspberry Pi 5 includes PIO hardware similar to the RP2040 (Pico):
- 4 state machines per PIO instance
- 32 instruction memory slots
- Independent clock dividers
- TX/RX FIFOs for each state machine
- DMA capability

### Current Implementation Status

**What Works**:
- PIO device initialization
- State machine configuration
- Basic data transmission
- Clock configuration (200MHz system clock confirmed)

**Current Issues**:
1. **Wrong colors displayed**: Sending RED shows various colors (blue, green, mixed)
2. **Multiple pixels lighting**: When targeting one pixel, multiple light up
3. **Pattern inconsistency**: Colors vary by position in unpredictable ways
4. **Partial correctness**: Some pixels occasionally show correct color

## Technical Analysis of Current Problems

### Confirmed Facts from Testing

1. **System Clock**: 200MHz confirmed (`clock_get_hz(clk_sys)`)
2. **Clock Divider**: 25.00 for 800kHz operation (200MHz / 25 / 10 cycles = 800kHz)
3. **Data Format**: Using RGB order with 24-bit data shifted left by 8 bits
4. **PIO Configuration**: 
   - Shift direction: LEFT (MSB first)
   - Autopull: Enabled at 24-bit threshold
   - FIFO join: TX only

### Observed Behavior Pattern

When sending RED (255,0,0) to individual pixels:
```
Pixel 1: Blue
Pixel 2: Blue (two pixels lit)
Pixel 3: One blue, one green
Pixel 4: One blue, one red
Pixel 5: One blue
Pixel 6: One red, one green
Pixel 7: One green
Pixel 8: One red
Pixel 9: One yellow, one aquamarine
Pixel 10-12: Red (but wrong positions)
Pixel 13: One green
Pixel 14: One blue
Pixel 15: One red, one green
```

### Potential Root Causes Under Investigation

1. **Timing Mismatch**: The ws2812.pio program generates:
   - '0' bit: 375ns HIGH, 875ns LOW
   - '1' bit: 875ns HIGH, 375ns LOW
   
   But WS2811 expects:
   - '0' bit: 250ns HIGH, 1000ns LOW
   - '1' bit: 600ns HIGH, 650ns LOW

2. **FIFO/State Machine Synchronization**: Data may be transmitted before complete frame is loaded

3. **Bit Alignment Issues**: The 8-bit shift and 24-bit autopull threshold interaction

4. **Signal Integrity**: Level shifter (3.3V to 5V) with 0.1µF bypass capacitor

## Code Structure

### Key Components

**Headers Required**:
```c
#include "pico/stdlib.h"      // PIO compatibility layer
#include "hardware/pio.h"     // PIO API
#include "hardware/clocks.h"  // Clock functions
#include "ws2812.pio.h"      // PIO program for WS2812/WS2811
```

**Data Transmission**:
```c
// For 24-bit RGB mode with autopull at 24 bits
// PIO uses bits 31-8 of the 32-bit word
static inline void put_pixel(uint32_t pixel_rgb) {
    pio_sm_put_blocking(pio, sm, pixel_rgb << 8u);
}

// RGB color order for WS2811
static inline uint32_t urgb_u32(uint8_t r, uint8_t g, uint8_t b) {
    return ((uint32_t)(r) << 16) |  // R in bits 23-16
           ((uint32_t)(g) << 8) |    // G in bits 15-8
           (uint32_t)(b);             // B in bits 7-0
}
```

**Initialization**:
```c
ws2812_program_init(pio, sm, offset, gpio, 800000, false);  // false = RGB mode
```

## Next Steps for Debugging

### Immediate Tests Needed

1. **Verify WS2811 vs WS2812 Chips**: Confirm actual LED chip model
2. **Test with 400kHz timing**: Some WS2811 variants use slower speed
3. **Create custom PIO program**: Match exact WS2811 timing requirements
4. **Analyze with oscilloscope**: Verify actual signal timing
5. **Test with different data patterns**: Identify bit interpretation pattern

### Potential Solutions

1. **Custom WS2811 PIO Program**: Create new PIO assembly matching exact WS2811 timing
2. **Direct register manipulation**: Bypass piolib abstractions if needed
3. **Alternative GPIO approach**: Use different pins or PIO state machines
4. **Frame synchronization**: Ensure complete frames before transmission

## References and Resources

### Official Documentation
- WS2811 Datasheet: Search for "WS2811 datasheet PDF" (Worldsemi)
- Raspberry Pi RP1 Documentation: Limited public documentation available
- PIOlib Repository: https://github.com/raspberrypi/utils/tree/master/piolib

### Instructables WS2811 Reference
- https://www.instructables.com/Bitbanging-step-by-step-Arduino-control-of-WS2811-/
- Confirms RGB order and MSB-first transmission

### PIO Programming Resources
- Raspberry Pi Pico PIO Documentation: https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf (Chapter 3)
- PIO Assembly Language Reference: Part of RP2040 documentation

### Related Projects
- rpi_ws281x library (doesn't support Pi 5): https://github.com/jgarff/rpi_ws281x
- Nick Anderson's OctoWS2811 implementation (Teensy-based)

## Hardware Configuration

### Current Setup
- **Raspberry Pi 5** with RP1 I/O controller
- **GPIO Pin 10** (physical pin 19) for data output
- **Level Shifter**: 3.3V to 5V conversion
- **Power Supply**: 12V system with appropriate current capacity
- **Bypass Capacitor**: 0.1µF between VCC and GND
- **LED Configuration**: 25 test LEDs (will scale to 700)

### Wiring
```
Pi GPIO 10 (3.3V) → Level Shifter → 5V Data → WS2811 DIN
Pi GND → Level Shifter GND → LED GND → Power Supply GND
Power Supply 5V → LED VCC
```

## Performance Considerations

### Theoretical Performance
- **Data Rate**: 800kbps (800kHz × 1 bit)
- **Frame Time (700 LEDs)**: 700 × 24 bits / 800kbps = 21ms
- **Maximum FPS**: ~47 FPS theoretical

### PIO Advantages
- Near-zero CPU usage (DMA-driven)
- Consistent timing regardless of system load
- No Python GIL interference
- Independent of Linux scheduler

## Known Limitations

1. **piolib warning**: "Blocking operations block the whole RP1 firmware interface until they complete"
2. **Limited RP1 documentation**: Public information about RP1 PIO implementation is scarce
3. **No direct debugging**: Cannot easily probe PIO internal state

## Conclusion

The PIO approach remains the most promising solution for reliable WS2811 control on Raspberry Pi 5. The current implementation has timing and/or protocol issues that need resolution, but the fundamental approach is sound. Once the bit-level issues are resolved, this will provide a robust, high-performance solution for controlling the 700 LED mushroom installation.
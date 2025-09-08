# LED Flickering Issue - Comprehensive Analysis

## ✅ ISSUE RESOLVED

**Root Cause**: Simultaneous transmission on SPI0 and SPI1 caused signal interference on Raspberry Pi 5's RP1 I/O controller.

**Solution Applied**: 
- Serialized SPI transmission using shared lock (`_spi_transmission_lock` in `strip_controller.py`)
- Configured GPIO pins 10 and 20 for higher output amperage
- Maintained 800kHz SPI speed (no reduction needed)

**Result**: Stable operation at ~30 FPS with zero flickering across all 700 LEDs.

---

## Executive Summary

The Mushroom LED project experienced intermittent flickering on WS2811 LED strips when displaying colors other than pure white. This document consolidates all investigation findings, eliminated hypotheses, and the successful resolution.

**Key Diagnostic Finding**: Pure white (0xFF, 0xFF, 0xFF) displayed without flickering, while any color containing "0" bits flickered. This pointed to timing/signal integrity issues under concurrent SPI load.

## System Overview

### Hardware Configuration
- **Controller**: Raspberry Pi 5 with RP1 I/O controller (new architecture, different from Pi 1-4)
- **LEDs**: 700 total WS2811 pixels (12V system, GRB color order)
  - Cap exterior: 450 LEDs on SPI0 (GPIO 10, Pin 19, /dev/spidev0.0)
  - Stem interior: 250 LEDs on SPI1 (GPIO 20, Pin 38, /dev/spidev1.0)
- **Level Shifting**: 74AHCT125 buffer (3.3V → 5V conversion)
- **Power**: 12V system with external power supply
- **Test Setup**: Single 50 LED strip on external power (for isolated testing)

### Testing Configurations Attempted
1. **Direct Connection**: 3.3V GPIO output directly to LED data input (no level shifting)
2. **With Level Shifter**: Through 74AHCT125 buffer for 3.3V → 5V conversion
3. **Pending Test**: Adding capacitor to voltage stepper circuit for improved signal stability

### Software Architecture
- **Language**: Python 3.9+
- **LED Library**: Pi5Neo v1.0.6 (SPI-based, designed specifically for Pi 5)
- **Architecture**: Multi-threaded with double-buffering
  - Pattern generation thread (60 FPS target)
  - SPI transmission thread (parallel for each strip)
- **SPI Configuration**: 800kHz base rate (6.4MHz actual SPI clock after 8x encoding)

## The Flickering Problem

### Observed Behavior
1. **Random flickering** across LED strips during normal operation
2. **Pure white (0xFF, 0xFF, 0xFF) works perfectly** - no flickering whatsoever
3. **All other colors flicker** - including single channels (red, green, blue)
4. **Flickering occurs with both connection methods**:
   - Direct 3.3V connection from Pi GPIO to LED data input
   - Through 74AHCT125 level shifter (3.3V → 5V conversion)
   - Note: Waiting on capacitor installation for voltage stepper to test if this improves stability
5. **Multiple fix attempts** (7+ commits) have not resolved the issue
6. **Both SPI channels affected** when running full system

### Measured Data
- **SPI transmission time**: ~20ms for 450 LEDs, <1ms buffer preparation
- **Threading**: Double-buffering implementation verified in code
- **GPIO drive strength**: Increased to 16mA (high drive) via config.txt
- **Test patterns**: Flickering occurs with both solid colors and animations
- **Successful pattern**: Only pure white (0xFF, 0xFF, 0xFF) at full brightness displays without flickering

## Eliminated Hypotheses

### 1. ❌ Race Condition in Buffer Management
**Theory**: Pattern thread overwrites buffer while SPI thread transmits.

**Investigation**: 
- Reviewed `src/hardware/strip_controller.py` threading logic
- Buffer is properly copied to local variable before transmission
- Thread synchronization uses events correctly

**Conclusion**: Double-buffering is correctly implemented. No race condition exists.

### 2. ❌ Color Order Misconfiguration (RGB vs GRB)
**Theory**: Config specifies RGB but WS2811 expects GRB.

**Investigation**:
- Config shows `color_order: "RGB"`
- WS2811 typically uses GRB

**Why Eliminated**: Wrong color order would cause incorrect colors (e.g., red appearing as green), not random flickering.

### 3. ❌ Python GIL Interference
**Theory**: Global Interpreter Lock causes timing disruptions during SPI transmission.

**Investigation**:
- SPI transmission uses kernel-level DMA via `spidev`
- Once `xfer3()` is called, transmission is handled by kernel

**Conclusion**: GIL cannot interrupt kernel-level SPI operations. Timing is maintained by hardware.

### 4. ❌ Ground Bounce from Dual SPI
**Theory**: Simultaneous transmission on both SPI channels causes ground reference issues.

**Investigation**:
- Problem persists when testing single 50 LED strip
- Only one SPI channel active during isolated testing

**Conclusion**: Not related to dual-channel interference.

### 5. ❌ Insufficient WS2811 Latch Delay
**Theory**: 240μs latch delay too short for reliable operation.

**Investigation**:
- Current setting: 0.24ms (240μs)
- WS2811 specification: minimum 50μs
- Even WS2812B only requires 280μs

**Conclusion**: 240μs provides adequate margin above minimum specification.

### 6. ❌ LED Count Mismatch
**Theory**: Configured for 450 LEDs but testing with 50 causes framing issues.

**Investigation**:
- Extra data transmitted after 50th LED
- LEDs should ignore data after their position

**Why Eliminated**: LEDs ignore data after their position in the chain. The selective nature of the problem (white works, colors flicker) suggests this is not the cause.

### 7. ❌ Pi5Neo Library Fundamental Bug
**Theory**: Library has basic implementation errors.

**Investigation**:
- Library is actively maintained and tested
- Other users report successful operation with Pi 5
- Code review shows competent implementation

**Conclusion**: Library works for others with same hardware.

## Current Working Theories

### Theory 1: Dual Pi5Neo Instance Interference

**Unique Configuration**: 
The system creates **two separate Pi5Neo instances** simultaneously:
- Cap controller: Pi5Neo instance on `/dev/spidev0.0`
- Stem controller: Pi5Neo instance on `/dev/spidev1.0`

**Evidence**:
1. Flickering occurs even with single 50 LED test strip
2. Test still runs both Pi5Neo instances (one transmitting to unconnected SPI device)
3. Most Pi5Neo users run single instance for one strip
4. This dual-instance configuration is uncommon and untested

**Potential Issues**:
- Kernel SPI driver handling two simultaneous SPI streams
- RP1 I/O controller contention between SPI0 and SPI1
- Python threading with 4 threads (2 per controller) 
- Timing interference when both instances call `spi.xfer3()` near simultaneously

**Test Needed**: Run with truly single Pi5Neo instance (not just single physical strip)

### Theory 2: Marginal "0" Bit Timing

**Evidence Supporting This Theory**:
1. **White works perfectly** - contains only "1" bits (0xFF = 11111111)
2. **All colors with "0" bits flicker** - even single color channels
3. **Timing calculations reveal marginal conditions**:

```
Pi5Neo bit encoding at 6.4MHz SPI clock:
- "0" bit: 0xC0 (11000000) = 312.5ns high, 937.5ns low
- "1" bit: 0xF8 (11111000) = 781.25ns high, 468.75ns low

WS2812B specification:
- "0" bit: 400ns ±150ns high (250-550ns range)
- "1" bit: 800ns ±150ns high (650-950ns range)

Critical observation: 312.5ns is only 62.5ns above the absolute minimum (250ns)
```

**Why This Causes Flickering**:
- Marginal timing becomes unreliable with signal degradation
- RP1 I/O controller may have different rise/fall characteristics than BCM2835
- Cable capacitance and LED input thresholds reduce margin further
- "0" bits occasionally read as "1" bits, causing color corruption

**Uncertainty**: Why doesn't this affect all Pi5Neo users? Possible factors:
- LED batch variations in input thresholds
- Cable length and quality differences
- Power supply stability variations
- Environmental factors (temperature, EMI)

### Theory 3: SPI Clock Frequency Rounding

**Observation**: 
Pi5Neo calculates SPI frequency as `spi_speed_khz * 1024 * 8` instead of `* 1000 * 8`.

**Impact**:
- Requested: 6,553,600 Hz (6.5536 MHz)
- Pi must choose from available divisors of core clock
- Actual frequency might be 7.8125 MHz (too fast) or 3.90625 MHz (too slow)

**Why This Could Cause Issues**:
- If running too fast, timing violations accumulate
- If running too slow, might interact poorly with LED internal timing

**Uncertainty**: Need to measure actual SPI clock frequency to confirm.

## Important Discoveries

### 1. Pi5Neo Implementation Details
Located in `pi5neo/pi5neo.py`:
- Uses `spidev` library for hardware SPI
- Bit-banging done in software, then sent as SPI bytes
- Single internal buffer (not double-buffered within library)
- Blocking transmission via `xfer3()` call

### 2. Thread Architecture Insights
From `src/hardware/strip_controller.py`:
- Proper producer-consumer pattern with events
- Separate threads for pattern generation and SPI transmission
- Performance metrics show expected timing (~20ms for 450 LEDs)

### 3. Configuration Observations
From `config/led_config.yaml`:
- Dual SPI configuration unique (most users have single strip)
- Hardware PWM not used (avoiding known audio conflicts)
- 5-minute metric window might hide intermittent issues

## Recommended Solutions

### Solution 1: Reduce SPI Speed
```yaml
# config/led_config.yaml
hardware:
  spi_speed_khz: 640  # Reduced from 800
```
**Rationale**: Increases "0" bit high time from 312.5ns to 390ns, providing larger margin above 250ns minimum.

### Solution 2: Modify Pi5Neo Bit Encoding
Fork library and change "0" bit pattern:
```python
def byte_to_bitstream(self, byte):
    bitstream = [0xE0] * 8  # Changed from 0xC0
    # 0xE0 = 11100000 gives 468ns high time
```
**Rationale**: Provides much larger timing margin for "0" bits.

### Solution 3: Progressive Speed Testing
Start very slow and increase gradually:
```yaml
spi_speed_khz: 400  # Start here
# Test, then try: 450, 500, 550, 600, 640, 680, 720, 760
```
**Rationale**: Find maximum stable speed for specific hardware combination.

## Testing Methodology

### Recommended Test Procedure
1. **Baseline Test**: Confirm white still works without flickering
2. **Single Color Channels**: Test pure red (0xFF, 0x00, 0x00), green, blue
3. **Gray Levels**: Test 0x80, 0x80, 0x80 (50% gray - many "0" bits)
4. **Speed Reduction**: Start with 640kHz, test all colors
5. **Document Results**: Note which speeds work with which patterns

### Diagnostic Metrics to Monitor
- Frame rate (should maintain 30+ FPS)
- SPI transmission time (should scale linearly with speed change)
- Error counts (should remain zero)
- CPU usage (should stay under 30%)

## Open Questions

1. **Why does Pi5Neo work for others but not this setup?**
   - LED manufacturer differences?
   - Specific RP1 chip variations?
   - Environmental factors?

2. **What is the actual SPI clock frequency being used?**
   - Need oscilloscope to measure
   - Could use logic analyzer to verify bit timing

3. **Are these actually WS2811 or WS2812B chips?**
   - Vendors often mislabel
   - Different chips have different timing requirements

4. **Would kernel-level debugging reveal more?**
   - SPI driver debug output might show actual frequencies
   - DMA transfer patterns could be relevant

## Future Investigation Paths

1. **Hardware Analysis**
   - Oscilloscope measurement of actual bit timing
   - Logic analyzer capture of full frame transmission
   - Signal integrity testing with different cable lengths

2. **Software Experiments**
   - Custom test pattern with controllable "0" bit density
   - Single-threaded version to eliminate threading variables
   - Direct register manipulation bypassing Pi5Neo

3. **Comparative Testing**
   - Test same code on Raspberry Pi 4
   - Test different LED strips with same controller
   - Test different Pi5Neo versions

## Conclusion

Claude's suspicion is that the flickering issue is almost certainly related to marginal "0" bit timing in the WS2811 protocol implementation. The fact that pure white (all "1" bits) works perfectly while any pattern containing "0" bits flickers strongly supports this hypothesis. Claude's next recommendation is to take immediate action is to reduce SPI speed to 640kHz or lower, which should provide adequate timing margin for reliable operation. If this fails, progressively more invasive solutions (library modification, hardware changes) could be attempted.

This document will be updated as new information becomes available or additional testing is completed.
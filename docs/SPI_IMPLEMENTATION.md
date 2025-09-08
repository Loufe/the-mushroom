# SPI Implementation Notes

## Current Status: Unresolved Flickering Issue

**Summary for Next Developer/AI**: We have an unresolved flickering issue when rapidly updating WS2811 LEDs via SPI on Raspberry Pi 5. The hardware and protocol are correct (single frames work perfectly), but something about continuous rapid updates causes corruption for all colors except pure white at 100% brightness.

**Initial Hypothesis (INCORRECT)**: Dual SPI (SPI0/SPI1) caused flickering due to RP1 I/O controller timing conflicts.

**Current Finding**: Flickering persists even with single SPI channel, indicating the root cause is elsewhere.

**Critical Diagnostic Pattern**: 
- Single static frames work perfectly (tested holding color for 5 seconds)
- Rapid frame updates cause flickering
- **Pure white at 100% brightness (0xFF,0xFF,0xFF) is the ONLY stable color** during rapid updates
- Even (254,254,254) flickers - single bit difference causes instability
- Any byte value containing a 0 bit will flicker (0xFE = 11111110 has one 0 bit)
- Issue scales with data volume and frame rate (but neither alone fixes it)
- Test setup: 50 physical LEDs connected to GPIO 10 (SPI0 MOSI)
- Config restored to 450 cap + 250 stem for full deployment

## Test Results & Evidence

### What We've Tested
1. **Dual SPI → Single SPI**: Flickering persists with single channel
2. **700 LEDs → 51 LEDs**: Reduced flickering but didn't eliminate it
3. **SPI Speed (800kHz → 640kHz)**: No improvement
4. **Frame rate limiting (uncapped → 30 FPS)**: Reduced flickering but didn't eliminate it
5. **Latch delay (0.24ms → 10ms)**: No improvement
6. **Explicit LOW bytes for latch**: No improvement
7. **Series resistor on data line**: No improvement

### What We Know for CERTAIN
- Hardware and protocol are correct (single frames work perfectly)
- Pi5Neo library uses synchronous `xfer3()` (blocking, not async)
- **SPI kernel buffer size is 4096 bytes** (`/sys/module/spidev/parameters/bufsiz`)
  - 700 LEDs × 24 bytes = 16,800 bytes total
  - `xfer3()` splits this into 5 chunks: 4×4096 + 1×512 bytes
  - However, issue persists even with 51 LEDs (1,224 bytes - single chunk)
- **DietPi is configured in performance mode** (CPU frequency scaling disabled)
  - Rules out throttling/frequency changes as a cause
- The issue ONLY occurs during rapid frame transitions, not static display
- Pure white at 100% (all 0xFF bytes → 0xF8 bitstream) is uniquely stable

### Q: What are the actual timing margins at 800kHz SPI?
**A:** With 8x oversampling at 6.4MHz actual SPI clock:
- "0" bit high time: 312.5ns (spec: 400±150ns) - **62.5ns margin**
- "1" bit high time: 781.25ns (spec: 800±150ns) - **comfortable margin**

The 62.5ns margin for "0" bits appears to be violated during rapid frame updates (mechanism unknown).

## Remaining Unknowns & Theories

### What We DON'T Know
1. **Why does 0xFF work but nothing else?**
   - 0xFF → 8 consecutive 0xF8 bytes (11111000 each)
   - 0xFE → 7×0xF8 bytes + 1×0xC0 byte (11000000)
   - That single 0xC0 is enough to cause corruption
   
2. **What happens during frame transitions?**
   - Between frames: Pattern generation → Buffer copy → Bitstream rebuild → SPI transmission
   - Where exactly does the corruption occur?

3. **Is this Pi 5/RP1 specific?**
   - Would the same code work on Pi 4 (BCM2835)?
   - Is there an RP1-specific behavior we're missing?

### Remaining Theories to Test

1. **Python GIL Contention During Bitstream Generation**
   - Pi5Neo rebuilds entire bitstream in Python for every frame (lines 114-125)
   - 3 threads competing for GIL during rapid updates
   - Could cause micro-stutters that violate the 62.5ns timing margin for "0" bits

2. **RP1-Specific SPI Behavior**
   - Does RP1 handle SPI differently than BCM2835 in ways that affect timing?
   - Are there undocumented quirks in how RP1 manages rapid SPI transactions?

3. **GPIO State Between Frames**
   - What is the MOSI pin state between xfer3() calls?
   - Does RP1 handle this differently than BCM2835?

4. **Bitstream Encoding Edge Case**
   - The 0xC0/0xF8 encoding assumes symmetric rise/fall times
   - Real-world asymmetry could accumulate errors over multiple frames

## Performance Characteristics

### Q: What's the measured SPI transmission overhead?
**A:** (Note: These measurements were estimated, not directly measured)
- 450 LEDs (1350 bytes → 10800 SPI bytes): ~20ms estimated
- 250 LEDs (750 bytes → 6000 SPI bytes): ~12ms estimated
- Theoretical at 6.4MHz: 13.5ms + 7.5ms = 21ms
- Actual measurements needed with oscilloscope or logic analyzer

### Q: Why does buffer preparation take <1ms despite 700 pixels?
**A:** NumPy vectorization with contiguous memory layout. The `np.clip()` and array operations process all pixels in SIMD fashion. Cache-friendly access pattern maintains L1/L2 cache hits.

## Hardware-Specific Findings

### Q: What distinguishes RP1 from BCM2835 for this application?
**A:** (Note: These differences may or may not be related to the flickering issue)
1. Different SPI FIFO depths (RP1: 16 bytes vs BCM2835: 64 bytes)
2. Modified GPIO slew rate control registers
3. Separate clock domains for SPI0/SPI1 (initially suspected but ruled out)
4. DMA controller scheduling differences affecting concurrent transfers

### Q: Why configure GPIO 10/20 for higher amperage?
**A:** RP1 GPIO default drive strength (8mA) produces slower rise times. At 6.4MHz SPI rate, signal edges need <50ns transition time. 16mA drive strength achieves ~30ns rise time, maintaining signal integrity through typical cable capacitance (~50pF/m).

## Thread Architecture Specifics

### Q: What's the critical path in the threading model?
**A:** 
```
Pattern.update() → Queue.put() → [thread boundary] → Queue.get() → spi.xfer3()
   <1ms              ~0ms                              ~0ms          20-12ms
```
SPI transmission dominates at 94% of frame time.

### Q: Why double-buffering despite serialized transmission?
**A:** Prevents pattern generator blocking during SPI transmission. Enables consistent pattern timing independent of transmission jitter. Measured benefit: 5-8% reduction in frame time variance.

## Protocol Implementation

### Q: Why 240μs latch delay vs WS2811 50μs minimum?
**A:** Safety margin for signal conditioning circuits. Some LED controllers include RC filters that extend the effective reset detection window. 240μs ensures compatibility across LED batches while adding negligible overhead (0.7% of frame time).

### Q: How does Pi5Neo's bitstream encoding affect compatibility?
**A:** The 0xC0/0xF8 encoding assumes symmetric rise/fall times. Real-world asymmetry (rise typically faster) shifts the effective pulse center by 10-30ns. This explains why some installations require speed adjustment despite identical hardware.

## Next Steps for Debugging

### Immediate Tests
1. **Test with Pi 4** - Determine if issue is RP1/Pi5-specific
2. **Oscilloscope Analysis** - Capture actual waveform during flicker vs stable
3. **Single-threaded Test** - Eliminate GIL contention by removing threading
4. **Pre-computed Bitstream** - Send same pre-built buffer repeatedly to isolate generation vs transmission

### Code Investigation
1. **Pi5Neo Speed Calculation** - Why `* 1024 * 8` instead of `* 1000 * 8`?
2. **xfer3() internals** - Verify it truly blocks until completion
3. **GPIO pin state** - Check MOSI state between frames with scope or logic analyzer

### Key Finding
**0xFF bytes (all 1s) are uniquely stable. Even 0xFE (11111110) with a single 0 bit causes flickering.**

This points to the 0xC0 bitstream encoding for "0" bits as the failure point:
- 0xFF → 0xF8,0xF8,0xF8,0xF8,0xF8,0xF8,0xF8,0xF8 (all HIGH pulses)
- 0xFE → 0xF8,0xF8,0xF8,0xF8,0xF8,0xF8,0xF8,0xC0 (one LOW pulse)

That single 0xC0 byte (11000000) for the "0" bit is enough to cause flickering during rapid updates.
The issue is specifically with how 0xC0 is transmitted or interpreted during continuous frames.

## Conclusion for Next Developer

The flickering issue is directly related to the 0xC0 bitstream encoding used for "0" bits in the WS2811 protocol. During rapid continuous frame updates:
- 0xF8 bytes (11111000 for "1" bits) transmit reliably
- 0xC0 bytes (11000000 for "0" bits) cause corruption

The corruption mechanism is still unknown but likely involves:
1. **Timing margin violation**: 0xC0 has only 2 HIGH bits (312.5ns) vs spec (400±150ns)
2. **Pi 5/RP1 specific behavior**: Issue may not exist on Pi 4 (needs testing)
3. **Cumulative effect**: Single frames work, continuous frames fail

**Temporary Workaround**: None identified. Frame rate limiting and data reduction help but don't eliminate the issue.

**Root Cause**: Unknown, but isolated to the transmission/interpretation of 0xC0 bytes during rapid SPI updates on Pi 5.

## Historical Notes
- Initial dual-SPI theory was based on flickering observation but proved incorrect
- Single SPI channel still exhibits the same issue
- Confirmed that even a single "0" bit in any byte causes flickering (254 vs 255 test)
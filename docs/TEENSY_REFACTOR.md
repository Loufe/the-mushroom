# Teensy + OctoWS2811 LED Controller Refactor

## Current Situation Summary

### The Problem
- **Pi 5 + Pi5Neo + SPI = Flickering** for all colors except pure white (0xFF,0xFF,0xFF)
- Root cause: 0xC0 bitstream encoding for "0" bits violates WS2811 timing specs by ~62ns
- Issue is Pi 5/RP1 specific - the new I/O controller can't maintain timing during rapid SPI updates
- 30+ hours debugging proved this is unsolvable in Python on Pi 5

### What We've Proven
- ✅ Single static frames work perfectly (hardware is correct)
- ❌ Rapid continuous updates fail (timing violation during updates)
- ❌ Pre-built buffers still flicker (not Python overhead)
- ❌ Level shifter installed but doesn't help (timing, not voltage issue)
- ❌ Reduced to 50 LEDs still flickers (not a data volume issue)

## New Architecture: Pi 5 + Teensy + OctoWS2811

### Overview
```
┌─────────────────┐      USB Serial      ┌──────────────────┐
│                 │       2Mbps            │                  │──► Cap (450 LEDs)
│   Raspberry     │  ──────────────────►  │  Teensy 4.0/4.1  │
│     Pi 5        │    Raw RGB Data       │  + OctoWS2811    │──► Stem (250 LEDs)
│                 │                        │                  │
│  - All Logic    │                        │  - ONLY Output   │
│  - Patterns     │                        │  - DMA Transfer  │
│  - Audio        │                        │  - Near 0% CPU   │
└─────────────────┘                        └──────────────────┘
```

### Division of Responsibilities

**Raspberry Pi 5 (100% of intelligence):**
- Pattern generation (Python, numpy)
- Audio processing and reactive patterns
- Network/web interface
- Configuration management
- All control logic and decision making

**Teensy (dumb pixel pusher only):**
- Receives raw RGB data via USB serial
- Outputs to LEDs using OctoWS2811 DMA
- No pattern logic whatsoever
- No failsafe patterns
- No audio processing

## Why OctoWS2811 Instead of FastLED

- **DMA-based**: Near-zero CPU usage vs FastLED's CPU-intensive bit-banging
- **Non-blocking**: Can receive next frame while outputting current frame
- **Performance**: 450 LEDs updates in ~1.7ms, 250 in ~0.95ms
- **Teensy 4.x optimized**: Can use any pins, flexible configuration
- **Hardware acceleration**: Uses Teensy's crossbar switch and dual-bus RAM

## Implementation Plan

### Phase 1: Basic Communication
1. Test both Teensy 4.0 and 4.1 (one may be broken)
2. OctoWS2811 sketch for 2 strips (450 cap, 250 stem)
3. Simple serial protocol for raw RGB data
4. Python serial sender on Pi 5
5. Verify no flickering with test colors

### Phase 2: Integration
1. Adapt LEDController to send via serial instead of SPI
2. Existing patterns work unchanged (they just generate numpy arrays)
3. Test performance and latency

### Phase 3: Optimization (if needed)
1. Implement basic frame sync if tearing occurs
2. Add brightness control command
3. Monitor for dropped frames

## Technical Specifications

### Hardware Configuration
- **LEDs**: 700 total (450 cap + 250 stem)
- **Teensy Pins**: 
  - Pin 2: Cap LEDs data (450 pixels)
  - Pin 14: Stem LEDs data (250 pixels)
  - Or single pin if keeping series connection
- **Power**: Existing 12V system unchanged

### Serial Protocol Design

#### Frame Format
```
[HEADER][COMMAND][DATA][CHECKSUM]

HEADER: 0xFF 0xFE (2 bytes) - Frame start marker
COMMAND: 1 byte
  0x01 = Full frame update
  0x02 = Brightness change
  0x03 = Clear all
  0x04 = Test pattern
DATA: Variable length
  For frame: [CAP_COUNT_HI][CAP_COUNT_LO][CAP_DATA][STEM_COUNT_HI][STEM_COUNT_LO][STEM_DATA]
CHECKSUM: 1 byte XOR of all data bytes
```

#### Timing Requirements
- Serial baud: 2,000,000 (2Mbps) or 115,200 for testing
- Frame size: 700 * 3 = 2,100 bytes
- Transmission time at 2Mbps: ~10.5ms
- Target: 30 FPS minimum, 60 FPS ideal

### Implementation Requirements

**Teensy Sketch:**
- OctoWS2811 library configured for 2 strips (450 and 250 LEDs)
- 2Mbps USB serial reception
- Frame marker detection and buffering
- DMA-based non-blocking output

**Python Side:**
- Serial transmission at 2Mbps
- Direct numpy array to bytes conversion
- Frame markers for sync
- Drop-in replacement for current SPI output

## Migration Checklist

### Setup Phase
- [ ] Install Arduino IDE with Teensyduino
- [ ] Install OctoWS2811 library
- [ ] Test both Teensy 4.0 and 4.1 boards
- [ ] Verify OctoWS2811 adapter connections

### Development Phase  
- [ ] Create minimal Teensy test sketch (solid colors)
- [ ] Verify both strips work independently
- [ ] Implement serial frame reception
- [ ] Create Python test sender script
- [ ] Verify frame sync and no tearing

### Integration Phase
- [ ] Create TeensyLEDController class
- [ ] Modify LEDController to use serial backend
- [ ] Test existing patterns unchanged
- [ ] Measure actual FPS and latency
- [ ] Add reconnection handling

### Deployment Phase
- [ ] Update run.sh for Teensy detection
- [ ] Update systemd service
- [ ] Document wiring and setup
- [ ] Test full system integration

## Performance Expectations

| Metric | Current (Pi5+SPI) | Expected (Teensy+OctoWS2811) |
|--------|------------------|------------------------------|
| Frame Rate | ~30 FPS (flickering) | 70+ FPS stable |
| CPU Usage (Pi) | ~30% | ~5% (pattern generation only) |
| CPU Usage (Teensy) | N/A | <1% (DMA driven) |
| Latency | <1ms | ~15ms (serial + output) |
| Reliability | Flickering | Rock solid |

## Testing Priority

1. **Proof of concept**: Single solid color via serial
2. **Two strips**: Verify independent control
3. **Frame sync**: Ensure no tearing at high FPS
4. **Pattern test**: Rainbow pattern from Pi
5. **Stress test**: Maximum frame rate test

## Open Questions

- Pin assignment for 2 strips on OctoWS2811 adapter?
- Need level shifter between Teensy and LEDs?
- USB cable length limitations at 2Mbps?

## References

- [OctoWS2811 Documentation](https://www.pjrc.com/teensy/td_libs_OctoWS2811.html)
- [OctoWS2811 GitHub](https://github.com/PaulStoffregen/OctoWS2811)
- [Teensy 4.0 Pinout](https://www.pjrc.com/teensy/pinout.html)
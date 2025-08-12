# Hardware Configuration

## Physical Dimensions
- **Cap:** 14ft diameter, angled top (higher at center/entrance)
- **Stem:** 6ft wide, 7ft tall
- **Total Height:** ~14ft from ground to cap top
- **Interior:** Hollow with round door, seating for 2

## LED Strip Setup
- **Total LEDs:** 700 WS2811
- **Current format:** 14 strips of 50 LEDs
- **Proposed configuration:** 2x 150 LEDs + 2x 200 LEDs
- **Level Shifter:** 1x 74HCT125 (4 channels available)
- **Power:** Injection handled separately by user

### GPIO Pin Allocation
The 74HCT125 provides 4 independent level-shifted channels:
- **Channel 1:** GPIO 10 (SPI MOSI) - Strip 1 (200 LEDs) - Cap primary
- **Channel 2:** GPIO 12 (PWM0) - Strip 2 (200 LEDs) - Cap secondary
- **Channel 3:** GPIO 18 (PWM0) - Strip 3 (150 LEDs) - Stem upper
- **Channel 4:** GPIO 21 (PWM1) - Strip 4 (150 LEDs) - Stem lower

**Note:** Pi 5 requires GPIO 10, 12, 18, or 21 for NeoPixels. Using SPI on GPIO 10 for best performance.

## Audio Configuration
- **Hardware:** 1x AU-MMSA USB adapter
- **Placement:** Inside mushroom (primary)
- **Target:** Human voice reactivity
- **Sampling:** 44.1kHz, 16-bit, mono
- **Buffer:** 64 samples (low latency)

## Performance Targets
- **Frame Rate:** 30 FPS minimum, optimize for higher
- **Audio Latency:** < 10ms total system latency
- **CPU Target:** < 50% utilization leaving headroom

## Development Hardware
- **Platform:** Raspberry Pi 5
- **OS:** DietPi (fresh install pending)
- **Cooling:** Active cooling required
- **Network:** Development only (not required for production)
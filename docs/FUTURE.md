# Future Development

## Audio-Reactive Features

### Hardware
- **USB Adapter**: AU-MMSA (confirmed working with Pi 5, no drivers needed)
- **Specs**: 16-bit/48kHz input, built-in bias voltage for electret mics

### Implementation Context
- **Library**: `python-sounddevice` (better buffer handling than PyAudio)
- **Config**: 64-sample buffers at 44.1kHz, callback mode
- **Expected**: 4-6ms latency, 5-10% CPU usage

### Notes
- USB audio avoids GPIO complexity (would need signal conditioning)
- Compatible with existing SPI LED control
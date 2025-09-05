# Development Guide

## Architecture Overview

### System Components
```
the-mushroom/
├── main.py                  # Entry point, pattern management
├── src/
│   ├── hardware/
│   │   └── led_controller.py  # Dual SPI abstraction layer
│   ├── patterns/
│   │   ├── base.py          # Abstract pattern class
│   │   ├── registry.py      # Auto-registration system
│   │   └── *.py             # Pattern implementations
│   └── effects/
│       └── colors.py        # Color utilities and palettes
├── config/                  # YAML configurations
├── tests/                   # Hardware validation
└── scripts/                 # Operational utilities
```

### Key Design Decisions
- **Pi5Neo over CircuitPython**: Better Pi 5 compatibility, handles 700 LEDs
- **Dual SPI channels**: Parallel updates, independent zone control
- **Pattern registry**: Auto-discovery via decorators
- **YAML configs**: Runtime adjustments without code changes

## Creating New Patterns

### 1. Basic Pattern Template

```python
# src/patterns/mypattern.py
from .base import Pattern
from .registry import PatternRegistry
import numpy as np

@PatternRegistry.register("my_pattern")
class MyPattern(Pattern):
    def get_default_params(self):
        return {
            'speed': 1.0,
            'color': (255, 0, 0)
        }
    
    def update(self, delta_time):
        # Your pattern logic here
        # Modify self.pixels (numpy array of shape [led_count, 3])
        self.pixels[:] = self.params['color']
        return self.pixels
```

### 2. Register in __init__.py

```python
# src/patterns/__init__.py
from . import mypattern  # Add this line
```

The pattern auto-registers and appears in `--pattern` options.

### 3. Pattern Best Practices

- **Use numpy operations** for performance (vectorized > loops)
- **Respect frame timing** via delta_time parameter
- **Parameter validation** in set_param() method
- **Test with reduced LEDs** first: `--count 10`

### Available Base Methods
- `get_time()`: Time since pattern started
- `reset()`: Reset to initial state  
- `set_param(name, value)`: Runtime adjustment
- `render()`: Called by main loop (handles timing)

## Hardware Abstraction

### LED Controller
The `LEDController` manages both SPI channels as one logical display:

```python
controller = LEDController("config/led_config.yaml")
controller.set_pixels(pixel_array)  # 700x3 numpy array
controller.present()                # Push to hardware

# Zone-specific updates (atomic - both updated before present)
controller.set_stem_pixels(stem_array)  # 250 LEDs
controller.set_cap_pixels(cap_array)    # 450 LEDs  
controller.present()                    # Push both zones to hardware
```

### Configuration Files

**led_config.yaml**: Hardware definitions
```yaml
strips:
  - id: stem_interior
    spi_device: "/dev/spidev1.0"
    led_count: 250
  - id: cap_exterior  
    spi_device: "/dev/spidev0.0"
    led_count: 450
```

**startup.yaml**: Boot settings
```yaml
pattern: rainbow_wave
brightness: 128
pattern_params:
  rainbow_wave:
    wave_length: 100
    speed: 50.0
```

## Testing & Debugging

### Hardware Validation
```bash
# Test individual strips
sudo mushroom-env/bin/python tests/test_spi.py --mode stem --count 10
sudo mushroom-env/bin/python tests/test_spi.py --mode cap --count 10

# Test dual simultaneous
sudo mushroom-env/bin/python tests/test_spi.py --mode dual

# Full system test
sudo mushroom-env/bin/python tests/test_spi.py --mode both
```

### Pattern Testing
```bash
# Test specific pattern with low brightness
./run.sh --pattern my_pattern --brightness 32

# Monitor performance
htop  # In another terminal
vcgencmd measure_temp
```

### Debug Logging
```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"Pattern params: {self.params}")
```

## Development Environment

### Recommended Setup
- **IDE**: VS Code with Remote-SSH extension
- **Connection**: SSH directly to Pi
- **Virtual Env**: Always activate before testing
- **Testing**: Use reduced LED counts during development

### Performance Optimization
- Target 30 FPS minimum, 60 FPS target with all 700 LEDs
- Keep CPU usage under 30%
- Monitor temperature (should stay under 60°C with cooling)
- Use numpy vectorization over Python loops
- Profile with `cProfile` if needed

## Future Development Areas

### Planned Features
- Audio-reactive patterns via USB microphone
- 3D coordinate mapping for spatial effects  
- Web interface for remote control
- Motion sensor integration
- BPM synchronization

### Adding Audio Support
The AU-MMSA USB adapter is supported. Use `python-sounddevice`:
```python
import sounddevice as sd
# 44.1kHz, 64-sample buffer for low latency
```

### Coordinate Mapping
Future feature: 3D coordinate mapping for spatial effects. Will require measuring physical LED positions and implementing coordinate-based patterns.
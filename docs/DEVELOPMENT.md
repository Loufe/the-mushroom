# Development Guide

## Architecture Overview

### System Components
```
the-mushroom/
├── main.py                     # Entry point, health monitoring
├── src/
│   ├── hardware/
│   │   ├── led_controller.py  # Dual strip manager
│   │   └── strip_controller.py # Per-strip threading
│   ├── patterns/
│   │   ├── base.py            # Abstract pattern class
│   │   ├── registry.py        # Auto-registration
│   │   └── *.py               # Pattern implementations
│   └── effects/
│       └── colors.py          # Color utilities
├── config/                     # YAML configurations
└── tests/                      # Hardware validation
```

### Architecture
- **Parallel Threading**: Separate pattern generation and SPI transmission threads per strip
- **Double Buffering**: Pattern threads generate while SPI threads transmit
- **Independent Control**: Cap (450 LEDs) and stem (250 LEDs) run different patterns
- **Health Monitoring**: Main thread monitors thread health and performance

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
- **Keep patterns simple** - complexity can cause frame drops

### Available Base Methods
- `get_time()`: Time since pattern started
- `reset()`: Reset to initial state
- `render()`: Called by main loop (handles timing)

## Hardware Abstraction

### Controller API

```python
controller = LEDController("config/led_config.yaml")

# Set patterns (before starting)
controller.set_cap_pattern(cap_pattern)    # 450 LED pattern
controller.set_stem_pattern(stem_pattern)  # 250 LED pattern

# Start threading system
controller.start()

# Monitor health
health = controller.get_health()
stats = controller.get_stats()
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
cap_pattern: rainbow
stem_pattern: rainbow
brightness: 128
```

## Testing & Debugging

### Hardware Validation
```bash
# Full hardware test
sudo mushroom-env/bin/python tests/test_spi.py
```

### Pattern Testing
```bash
# Test with different patterns on cap/stem
./run.sh --cap-pattern rainbow --stem-pattern test --brightness 32

# Same pattern on both
./run.sh --pattern rainbow --brightness 32

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
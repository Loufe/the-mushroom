# Pattern Development Guide

## Creating a New Pattern

1. Create a new file in `src/patterns/` (e.g., `fire.py`)
2. Import the required modules and decorator:
```python
from .base import Pattern
from .registry import PatternRegistry
```

3. Use the decorator to register your pattern:
```python
@PatternRegistry.register("fire")
class FirePattern(Pattern):
    # Your implementation
```

4. Add import in `src/patterns/__init__.py`:
```python
from . import fire
```

## Pattern Registry Benefits

- **Auto-discovery**: Patterns register themselves when imported
- **No hardcoding**: Main.py dynamically gets available patterns
- **Easy testing**: Add/remove patterns without touching main code
- **Clean separation**: Pattern logic isolated from application logic

## Available Base Methods

- `get_default_params()`: Define configurable parameters
- `update(delta_time)`: Called each frame to generate colors
- `get_time()`: Time since pattern started
- `reset()`: Reset pattern to initial state
- `set_param(name, value)`: Runtime parameter adjustment
# Pattern modules
from .base import Pattern
from .registry import PatternRegistry

# Import all pattern modules to trigger registration
# The decorators will automatically register them
from . import test
from . import rainbow
from . import wisps

# Export the registry and base class for external use
__all__ = ['Pattern', 'PatternRegistry']